"""
Research Agent  —  Multi-Agent Financial Research System (Vidzai Digital project)
-----------------------------------------------------------------------------
Implements the "Research Agent" module described in the project spec:
  - Handles multi-part user queries
  - Uses multi-step retrieval + reasoning
  - Answers with strict source citation (grounded only in the indexed document)
  - Never states information the source document doesn't contain

This is a standalone, runnable reference implementation. It plugs into the rest
of the pipeline (Document Agent -> Extraction Agent -> Red Flag Agent -> Research
Agent -> Report Agent) by consuming whatever text the Document Agent has chunked
and indexed. Retrieval here uses TF-IDF cosine similarity as a lightweight,
dependency-light stand-in for a vector database + embedding model — swap
`TfidfRetriever` for a real embedding-based retriever (e.g. FAISS + OpenAI/
Anthropic embeddings) in production without changing the Research Agent logic.
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# 1. DOCUMENT AGENT (minimal stand-in): chunking
# ---------------------------------------------------------------------------
def chunk_document(raw_text: str) -> List[Dict]:
    """Splits the source document into cited, addressable chunks by section
    and paragraph, mimicking what the Document Agent hands to the vector DB."""
    chunks = []
    section = "UNSPECIFIED"
    chunk_id = 0
    for block in raw_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        header_match = re.match(r"^(SECTION \d+:.*)$", block.splitlines()[0])
        if header_match:
            section = header_match.group(1).strip()
        # further split long sections into sentence-group sub-chunks (~2-3 sentences)
        sentences = re.split(r"(?<=[.])\s+", block)
        buf = []
        for s in sentences:
            buf.append(s)
            if len(buf) >= 3:
                chunk_id += 1
                chunks.append({"id": f"C{chunk_id}", "section": section, "text": " ".join(buf).strip()})
                buf = []
        if buf:
            chunk_id += 1
            chunks.append({"id": f"C{chunk_id}", "section": section, "text": " ".join(buf).strip()})
    return chunks


# ---------------------------------------------------------------------------
# 2. RETRIEVER (stand-in for vector DB / embeddings)
# ---------------------------------------------------------------------------
class TfidfRetriever:
    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
        self.texts = [c["text"] for c in chunks]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.texts)

    def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        qvec = self.vectorizer.transform([query])
        sims = cosine_similarity(qvec, self.matrix)[0]
        ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:k]
        results = []
        for i in ranked:
            if sims[i] <= 0:
                continue
            c = dict(self.chunks[i])
            c["score"] = round(float(sims[i]), 3)
            results.append(c)
        return results


# ---------------------------------------------------------------------------
# 3. RESEARCH AGENT: decomposition, multi-step retrieval, grounded synthesis
# ---------------------------------------------------------------------------
@dataclass
class SubAnswer:
    sub_question: str
    retrieved: List[Dict]
    finding: str


@dataclass
class ResearchAnswer:
    query: str
    sub_answers: List[SubAnswer] = field(default_factory=list)
    synthesis: str = ""
    citations: List[str] = field(default_factory=list)


class ResearchAgent:
    """Answers multi-part financial questions with step-by-step retrieval and
    exact source citation, grounded ONLY in the indexed document."""

    def __init__(self, retriever: TfidfRetriever):
        self.retriever = retriever

    def decompose(self, query: str) -> List[str]:
        """Naive rule-based decomposition of a multi-part question into
        retrievable sub-questions. A production version would use an LLM call
        here; kept rule-based so this module runs with zero external API calls."""
        # split on common multi-part connectors
        parts = re.split(r"\band\b|\?|;", query, flags=re.IGNORECASE)
        parts = [p.strip() for p in parts if len(p.strip()) > 8]
        return parts if parts else [query]

    def answer(self, query: str, k: int = 3) -> ResearchAnswer:
        sub_questions = self.decompose(query)
        result = ResearchAnswer(query=query)
        seen_citations = []

        for sq in sub_questions:
            hits = self.retriever.retrieve(sq, k=k)
            if not hits:
                finding = "No grounded information found in the indexed document for this part of the question."
            else:
                finding = self._synthesize_from_chunks(hits)
                for h in hits:
                    tag = f"[{h['id']} | {h['section']}]"
                    if tag not in seen_citations:
                        seen_citations.append(tag)
            result.sub_answers.append(SubAnswer(sub_question=sq, retrieved=hits, finding=finding))

        result.synthesis = self._final_synthesis(result.sub_answers)
        result.citations = seen_citations
        return result

    def _synthesize_from_chunks(self, hits: List[Dict]) -> str:
        # Grounded synthesis: concatenate the retrieved evidence with citation tags.
        # (In production this step is an LLM call constrained to the retrieved
        # context only — "answer using ONLY the following excerpts".)
        lines = []
        for h in hits:
            lines.append(f"{h['text']} [{h['id']}]")
        return " ".join(lines)

    def _final_synthesis(self, sub_answers: List[SubAnswer]) -> str:
        lines = []
        for sa in sub_answers:
            lines.append(f"- On \"{sa.sub_question}\": {sa.finding}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. ACCURACY / GROUNDING SELF-CHECK
#    (mirrors the project's evaluation criterion #3: "source citation accuracy")
# ---------------------------------------------------------------------------
def grounding_accuracy(answer: ResearchAnswer, chunks_by_id: Dict[str, Dict]) -> Dict:
    """Checks that every citation tag referenced in the answer actually points
    to a real chunk, and that a sample of numeric claims in the synthesis
    appear verbatim in the cited chunk text (a proxy for hallucination rate)."""
    total_sub_answers = len(answer.sub_answers)
    grounded_sub_answers = 0
    numeric_claims_checked = 0
    numeric_claims_grounded = 0

    for sa in answer.sub_answers:
        cited_ids = re.findall(r"\[(C\d+)\]", sa.finding)
        if cited_ids and all(cid in chunks_by_id for cid in cited_ids):
            grounded_sub_answers += 1

        # pull numeric tokens (%, Rs figures, bps, x-multiples) out of the finding
        numbers = re.findall(r"\d+[\d,\.]*\s?(?:%|bps|cr|crore|x)?", sa.finding)
        cited_text = " ".join(chunks_by_id[cid]["text"] for cid in cited_ids if cid in chunks_by_id)
        for num in numbers:
            num_clean = num.strip()
            if len(num_clean) < 2:
                continue
            numeric_claims_checked += 1
            if num_clean.split()[0].rstrip(",.") in cited_text:
                numeric_claims_grounded += 1

    citation_validity = grounded_sub_answers / total_sub_answers if total_sub_answers else 0
    numeric_grounding = (numeric_claims_grounded / numeric_claims_checked) if numeric_claims_checked else 1.0

    return {
        "sub_questions_answered": total_sub_answers,
        "sub_answers_with_valid_citations": grounded_sub_answers,
        "citation_validity_rate": round(citation_validity * 100, 1),
        "numeric_claims_checked": numeric_claims_checked,
        "numeric_claims_grounded_in_cited_chunk": numeric_claims_grounded,
        "numeric_grounding_rate": round(numeric_grounding * 100, 1),
    }


# ---------------------------------------------------------------------------
# DEMO RUN on the NexaCore FY2025 Annual Report
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    with open("nexacore_source.txt", "r", encoding="utf-8") as f:
        raw = f.read()

    chunks = chunk_document(raw)
    chunks_by_id = {c["id"]: c for c in chunks}
    retriever = TfidfRetriever(chunks)
    agent = ResearchAgent(retriever)

    demo_query = (
        "What is driving NexaCore's operating margin decline, and what are the "
        "biggest financial red flags in the FY2025 annual report?"
    )

    result = agent.answer(demo_query, k=3)
    accuracy = grounding_accuracy(result, chunks_by_id)

    print("=" * 90)
    print("RESEARCH AGENT — QUERY")
    print("=" * 90)
    print(result.query)

    print("\n" + "=" * 90)
    print("STEP-BY-STEP RETRIEVAL & REASONING")
    print("=" * 90)
    for i, sa in enumerate(result.sub_answers, 1):
        print(f"\nSub-question {i}: {sa.sub_question}")
        print(f"Retrieved chunks: {[h['id'] for h in sa.retrieved]} (scores: {[h['score'] for h in sa.retrieved]})")
        print(f"Finding: {sa.finding[:400]}{'...' if len(sa.finding) > 400 else ''}")

    print("\n" + "=" * 90)
    print("FINAL SYNTHESIZED ANSWER (with citations)")
    print("=" * 90)
    print(result.synthesis)
    print(f"\nCitations used: {result.citations}")

    print("\n" + "=" * 90)
    print("ACCURACY / GROUNDING SELF-CHECK")
    print("=" * 90)
    print(json.dumps(accuracy, indent=2))
