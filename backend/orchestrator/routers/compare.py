from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

import models
import schemas
from database import get_db
from services.comparison import compare_documents

router = APIRouter(prefix="/sessions", tags=["compare"])


@router.post("/{session_id}/compare", response_model=schemas.CompareResponse)
async def compare(session_id: str, payload: schemas.CompareRequest, db: DBSession = Depends(get_db)):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    documents = []
    for document_id in payload.document_ids:
        document = db.get(models.Document, document_id)
        if document is None or document.session_id != session_id:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found in this session")
        documents.append(document)

    rows, summary = await compare_documents(documents)
    return schemas.CompareResponse(
        companies=[schemas.CompanyComparison(**row) for row in rows], summary=summary
    )
