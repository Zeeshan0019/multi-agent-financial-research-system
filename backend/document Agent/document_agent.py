
from __future__ import annotations

import io
import re
import os
import uuid
import shutil
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import fitz
from PIL import Image

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document as LCDocument

logger = logging.getLogger("document_agent")
logging.basicConfig(level=logging.INFO)

try:
    import pytesseract
    _env_path = os.environ.get("TESSERACT_CMD")
    _common_windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\Tesseract-OCR\tesseract.exe"),
    ]

    if _env_path and os.path.exists(_env_path):
        pytesseract.pytesseract.tesseract_cmd = _env_path
    elif os.name == "nt":
        for _path in _common_windows_paths:
            if os.path.exists(_path):
                pytesseract.pytesseract.tesseract_cmd = _path
                break

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract not installed — OCR fallback for scanned PDFs is disabled.")


class DocumentAgentConfig:
    """Central place for tunables so they aren't scattered as magic numbers."""

    CHUNK_SIZE = 1000             
    CHUNK_OVERLAP = 150          
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_STORE_ROOT = Path("./vector_store")
    UPLOAD_ROOT = Path("./uploads")

    MIN_CHARS_PER_PAGE_BEFORE_OCR = 30
    OCR_DPI = 300
    OCR_LANG = "eng"

@dataclass
class PageText:
    page_number: int        
    text: str
    source: str = "text_layer" 


@dataclass
class DocumentMetadata:
    document_id: str
    user_id: str
    company_name: str
    file_name: str
    upload_timestamp: str
    page_count: int
    ocr_page_count: int = 0
    chunk_count: int = 0
    status: str = "processing" 
    error: Optional[str] = None


@dataclass
class ProcessResult:
    document: DocumentMetadata
    chunks_indexed: int
    warnings: List[str] = field(default_factory=list)

class DocumentAgent:
   
    def __init__(self, config: DocumentAgentConfig = DocumentAgentConfig()):
        self.config = config
        self.config.VECTOR_STORE_ROOT.mkdir(parents=True, exist_ok=True)
        self.config.UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        # Lazy-load embeddings — don't block server startup
        self._embeddings = None

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.config.EMBEDDING_MODEL,
                model_kwargs={"local_files_only": True}
            )
        return self._embeddings

    def process_document(
        self,
        file_path: str,
        document_id: str,
        user_id: str,
        company_name: str = "Unknown",
    ) -> ProcessResult:
        """Full pipeline: PDF (+ OCR fallback) -> chunks -> embeddings -> FAISS."""
        warnings: List[str] = []
        file_name = Path(file_path).name

        pages = self._extract_pages(file_path, warnings)
        ocr_page_count = sum(1 for p in pages if p.source == "ocr")
        empty_page_count = sum(1 for p in pages if p.source == "empty")

        if empty_page_count:
            warnings.append(
                f"{empty_page_count} page(s) produced no text even after OCR "
                "(likely blank pages or unreadable images)."
            )
        if ocr_page_count:
            warnings.append(
                f"{ocr_page_count} page(s) had no text layer and were "
                "processed with OCR instead — double-check those pages for "
                "extraction accuracy, especially numbers in tables."
            )

        metadata = DocumentMetadata(
            document_id=document_id,
            user_id=user_id,
            company_name=company_name,
            file_name=file_name,
            upload_timestamp=datetime.now(timezone.utc).isoformat(),
            page_count=len(pages),
            ocr_page_count=ocr_page_count,
        )

        try:
            lc_documents = self._build_langchain_documents(pages, metadata)
            chunks = self.splitter.split_documents(lc_documents)

            if not chunks:
                raise ValueError("No text chunks were produced from this document.")

            self._index_chunks(chunks, document_id)

            metadata.chunk_count = len(chunks)
            metadata.status = "indexed"
            logger.info(
                "Indexed document %s (%s): %d pages (%d via OCR) -> %d chunks",
                document_id, file_name, len(pages), ocr_page_count, len(chunks),
            )

        except Exception as exc:
            metadata.status = "failed"
            metadata.error = str(exc)
            logger.exception("Failed to process document %s", file_name)
            return ProcessResult(document=metadata, chunks_indexed=0, warnings=warnings)

        return ProcessResult(document=metadata, chunks_indexed=metadata.chunk_count, warnings=warnings)

    def search(
        self,
        document_id: str,
        query: str,
        k: int = 5,
        company_filter: Optional[str] = None,
    ) -> List[dict]:
        """Top-k most relevant chunks for a query, scoped to a document."""
        vector_store = self._load_document_index(document_id)
        if vector_store is None:
            return []

        results = vector_store.similarity_search_with_score(query, k=k)

        hits = []
        for doc, score in results:
            if company_filter and doc.metadata.get("company_name") != company_filter:
                continue
            hits.append(
                {
                    "text": doc.page_content,
                    "score": float(score),
                    "document_id": doc.metadata.get("document_id"),
                    "company_name": doc.metadata.get("company_name"),
                    "file_name": doc.metadata.get("file_name"),
                    "page_number": doc.metadata.get("page_number"),
                    "chunk_index": doc.metadata.get("chunk_index"),
                    "source": doc.metadata.get("source"),
                }
            )

        return hits

    def delete_document(self, document_id: str) -> bool:
        """Remove the FAISS index directory for a document."""
        index_path = self._document_index_path(document_id)
        if index_path.exists():
            shutil.rmtree(index_path, ignore_errors=True)
            return True
        return False

    def _extract_pages(self, file_path: str, warnings: List[str]) -> List[PageText]:
        """
        Extract text page-by-page. Any page whose native text layer is too
        thin (a scanned image page) is re-processed with OCR.
        """
        pages: List[PageText] = []
        ocr_warned = False

        with fitz.open(file_path) as pdf:
            for i, page in enumerate(pdf, start=1):
                raw_text = self._clean_text(page.get_text("text"))

                if len(raw_text) >= self.config.MIN_CHARS_PER_PAGE_BEFORE_OCR:
                    pages.append(PageText(page_number=i, text=raw_text, source="text_layer"))
                    continue

                if not OCR_AVAILABLE:
                    if not ocr_warned:
                        warnings.append(
                            "Some pages appear to be scanned images, but "
                            "pytesseract/Tesseract is not installed, so OCR "
                            "could not run. Install Tesseract to extract "
                            "text from scanned pages."
                        )
                        ocr_warned = True
                    pages.append(PageText(page_number=i, text=raw_text, source="empty"))
                    continue

                ocr_text = self._ocr_page(page)
                if ocr_text:
                    pages.append(PageText(page_number=i, text=ocr_text, source="ocr"))
                else:
                    pages.append(PageText(page_number=i, text="", source="empty"))

        return pages

    def _ocr_page(self, page: "fitz.Page") -> str:
        """Render a PDF page to an image and run Tesseract OCR on it."""
        try:
            zoom = self.config.OCR_DPI / 72 
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))

            raw_text = pytesseract.image_to_string(image, lang=self.config.OCR_LANG)
            return self._clean_text(raw_text)
        except Exception:  # noqa: BLE001
            logger.exception("OCR failed on page %d", page.number + 1)
            return ""

    @staticmethod
    def _clean_text(text: str) -> str:
        """Collapse excess whitespace/form-feeds left over from extraction/OCR."""
        text = text.replace("\x0c", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _build_langchain_documents(
        self, pages: List[PageText], metadata: DocumentMetadata
    ) -> List[LCDocument]:
        """Wrap each page as a LangChain Document; metadata survives the split."""
        docs = []
        for page in pages:
            if not page.text:
                continue
            docs.append(
                LCDocument(
                    page_content=page.text,
                    metadata={
                        "document_id": metadata.document_id,
                        "user_id": metadata.user_id,
                        "company_name": metadata.company_name,
                        "file_name": metadata.file_name,
                        "page_number": page.page_number,
                        "source": page.source,  
                        "section": None,          
                    },
                )
            )
        return docs

    def _index_chunks(self, chunks: List[LCDocument], document_id: str) -> None:
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i

        index_path = self._document_index_path(document_id)

        if index_path.exists():
            vector_store = FAISS.load_local(
                str(index_path), self.embeddings, allow_dangerous_deserialization=True
            )
            vector_store.add_documents(chunks)
        else:
            vector_store = FAISS.from_documents(chunks, self.embeddings)

        vector_store.save_local(str(index_path))

    def _load_document_index(self, document_id: str) -> Optional[FAISS]:
        index_path = self._document_index_path(document_id)
        if not index_path.exists():
            return None
        return FAISS.load_local(
            str(index_path), self.embeddings, allow_dangerous_deserialization=True
        )

    def _document_index_path(self, document_id: str) -> Path:
        return self.config.VECTOR_STORE_ROOT / f"doc_{document_id}"

try:
    from fastapi import APIRouter, UploadFile, File, Form, HTTPException
    from pydantic import BaseModel

    router = APIRouter()
    _agent_singleton: Optional[DocumentAgent] = None

    def get_document_agent() -> DocumentAgent:
        global _agent_singleton
        if _agent_singleton is None:
            _agent_singleton = DocumentAgent()
        return _agent_singleton

    class SearchRequest(BaseModel):
        document_id: str
        query: str
        k: int = 5
        company_filter: Optional[str] = None

    @router.post("/upload")
    async def upload_document(
        document_id: str = Form(...),
        user_id: str = Form(...),
        company_name: str = Form("Unknown"),
        file: UploadFile = File(...),
    ):
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        agent = get_document_agent()
        save_dir = agent.config.UPLOAD_ROOT / user_id
        save_dir.mkdir(parents=True, exist_ok=True)
        dest_path = save_dir / file.filename

        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = agent.process_document(
            file_path=str(dest_path), document_id=document_id, user_id=user_id, company_name=company_name,
        )

        if result.document.status == "failed":
            raise HTTPException(status_code=422, detail=result.document.error)

        return {
            "document_id": result.document.document_id,
            "file_name": result.document.file_name,
            "company_name": result.document.company_name,
            "page_count": result.document.page_count,
            "ocr_page_count": result.document.ocr_page_count,
            "chunks_indexed": result.chunks_indexed,
            "status": result.document.status,
            "warnings": result.warnings,
        }

    @router.post("/search")
    async def search_documents(payload: SearchRequest):
        agent = get_document_agent()
        hits = agent.search(
            document_id=payload.document_id,
            query=payload.query,
            k=payload.k,
            company_filter=payload.company_filter,
        )
        return {"results": hits}

    @router.delete("/{document_id}")
    async def delete_document(document_id: str):
        agent = get_document_agent()
        deleted = agent.delete_document(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found.")
        return {"deleted": True, "document_id": document_id}

except ImportError:
    router = None
    logger.info("FastAPI not installed — skipping router setup; DocumentAgent class still usable directly.")


# --------------------------------------------------------------------------- #
# Standalone smoke test
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python document_agent.py <path_to_pdf> [company_name]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    company = sys.argv[2] if len(sys.argv) > 2 else "NexaCore Technologies"
    test_doc = "demo-doc-001"
    test_user = "demo-user-001"

    agent = DocumentAgent()
    result = agent.process_document(pdf_path, document_id=test_doc, user_id=test_user, company_name=company)

    print(f"\nStatus: {result.document.status}")
    print(f"Pages: {result.document.page_count} (OCR used on {result.document.ocr_page_count})")
    print(f"Chunks indexed: {result.chunks_indexed}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")

    if result.document.status == "indexed":
        print("\n--- Sample search: 'red flags in debt levels' ---")
        for hit in agent.search(test_doc, "red flags in debt levels", k=3):
            print(f"\n[p.{hit['page_number']} | {hit['source']}] score={hit['score']:.4f}")
            print(hit["text"][:300], "...")
