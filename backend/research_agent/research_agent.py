import os
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Absolute path so it works regardless of where uvicorn is launched from
VECTOR_STORE_ROOT = str(Path(__file__).resolve().parent.parent.parent / "vector_store")

# Repair ligature/symbol mis-mappings from certain PDF fonts so answers and
# snippets read cleanly (e.g. "raΘo" -> "ratio", "aΣriΘon" -> "attrition").
_LIGATURE_MAP = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
    "\ufb05": "ft", "\ufb06": "st",
    "\u019f": "ti", "\u014c": "ft", "\u01a9": "tt", "\u019e": "tf",
    "\u0166": "ft", "\u0167": "ft",
    "\uf001": "fi", "\uf002": "fl", "\uf000": "ff", "\uf003": "ffi", "\uf004": "ffl",
    "\u0398": "ti", "\u03b8": "ti", "\u03a3": "tt", "\u2211": "tt",
}


def _normalize_text_glyphs(text: str) -> str:
    if not text:
        return text
    for bad, good in _LIGATURE_MAP.items():
        if bad in text:
            text = text.replace(bad, good)
    try:
        text = unicodedata.normalize("NFKC", text)
    except Exception:
        pass
    return text


# Groq deprecated several chat models (announced 2026-06-17); a stale .env may
# still point at one, which now returns HTTP 404. Remap to a working model.
_DEPRECATED_GROQ_MODELS = {
    "llama-3.3-70b-versatile": "openai/gpt-oss-120b",
    "llama-3.1-70b-versatile": "openai/gpt-oss-120b",
    "llama3-70b-8192": "openai/gpt-oss-120b",
    "llama-3.1-8b-instant": "openai/gpt-oss-20b",
    "llama3-8b-8192": "openai/gpt-oss-20b",
    "mixtral-8x7b-32768": "openai/gpt-oss-120b",
    "gemma2-9b-it": "openai/gpt-oss-20b",
    "qwen/qwen3-32b": "openai/gpt-oss-120b",
    "meta-llama/llama-4-scout-17b-16e-instruct": "openai/gpt-oss-120b",
}


def _resolve_groq_model() -> str:
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    return _DEPRECATED_GROQ_MODELS.get(model, model)


class ResearchAgent:
    def __init__(self):
        # Lazy-load embeddings — don't block server startup
        self._embeddings = None

    @property
    def embeddings(self):
        from backend.embeddings import get_shared_embeddings
        return get_shared_embeddings()

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
                    "text": _normalize_text_glyphs(doc.page_content),
                    "score": float(score),
                    "document_id": doc.metadata.get("document_id"),
                    "company_name": doc.metadata.get("company_name", "Unknown"),
                    "file_name": doc.metadata.get("file_name"),
                    "page_number": doc.metadata.get("page_number", 1),
                    "chunk_index": doc.metadata.get("chunk_index"),
                    "source": doc.metadata.get("source", "text_layer"),
                })

        # Sort by similarity score (lower score is better for FAISS distance)
        all_hits.sort(key=lambda x: x["score"])
        return all_hits[:k]

    # ------------------------------------------------------------------ #
    # Citation helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _clean_snippet(text: str, limit: int = 220) -> str:
        """Collapse whitespace, repair ligatures, and trim into a snippet."""
        snippet = re.sub(r"\s+", " ", _normalize_text_glyphs(text or "").strip())
        if len(snippet) > limit:
            snippet = snippet[:limit].rsplit(" ", 1)[0] + "…"
        return snippet

    def _build_citations(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build a citation list where each distinct retrieved passage gets its
        own number and its own source snippet. Passages are keyed by
        (document, page, chunk) so two different excerpts from the same page are
        cited separately — the earlier behaviour collapsed them into a single
        [1] with one snippet, which made every claim appear to cite the same
        source.
        """
        citations: List[Dict[str, Any]] = []
        seen = set()
        for hit in hits:
            page = hit.get("page_number") or 1
            doc_id = hit.get("document_id")
            chunk = hit.get("chunk_index")
            key = (doc_id, page, chunk)
            if key in seen:
                continue
            seen.add(key)
            company = hit.get("company_name") or hit.get("file_name") or "Source document"
            source_kind = "OCR text" if hit.get("source") == "ocr" else "text layer"
            citations.append({
                "id": len(citations) + 1,
                "document_id": doc_id,
                "page": page,
                "chunk_index": chunk,
                "label": f"{company} · p.{page}",
                "section": f"Retrieved from page {page} ({source_kind})",
                "snippet": self._clean_snippet(hit.get("text", "")),
            })
        return citations

    def _cite_key_map(self, citations):
        """Map (document_id, page, chunk_index) -> citation id."""
        return {(c["document_id"], c["page"], c.get("chunk_index")): c["id"] for c in citations}

    def generate_answer(self, query: str, hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a professionally formatted, citation-grounded response."""
        if not hits:
            return {
                "content": (
                    "I couldn't find anything relevant to that question in the "
                    "indexed filings for this session. Try selecting a specific "
                    "document above, rephrasing the question, or uploading the "
                    "relevant filing first."
                ),
                "citations": [],
            }

        citations = self._build_citations(hits)

        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                # Number the context blocks so the model can cite them as [n],
                # aligned 1:1 with the citation list we return to the UI.
                cite_map = self._cite_key_map(citations)
                context_str = ""
                for hit in hits:
                    cite_id = cite_map.get(
                        (hit.get("document_id"), hit.get("page_number") or 1, hit.get("chunk_index")), 1
                    )
                    context_str += (
                        f"[{cite_id}] (Source: {hit.get('company_name', 'Unknown')}, "
                        f"page {hit.get('page_number', 1)})\n{_normalize_text_glyphs(hit['text']).strip()}\n\n"
                    )

                system_prompt = (
                    "You are a senior financial research analyst. Write a clear, "
                    "professional, well-structured answer to the user's question "
                    "using ONLY the numbered context provided. Follow these rules "
                    "strictly:\n"
                    "1. Ground every factual claim in the context. Never invent "
                    "numbers, names, or facts that are not present.\n"
                    "2. After each claim, cite the supporting source inline using "
                    "its bracketed number, e.g. [1] or [2][3].\n"
                    "3. Open with a one or two sentence direct answer, then, if "
                    "helpful, expand with short labelled points or a brief "
                    "paragraph. Keep the tone precise and neutral.\n"
                    "4. Report figures exactly as they appear (currency, units, "
                    "scale). Do not round unless the source rounds.\n"
                    "5. If the context does not contain enough information to "
                    "answer fully, say so plainly rather than guessing.\n"
                    "Do not restate these instructions or mention the word "
                    "'context' in your answer."
                )

                prompt = (
                    f"{system_prompt}\n\n"
                    f"Numbered context:\n{context_str}\n"
                    f"Question: {query}\n\n"
                    f"Answer (professional, with inline [n] citations):"
                )

                llm = ChatGroq(
                    model=_resolve_groq_model(),
                    temperature=0.0,
                    groq_api_key=api_key,
                    timeout=30.0,
                    max_retries=1,
                )

                response = llm.invoke(prompt)
                content = _normalize_text_glyphs((response.content or "").strip())
                if content:
                    return {"content": content, "citations": citations}
            except Exception:
                # Fall through to the local responder on any Groq failure.
                pass

        # Local, LLM-free responder — produces clean, grounded, cited prose.
        content = self._generate_local_response(query, hits, citations)
        return {"content": content, "citations": citations}

    # ------------------------------------------------------------------ #
    # Local (no-LLM) responder — professional formatting + inline [n] cites
    # ------------------------------------------------------------------ #
    def _sentences_for(self, hits, keywords, cite_map, min_len=25, limit=5, max_len=320):
        """Pull whole, clean sentences matching any keyword, each tagged with
        the citation number of the specific chunk it came from. Skips overly
        long fragments (e.g. raw metric tables) so the answer stays readable."""
        found = []
        seen_norm = set()
        for hit in hits:
            page = hit.get("page_number") or 1
            cite = cite_map.get((hit.get("document_id"), page, hit.get("chunk_index")), 1)
            text = re.sub(r"\s+", " ", _normalize_text_glyphs(hit.get("text", ""))).strip()
            # Split into sentences without shattering decimals/abbreviations.
            parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
            for s in parts:
                s = s.strip().rstrip(".") + "."
                low = s.lower()
                if len(s) < min_len or len(s) > max_len:
                    continue
                # Skip fragments that are mostly numbers/table rows (few real words)
                word_chars = len(re.findall(r"[A-Za-z]", s))
                if word_chars < len(s) * 0.4:
                    continue
                if keywords and not any(k in low for k in keywords):
                    continue
                norm = re.sub(r"[^a-z0-9]", "", low)[:80]
                if norm in seen_norm:
                    continue
                seen_norm.add(norm)
                found.append((s, cite))
                if len(found) >= limit:
                    return found
        return found

    def _generate_local_response(self, query, hits, citations) -> str:
        q = query.lower()
        cite_map = self._cite_key_map(citations)

        themes = [
            (["risk", "red flag", "threat", "concern", "warning", "adverse",
              "qualification", "auditor", "leverage", "going concern",
              "material weakness", "weakness", "litigation", "lawsuit",
              "conting", "borrowing", "debt", "impairment", "decline",
              "pressure", "uncertain", "default", "covenant"],
             "The key risks and warning signs identified in the filing are:"),
            (["profit", "net income", "margin", "earnings", "ebitda",
              "revenue", "turnover", "sales", "growth"],
             "Here is what the filing reports on revenue, profitability and margins:"),
            (["cash", "liquidity", "flow", "debt", "borrowing", "obligation",
              "capital", "expenditure", "solvency"],
             "The filing describes the cash flow, debt and liquidity position as follows:"),
            (["dividend", "shareholder", "buyback", "payout", "equity"],
             "On capital returns and shareholders, the filing states:"),
        ]

        intro = None
        sentences = []
        for keywords, heading in themes:
            if any(k in q for k in keywords):
                sentences = self._sentences_for(hits, keywords, cite_map)
                if sentences:
                    intro = heading
                    break

        # Generic fallback: summarise the most relevant retrieved passages.
        if not sentences:
            intro = "Based on the most relevant sections of the filing:"
            sentences = self._sentences_for(hits, [], cite_map, min_len=30, limit=4)

        if not sentences:
            # Nothing sentence-shaped survived — quote trimmed passages instead.
            lines = []
            for hit in hits[:3]:
                page = hit.get("page_number") or 1
                cite = cite_map.get((hit.get("document_id"), page, hit.get("chunk_index")), 1)
                lines.append(f"- {self._clean_snippet(hit.get('text', ''), 260)} [{cite}]")
            body = "\n".join(lines)
            return (
                "I found the following relevant passages in the filing:\n\n"
                f"{body}\n\n"
                "Ask a more specific question (e.g. about revenue, debt or risk "
                "factors) for a more targeted answer."
            )

        # Assemble a clean, numbered, professionally formatted answer.
        if len(sentences) == 1:
            s, cite = sentences[0]
            return f"{intro}\n\n{s} [{cite}]"

        body_lines = [f"{i}. {s} [{cite}]" for i, (s, cite) in enumerate(sentences, start=1)]
        body = "\n".join(body_lines)
        closing = "\n\nEach point above is drawn directly from the indexed filing; select a citation to see the exact source passage."
        return f"{intro}\n\n{body}{closing}"

    def ask(self, document_ids: List[str], query: str) -> Dict[str, Any]:
        """Perform search and generate a structured reply for the chat interface."""
        if not document_ids:
            return {
                "content": (
                    "No document is available to search yet. Upload and index a "
                    "filing, then select it above to start asking questions."
                ),
                "citations": [],
            }
        hits = self.search_context(document_ids, query, k=5)
        return self.generate_answer(query, hits)
