"""
Research Agent.

The repo's own `research_agent_demo.py` is a toy script (hardcoded mock
"vector DB", no LLM, meant only to demonstrate the retrieve -> prompt ->
answer shape). This module implements the real thing:

  1. Retrieve top-k relevant chunks from the Document Agent's FAISS index for
     the active session (optionally scoped to one document).
  2. Build a grounded prompt instructing the model to answer only from that
     context.
  3. Call Groq's chat-completions endpoint (OpenAI-compatible) directly over
     HTTP -- no extra LangChain dependency needed for this one call.
  4. Return an answer plus structured citations the frontend can render.

If no GROQ_API_KEY is configured, it degrades to an extractive fallback:
it stitches together the retrieved snippets and marks the answer as
untranslated by an LLM, rather than failing the chat entirely.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from config import settings
from document_agent_loader import get_document_agent

logger = logging.getLogger("orchestrator.research")

SYSTEM_PROMPT = (
    "You are a financial research assistant. Answer the user's question using "
    "ONLY the numbered context passages provided. Every factual claim must be "
    "traceable to a passage. If the answer is not present in the context, say "
    "so plainly instead of guessing. Keep answers concise and cite passages "
    "inline like [1], [2] matching the passage numbers given."
)


def _format_context(hits: list[dict[str, Any]]) -> str:
    blocks = []
    for i, hit in enumerate(hits, start=1):
        blocks.append(
            f"[{i}] Company: {hit.get('company_name') or 'Unknown'} | "
            f"File: {hit.get('file_name') or 'Unknown'} | Page: {hit.get('page_number') or '?'}\n"
            f"{hit.get('text', '').strip()}"
        )
    return "\n\n".join(blocks)


async def _call_groq(query: str, context: str) -> str:
    if not settings.groq_api_key:
        return ""

    payload = {
        "model": settings.groq_model,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"CONTEXT PASSAGES:\n{context}\n\nQUESTION:\n{query}\n\nANSWER:",
            },
        ],
    }
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            resp = await client.post(
                f"{settings.groq_api_base}/chat/completions", json=payload, headers=headers
            )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Groq call failed, falling back to extractive answer: %s", exc)
        return ""


def _extractive_fallback(query: str, hits: list[dict[str, Any]]) -> str:
    if not hits:
        return "I couldn't find anything relevant to that question in the uploaded documents."
    lines = ["Here's what the source documents say (no LLM configured, showing raw excerpts):"]
    for i, hit in enumerate(hits, start=1):
        snippet = (hit.get("text") or "").strip().replace("\n", " ")
        lines.append(f"[{i}] {snippet[:400]}")
    return "\n".join(lines)


async def answer_question(
    session_id: str, query: str, document_id: str | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """
    Returns (answer_text, citations) where citations is a list of
    {document_id, page, snippet} dicts matching the frontend's Citation shape.
    """
    document_agent = get_document_agent()
    hits = document_agent.search(
        session_id=session_id,
        query=query,
        k=settings.research_top_k,
        document_id_filter=document_id,
    )

    if not hits:
        return (
            "I don't have any indexed content to search yet for this session. "
            "Upload a document first.",
            [],
        )

    context = _format_context(hits)
    answer = await _call_groq(query, context)
    if not answer:
        answer = _extractive_fallback(query, hits)

    citations = [
        {
            "document_id": hit.get("document_id"),
            "page": hit.get("page_number"),
            "snippet": (hit.get("text") or "").strip()[:300],
        }
        for hit in hits
    ]
    return answer, citations
