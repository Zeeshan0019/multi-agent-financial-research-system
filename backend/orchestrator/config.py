"""
Central configuration for the orchestration layer.

Every other agent in this repo (Document Agent, Extraction Agent, Red Flag
Agent) already reads its own environment variables, so the orchestrator
follows the same convention: everything is overridable via env vars / a
`.env` file, with sane local-dev defaults.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Orchestrator's own HTTP server ---
    host: str = "0.0.0.0"
    port: int = 8000
    cors_allow_origins: str = "*"

    # --- Downstream agent services (each runs as its own FastAPI process) ---
    extraction_agent_url: str = "http://localhost:8001"
    redflag_agent_url: str = "http://localhost:8002"
    agent_request_timeout: float = 120.0
    agent_health_timeout: float = 5.0

    # --- Document Agent is imported in-process (it ships only an APIRouter,
    #     not its own app), so we point at the .py file to load it dynamically
    #     even though its folder name ("document Agent") has a space in it. ---
    document_agent_path: str = str(
        (BASE_DIR / ".." / "document Agent" / "document_agent.py").resolve()
    )

    # --- Storage ---
    data_dir: str = str((BASE_DIR / "data").resolve())
    database_url: str = ""  # derived from data_dir if empty
    upload_dir: str = ""
    reports_dir: str = ""
    vector_store_dir: str = ""

    # --- Research Agent (RAG chat) / LLM ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_api_base: str = "https://api.groq.com/openai/v1"
    llm_timeout_seconds: float = 60.0
    research_top_k: int = 6

    # --- Defaults used when a document is missing identifying fields ---
    default_company_name: str = "Unknown Company"
    default_financial_year: str = "Unspecified"

    def finalize(self) -> "Settings":
        """Fill in directory-derived defaults and ensure they exist on disk."""
        data_dir = Path(self.data_dir)
        if not self.upload_dir:
            self.upload_dir = str(data_dir / "uploads")
        if not self.reports_dir:
            self.reports_dir = str(data_dir / "reports")
        if not self.vector_store_dir:
            self.vector_store_dir = str(data_dir / "vector_store")
        if not self.database_url:
            self.database_url = f"sqlite:///{data_dir / 'orchestrator.db'}"

        for path in (self.upload_dir, self.reports_dir, self.vector_store_dir):
            Path(path).mkdir(parents=True, exist_ok=True)
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        return self


settings = Settings().finalize()

# The Document Agent's own config expects these as directories it manages
# itself; we redirect them into our shared data dir so everything lives in
# one place regardless of which working directory uvicorn is launched from.
os.environ.setdefault("DOCUMENT_AGENT_VECTOR_STORE", settings.vector_store_dir)
