from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchSession(Base):
    """A workspace grouping uploaded documents, chat, comparisons, and reports."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Document(Base):
    """One uploaded PDF and everything the agent pipeline produced from it."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)

    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), default="Unknown")
    financial_year: Mapped[str] = mapped_column(String(80), default="Unspecified")
    vector_document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing|ready|failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    page_count: Mapped[int] = mapped_column(Integer, default=0)
    chunks_indexed: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[float] = mapped_column(default=0.0)

    financial_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    red_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    overall_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped["ResearchSession"] = relationship(back_populates="documents")


class ChatMessage(Base):
    """A single turn (user question or assistant answer) in a session's Research chat."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user|assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped["ResearchSession"] = relationship(back_populates="chat_messages")


class Report(Base):
    """An analyst-style PDF generated for one or more documents in a session."""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    document_ids: Mapped[list] = mapped_column(JSON, default=list)

    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="generating")  # generating|ready|failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped["ResearchSession"] = relationship(back_populates="reports")
