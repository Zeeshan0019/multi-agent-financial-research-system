import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Absolute path so it works regardless of where uvicorn is launched from
VECTOR_STORE_ROOT = str(Path(__file__).resolve().parent.parent.parent / "vector_store")

class ResearchAgent:
    def __init__(self):
        # Lazy-load embeddings — don't block server startup
        self._embeddings = None

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
            )
        return self._embeddings

    def _load_document_index(self, document_id: str) -> Optional[FAISS]:
        index_path = os.path.join(VECTOR_STORE_ROOT, f"doc_{document_id}")
        if not os.path.exists(index_path):
            return None
        return FAISS.load_local(
            index_path, self.embeddings, allow_dangerous_deserialization=True
        )

    def search_context(self, document_ids: List[str], query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context chunks for the selected documents and query."""
        all_hits = []
        for doc_id in document_ids:
            vector_store = self._load_document_index(doc_id)
            if not vector_store:
                continue
            results = vector_store.similarity_search_with_score(query, k=k)
            for doc, score in results:
                all_hits.append({
                    "text": doc.page_content,
                    "score": float(score),
                    "document_id": doc.metadata.get("document_id"),
                    "company_name": doc.metadata.get("company_name", "Unknown"),
                    "file_name": doc.metadata.get("file_name"),
                    "page_number": doc.metadata.get("page_number", 1),
                    "source": doc.metadata.get("source", "text_layer")
                })
        
        # Sort by similarity score (lower score is better for FAISS distance)
        all_hits.sort(key=lambda x: x["score"])
        return all_hits[:k]

    def generate_answer(self, query: str, hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response with citations based on retrieved hits."""
        if not hits:
            return {
                "content": "No relevant documents found in this session. Please upload a document first.",
                "citations": []
            }

        # Build citations list in the format expected by the frontend
        citations = []
        seen_citations = set()
        for hit in hits:
            citation_key = (hit["document_id"], hit["page_number"])
            if citation_key not in seen_citations:
                seen_citations.add(citation_key)
                citations.append({
                    "document_id": hit["document_id"],
                    "page": hit["page_number"],
                    "snippet": hit["text"][:150] + "..."
                })

        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            # GROQ LLM pipeline
            try:
                context_str = ""
                for i, hit in enumerate(hits):
                    context_str += f"[Doc {i+1} | Page {hit['page_number']} | {hit['company_name']}]: {hit['text']}\n\n"

                system_prompt = (
                    "You are a professional financial research assistant. Answer the user's question "
                    "using ONLY the provided context. Ground every statement in the context. "
                    "Include the page numbers or documents inline when referring to facts."
                )

                prompt = f"{system_prompt}\n\nContext:\n{context_str}\n\nQuestion: {query}\n\nAnswer:"
                
                llm = ChatGroq(
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    temperature=0.0,
                    groq_api_key=api_key,
                    timeout=30.0,
                    max_retries=1
                )
                
                response = llm.invoke(prompt)
                return {
                    "content": response.content,
                    "citations": citations
                }
            except Exception as e:
                # Fallback to local heuristic Q&A if Groq fails
                pass

        # Smart local heuristic/template responder based on NexaCore document content and FAISS hits
        content = self._generate_local_response(query, hits)
        return {
            "content": content,
            "citations": citations
        }

    def _generate_local_response(self, query: str, hits: List[Dict[str, Any]]) -> str:
        """Formulate a high-quality response using keywords and semantic chunks."""
        q = query.lower()
        
        # Check for specific questions commonly asked about NexaCore
        if "risk" in q or "red flag" in q or "threat" in q:
            # Compile risks from text
            risk_sentences = []
            for hit in hits:
                for line in hit["text"].split("."):
                    if any(kw in line.lower() for kw in ["risk", "debt", "leverage", "concern", "red flag", "warning", "pension", "qualification", "auditor", "adverse"]):
                        s = line.strip()
                        if len(s) > 20 and s not in risk_sentences:
                            risk_sentences.append(s)
            
            if risk_sentences:
                response = "Based on the retrieved sections, the major financial risks and warnings include:\n\n"
                for i, s in enumerate(risk_sentences[:5], start=1):
                    response += f"{i}. {s}.\n"
                return response
            
        if "profit" in q or "net income" in q or "margin" in q or "earnings" in q:
            margin_sentences = []
            for hit in hits:
                for line in hit["text"].split("."):
                    if any(kw in line.lower() for kw in ["margin", "profit", "income", "compression", "headwind", "decrease", "increase", "revenue", "ebitda"]):
                        s = line.strip()
                        if len(s) > 20 and s not in margin_sentences:
                            margin_sentences.append(s)
            
            if margin_sentences:
                response = "Here is the summary of profit, margins, and earnings trends from the document:\n\n"
                for i, s in enumerate(margin_sentences[:5], start=1):
                    response += f"{i}. {s}.\n"
                return response

        if "cash" in q or "liquidity" in q or "flow" in q or "debt" in q:
            cash_sentences = []
            for hit in hits:
                for line in hit["text"].split("."):
                    if any(kw in line.lower() for kw in ["cash", "liquidity", "debt", "borrowing", "obligations", "capital", "expenditure"]):
                        s = line.strip()
                        if len(s) > 20 and s not in cash_sentences:
                            cash_sentences.append(s)
            if cash_sentences:
                response = "Based on the source document, the cash flow and liquidity position is summarized as:\n\n"
                for i, s in enumerate(cash_sentences[:5], start=1):
                    response += f"{i}. {s}.\n"
                return response

        # General snippet compiler
        snippets = []
        for hit in hits[:3]:
            text = hit["text"].strip()
            # clean up spaces
            text = re.sub(r"\s+", " ", text)
            if len(text) > 300:
                text = text[:300] + "..."
            snippets.append(f"• From Page {hit['page_number']}: {text}")
        
        response = "Retrieved the following details from the uploaded financial document:\n\n" + "\n\n".join(snippets)
        return response

    def ask(self, document_ids: List[str], query: str) -> Dict[str, Any]:
        """Perform search and generate structured reply for the chat interface."""
        if not document_ids:
            return {
                "content": "No document selected. Please select a document to query in the workspace.",
                "citations": []
            }
        hits = self.search_context(document_ids, query, k=4)
        return self.generate_answer(query, hits)
