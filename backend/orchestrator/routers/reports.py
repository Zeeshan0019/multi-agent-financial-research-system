from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

import models
import schemas
from database import SessionLocal, get_db
from services.reports import generate_report_sync

logger = logging.getLogger("orchestrator.routers.reports")
router = APIRouter(tags=["reports"])


def _download_url(report: models.Report) -> str | None:
    if report.status != "ready" or not report.file_path:
        return None
    return f"/reports/{report.id}/download"


def _to_report_summary(report: models.Report) -> schemas.ReportSummary:
    return schemas.ReportSummary(
        id=report.id,
        file_name=report.file_name,
        generated_at=report.generated_at,
        download_url=_download_url(report),
    )


def _run_report_job(report_id: str) -> None:
    """Runs synchronously in a background task (reportlab is not async)."""
    db = SessionLocal()
    try:
        report = db.get(models.Report, report_id)
        if report is None:
            return
        try:
            documents = [
                db.get(models.Document, doc_id) for doc_id in report.document_ids
            ]
            documents = [d for d in documents if d is not None]
            if not documents:
                raise ValueError("None of the requested documents were found.")

            session = db.get(models.ResearchSession, report.session_id)
            output_path = generate_report_sync(
                report_id=report.id,
                session_id=report.session_id,
                session_name=session.name if session else "Session",
                documents=documents,
            )
            report.file_path = str(output_path)
            report.file_name = output_path.name
            report.status = "ready"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Report generation failed for %s", report_id)
            report.status = "failed"
            report.error = str(exc)
        db.commit()
    finally:
        db.close()


@router.get("/sessions/{session_id}/reports", response_model=list[schemas.ReportSummary])
def list_reports(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    reports = db.scalars(
        select(models.Report)
        .where(models.Report.session_id == session_id)
        .order_by(models.Report.generated_at.desc())
    ).all()
    return [_to_report_summary(r) for r in reports]


@router.post("/sessions/{session_id}/reports", response_model=schemas.ReportStatus)
def generate_report(
    session_id: str,
    payload: schemas.ReportRequest,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    for document_id in payload.document_ids:
        document = db.get(models.Document, document_id)
        if document is None or document.session_id != session_id:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found in this session")

    report = models.Report(
        session_id=session_id, document_ids=payload.document_ids, status="generating"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    background_tasks.add_task(_run_report_job, report.id)

    return schemas.ReportStatus(id=report.id, status=report.status)


@router.get("/reports/{report_id}", response_model=schemas.ReportStatus)
def get_report(report_id: str, db: DBSession = Depends(get_db)):
    report = db.get(models.Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return schemas.ReportStatus(
        id=report.id, status=report.status, download_url=_download_url(report), error=report.error
    )


@router.get("/reports/{report_id}/download")
def download_report(report_id: str, db: DBSession = Depends(get_db)):
    report = db.get(models.Report, report_id)
    if report is None or report.status != "ready" or not report.file_path:
        raise HTTPException(status_code=404, detail="Report is not ready for download")

    path = Path(report.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file is missing on disk")

    return FileResponse(path, media_type="application/pdf", filename=report.file_name or path.name)
