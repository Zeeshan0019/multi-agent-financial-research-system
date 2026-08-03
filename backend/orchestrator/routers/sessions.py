from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

import models
import schemas
from config import settings
from database import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_summary(session: models.ResearchSession) -> schemas.SessionSummary:
    return schemas.SessionSummary(
        id=session.id,
        name=session.name,
        created_at=session.created_at,
        document_count=len(session.documents),
    )


@router.post("", response_model=schemas.SessionSummary)
def create_session(payload: schemas.SessionCreate, db: DBSession = Depends(get_db)):
    session = models.ResearchSession(name=payload.name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return _to_summary(session)


@router.get("", response_model=list[schemas.SessionSummary])
def list_sessions(db: DBSession = Depends(get_db)):
    sessions = db.scalars(
        select(models.ResearchSession).order_by(models.ResearchSession.created_at.desc())
    ).all()
    return [_to_summary(s) for s in sessions]


@router.get("/{session_id}", response_model=schemas.SessionDetail)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return schemas.SessionDetail(
        id=session.id,
        name=session.name,
        created_at=session.created_at,
        document_count=len(session.documents),
        documents=[
            schemas.DocumentSummary(
                id=d.id,
                file_name=d.file_name,
                company_name=d.company_name,
                status=d.status,
                uploaded_at=d.uploaded_at,
                page_count=d.page_count,
            )
            for d in session.documents
        ],
    )


@router.delete("/{session_id}")
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    # Best-effort cleanup of on-disk artifacts for this session.
    for base in (settings.upload_dir, settings.reports_dir):
        session_dir = Path(base) / session_id
        shutil.rmtree(session_dir, ignore_errors=True)
    vector_dir = Path(settings.vector_store_dir) / session_id
    shutil.rmtree(vector_dir, ignore_errors=True)

    return {"deleted": True, "id": session_id}
