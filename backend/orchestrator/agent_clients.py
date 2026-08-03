"""
Thin async HTTP clients around the two agents that run as their own FastAPI
microservices: the Extraction Agent (`/extract`) and the Red Flag Agent
(`/redflags`). The Document Agent is used in-process instead (see
`document_agent_loader.py`), since it ships only a router, not a standalone app.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger("orchestrator.agent_clients")


class AgentUnavailableError(RuntimeError):
    """Raised when a downstream agent can't be reached or errors out."""


class ExtractionAgentClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.extraction_agent_url).rstrip("/")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=settings.agent_health_timeout) as client:
                resp = await client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def extract(self, file_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
        """POST the raw file to the Extraction Agent's /extract endpoint."""
        try:
            async with httpx.AsyncClient(timeout=settings.agent_request_timeout) as client:
                files = {"file": (filename, file_bytes, content_type or "application/octet-stream")}
                resp = await client.post(f"{self.base_url}/extract", files=files)
        except httpx.HTTPError as exc:
            raise AgentUnavailableError(f"Extraction Agent unreachable: {exc}") from exc

        if resp.status_code >= 400:
            raise AgentUnavailableError(
                f"Extraction Agent returned {resp.status_code}: {resp.text[:500]}"
            )
        return resp.json()


class RedFlagAgentClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.redflag_agent_url).rstrip("/")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=settings.agent_health_timeout) as client:
                resp = await client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST a structured metrics/document_sections payload to /redflags."""
        try:
            async with httpx.AsyncClient(timeout=settings.agent_request_timeout) as client:
                resp = await client.post(f"{self.base_url}/redflags", json=payload)
        except httpx.HTTPError as exc:
            raise AgentUnavailableError(f"Red Flag Agent unreachable: {exc}") from exc

        if resp.status_code >= 400:
            raise AgentUnavailableError(
                f"Red Flag Agent returned {resp.status_code}: {resp.text[:500]}"
            )
        return resp.json()


extraction_client = ExtractionAgentClient()
redflag_client = RedFlagAgentClient()
