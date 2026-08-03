"""
The core orchestration workflow triggered on every document upload:

    1. Document Agent  -- parse the PDF, chunk it, embed it, index it in FAISS
                           (scoped to the session) so the Research Agent can
                           retrieve from it later.
    2. Extraction Agent -- pull structured financial metrics out of the file.
    3. Red Flag Agent   -- combine those metrics with qualitative sections
                           pulled from the vector index to surface risks.

Each step is best-effort: if the Extraction or Red Flag *services* are
unreachable or fail, the document is still indexed and searchable, and the
failure is recorded as a warning rather than aborting the whole pipeline.
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session as DBSession

import models
from agent_clients import AgentUnavailableError, extraction_client, redflag_client
from document_agent_loader import get_document_agent
from utils import build_document_sections, build_redflag_metrics, resolve_company_and_year

logger = logging.getLogger("orchestrator.pipeline")


async def run_document_pipeline(document_id: str, db_factory) -> None:
    """
    Runs the full pipeline for one document. `db_factory` is a callable
    returning a fresh SQLAlchemy Session (background tasks must not reuse a
    request-scoped session).
    """
    db: DBSession = db_factory()
    try:
        document = db.get(models.Document, document_id)
        if document is None:
            logger.warning("Pipeline invoked for missing document_id=%s", document_id)
            return

        warnings: list[str] = []

        # --- Step 1: Document Agent — parse, chunk, embed, index --- #
        try:
            document_agent = get_document_agent()
            result = document_agent.process_document(
                file_path=document.file_path,
                session_id=document.session_id,
                company_name=document.company_name or "Unknown",
            )
            document.page_count = result.document.page_count
            document.chunks_indexed = result.chunks_indexed
            document.vector_document_id = result.document.document_id
            warnings.extend(result.warnings)
            if result.document.status == "failed":
                document.status = "failed"
                document.error = result.document.error or "Document Agent failed to index the file."
                document.warnings = warnings
                db.commit()
                return
        except Exception as exc:  # noqa: BLE001
            logger.exception("Document Agent step failed for %s", document_id)
            document.status = "failed"
            document.error = f"Document Agent error: {exc}"
            document.warnings = warnings
            db.commit()
            return

        # --- Step 2: Extraction Agent — structured financial metrics --- #
        financial_data: dict = {}
        confidence_score = 0.0
        try:
            file_bytes = Path(document.file_path).read_bytes()
            extraction_response = await extraction_client.extract(
                file_bytes=file_bytes,
                filename=document.file_name,
                content_type="application/pdf",
            )
            if extraction_response.get("success", True):
                financial_data = extraction_response.get("financial_data") or {}
                confidence_score = float(extraction_response.get("confidence_score") or 0.0)
                warnings.extend(extraction_response.get("warnings") or [])
            else:
                warnings.append(
                    f"Extraction Agent reported failure: "
                    f"{'; '.join(extraction_response.get('errors') or ['unknown error'])}"
                )
        except AgentUnavailableError as exc:
            logger.warning("Extraction Agent unavailable for %s: %s", document_id, exc)
            warnings.append(f"Extraction Agent unavailable: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Extraction Agent step failed for %s", document_id)
            warnings.append(f"Extraction Agent error: {exc}")

        company_name, financial_year = resolve_company_and_year(financial_data)
        document.company_name = company_name
        document.financial_year = financial_year
        document.financial_data = financial_data
        document.confidence_score = confidence_score

        # --- Step 3: Red Flag Agent — deterministic + LLM risk analysis --- #
        red_flags: list[dict] = []
        overall_risk = None
        risk_summary = None
        try:
            metrics_payload = build_redflag_metrics(financial_data)
            if metrics_payload:
                sections = build_document_sections(
                    document_agent=document_agent,
                    session_id=document.session_id,
                    document_id=document.vector_document_id,
                    company_name=company_name,
                )
                redflag_payload = {
                    "company": company_name,
                    "financial_year": financial_year,
                    "metrics": metrics_payload,
                    "document_sections": sections,
                }
                redflag_response = await redflag_client.analyze(redflag_payload)
                red_flags = redflag_response.get("red_flags") or []
                overall_risk = redflag_response.get("overall_risk")
                risk_summary = redflag_response.get("summary")
            else:
                warnings.append(
                    "Skipped red flag analysis: no numeric metrics were extracted from this document."
                )
        except AgentUnavailableError as exc:
            logger.warning("Red Flag Agent unavailable for %s: %s", document_id, exc)
            warnings.append(f"Red Flag Agent unavailable: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Red Flag Agent step failed for %s", document_id)
            warnings.append(f"Red Flag Agent error: {exc}")

        document.red_flags = red_flags
        document.overall_risk = overall_risk
        document.risk_summary = risk_summary
        document.warnings = warnings
        document.status = "ready"
        db.commit()
        logger.info("Pipeline complete for document %s (status=ready)", document_id)

    except Exception:  # noqa: BLE001
        logger.exception("Unhandled pipeline failure for document %s", document_id)
        db.rollback()
        document = db.get(models.Document, document_id)
        if document is not None:
            document.status = "failed"
            document.error = "Unhandled orchestration error; check server logs."
            db.commit()
    finally:
        db.close()
