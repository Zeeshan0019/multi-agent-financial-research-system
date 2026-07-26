from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from datetime import datetime
from backend.database.database import Base
from sqlalchemy import Float
from sqlalchemy.orm import relationship




class ResearchSession(Base):
    __tablename__ = "research_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(100), nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    documents = relationship("Document", back_populates="research_session")
    queries = relationship("ResearchQuery", back_populates="research_session")
    reports = relationship("Report", back_populates="research_session")
class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    industry = Column(String(100))
    fiscal_year = Column(String(20))
    documents = relationship("Document", back_populates="company")

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.session_id"))
    company_id = Column(Integer, ForeignKey("companies.company_id"))

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    research_session = relationship("ResearchSession", back_populates="documents")
    company = relationship("Company", back_populates="documents")

    financial_metrics = relationship("FinancialMetric", back_populates="document")
    red_flags = relationship("RedFlag", back_populates="document")

class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    metric_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"))

    revenue = Column(Float)
    net_income = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    eps = Column(Float)
    debt_to_equity = Column(Float)
    document = relationship("Document", back_populates="financial_metrics")

class RedFlag(Base):
    __tablename__ = "red_flags"

    red_flag_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"))

    risk_type = Column(String(100))
    severity = Column(String(20))
    description = Column(String(500))
    document = relationship("Document", back_populates="red_flags")
class ComparisonResult(Base):
    __tablename__ = "comparison_results"

    comparison_id = Column(Integer, primary_key=True, index=True)

    company1_id = Column(Integer, ForeignKey("companies.company_id"))
    company2_id = Column(Integer, ForeignKey("companies.company_id"))

    comparison_summary = Column(String(1000))


class ResearchQuery(Base):
    __tablename__ = "research_queries"

    query_id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, ForeignKey("research_sessions.session_id"))

    question = Column(String(1000))
    answer = Column(String(3000))
    created_at = Column(DateTime, default=datetime.utcnow)
    research_session = relationship("ResearchSession", back_populates="queries")
class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, ForeignKey("research_sessions.session_id"))

    report_title = Column(String(200))
    report_path = Column(String(500))
    generated_at = Column(DateTime, default=datetime.utcnow)
    research_session = relationship("ResearchSession", back_populates="reports")