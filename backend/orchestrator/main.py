"""
Orchestration layer for the multi-agent financial research system.

This is the single backend the frontend talks to (VITE_API_BASE_URL, default
http://localhost:8000). It is NOT where the heavy document parsing happens
directly -- it coordinates three other pieces:

  * Document Agent   -- imported in-process (backend/document Agent/document_agent.py)
  * Extraction Agent -- its own FastAPI microservice (backend/Extraction agent/)
  * Red Flag Agent    -- its own FastAPI microservice (backend/Red Flag Agent/)

and implements the two agents that didn't have a real service yet:

  * Research Agent -- RAG chat grounded in the Document Agent's FAISS index
  * Report Agent   -- PDF generation from stored metrics/red flags

Run alongside:
    uvicorn main:app --reload --port 8000                                  (this file)
    uvicorn "Extraction agent.Extraction agent:app" --port 8001            (extraction agent, see its own README)
    uvicorn "Red Flag Agent.redflag_agent:app" --port 8002                 (red flag agent)

See README.md in this folder for full run instructions.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_clients import extraction_client, redflag_client
from config import settings
from database import init_db
from routers import chat, compare, documents, reports, sessions

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("orchestrator.main")

app = FastAPI(
    title="Financial Research Orchestrator",
    description=(
        "Coordinates the Document, Extraction, Red Flag, Research, and Report "
        "agents behind a single REST API for the finresearch frontend."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_allow_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(compare.router)
app.include_router(reports.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("Database ready at %s", settings.database_url)
    logger.info("Extraction Agent expected at %s", settings.extraction_agent_url)
    logger.info("Red Flag Agent expected at %s", settings.redflag_agent_url)


@app.get("/health")
async def health():
    """Aggregate health check: orchestrator DB plus reachability of the two
    downstream agent microservices (Document Agent is in-process so it's
    implicitly healthy if this process is running)."""
    extraction_ok = await extraction_client.health()
    redflag_ok = await redflag_client.health()
    return {
        "status": "ok",
        "extraction_agent": {"url": settings.extraction_agent_url, "reachable": extraction_ok},
        "redflag_agent": {"url": settings.redflag_agent_url, "reachable": redflag_ok},
        "groq_configured": bool(settings.groq_api_key),
    }


@app.get("/")
async def root():
    return {
        "service": "Financial Research Orchestrator",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)
