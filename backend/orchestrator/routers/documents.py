from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session as DBSession

import models
import schemas
from config import settings
from database import SessionLocal, get_db
from document_agent_loader import get_document_agent
from services.pipeline import run_document_pipeline
from utils import build_display_metrics

router = APIRouter(tags=["documents"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def _to_document_summary(document: models.Document) -> schemas.DocumentSummary:
    return schemas.DocumentSummary(
        id=document.id,
        file_name=document.file_name,
        company_name=document.company_name,
        status=document.status,
        uploaded_at=document.uploaded_at,
        page_count=document.page_count,
        overall_risk=document.overall_risk,
    )


def _to_red_flags(document: models.Document) -> list[schemas.RedFlagOut]:
    flags = document.red_flags or []
    out = []
    for i, flag in enumerate(flags):
        out.append(
            schemas.RedFlagOut(
                id=f"{document.id}-flag-{i}",
                category=flag.get("category"),
                title=flag.get("title"),
                severity=str(flag.get("severity", "medium")),
                description=flag.get("description", ""),
                recommendation=flag.get("recommendation"),
                source_page=flag.get("source_page"),
            )
        )
    return out


def _to_document_detail(document: models.Document) -> schemas.DocumentDetail:
    return schemas.DocumentDetail(
        id=document.id,
        file_name=document.file_name,
        company_name=document.company_name,
        financial_year=document.financial_year,
        status=document.status,
        error=document.error,
        confidence_score=document.confidence_score or 0.0,
        page_count=document.page_count,
        warnings=document.warnings or [],
        metrics=schemas.DocumentMetrics(**build_display_metrics(document.financial_data)),
        red_flags=_to_red_flags(document),
        overall_risk=document.overall_risk,
        risk_summary=document.risk_summary,
        uploaded_at=document.uploaded_at,
    )


@router.post("/sessions/{session_id}/documents", response_model=schemas.DocumentSummary)
async def upload_document(
    session_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 50MB upload limit.")
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    document = models.Document(
        session_id=session_id,
        file_name=file.filename,
        file_path="",  # filled in below once we know the document id
        company_name="Unknown",
        status="processing",
    )
    db.add(document)
    db.flush()  # assigns document.id without committing yet

    save_dir = Path(settings.upload_dir) / session_id
    save_dir.mkdir(parents=True, exist_ok=True)
    dest_path = save_dir / f"{document.id}_{file.filename}"
    dest_path.write_bytes(data)
    document.file_path = str(dest_path)

    db.commit()
    db.refresh(document)

    # Run the Document/Extraction/Red-Flag pipeline in the background so the
    # upload responds immediately; the frontend polls document status.
    background_tasks.add_task(run_document_pipeline, document.id, SessionLocal)

    return _to_document_summary(document)


@router.get("/sessions/{session_id}/documents", response_model=list[schemas.DocumentSummary])
def list_documents(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return [_to_document_summary(d) for d in session.documents]


@router.get("/documents/{document_id}", response_model=schemas.DocumentDetail)
def get_document(document_id: str, db: DBSession = Depends(get_db)):
    document = db.get(models.Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_document_detail(document)


@router.get("/documents/{document_id}/metrics", response_model=schemas.DocumentMetrics)
def get_document_metrics(document_id: str, db: DBSession = Depends(get_db)):
    document = db.get(models.Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return schemas.DocumentMetrics(**build_display_metrics(document.financial_data))


@router.get("/documents/{document_id}/red-flags", response_model=list[schemas.RedFlagOut])
def get_document_red_flags(document_id: str, db: DBSession = Depends(get_db)):
    document = db.get(models.Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_red_flags(document)


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: DBSession = Depends(get_db)):
    document = db.get(models.Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    session_id = document.session_id
    try:
        if document.vector_document_id:
            document_agent = get_document_agent()
            document_agent.delete_document(session_id, document.vector_document_id)
    except Exception:  # noqa: BLE001
        pass  # index may already be gone/empty; deleting the DB row still proceeds

    if document.file_path:
        Path(document.file_path).unlink(missing_ok=True)

    db.delete(document)
    db.commit()
    return {"deleted": True, "id": document_id}
