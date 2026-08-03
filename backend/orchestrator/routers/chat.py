from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

import models
import schemas
from database import get_db
from services.research import answer_question

router = APIRouter(prefix="/sessions", tags=["chat"])


def _to_message_out(message: models.ChatMessage) -> schemas.ChatMessageOut:
    return schemas.ChatMessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        citations=[schemas.Citation(**c) for c in (message.citations or [])],
        created_at=message.created_at,
    )


@router.get("/{session_id}/chat", response_model=list[schemas.ChatMessageOut])
def get_chat_history(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.scalars(
        select(models.ChatMessage)
        .where(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at.asc())
    ).all()
    return [_to_message_out(m) for m in messages]


@router.post("/{session_id}/chat", response_model=schemas.ChatMessageOut)
async def ask_question(session_id: str, payload: schemas.ChatQuery, db: DBSession = Depends(get_db)):
    session = db.get(models.ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = models.ChatMessage(session_id=session_id, role="user", content=payload.query)
    db.add(user_message)
    db.commit()

    answer, citations = await answer_question(
        session_id=session_id, query=payload.query, document_id=payload.document_id
    )

    assistant_message = models.ChatMessage(
        session_id=session_id, role="assistant", content=answer, citations=citations
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return _to_message_out(assistant_message)
