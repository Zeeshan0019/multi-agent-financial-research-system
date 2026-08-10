from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from datetime import datetime
from backend.database.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    password_salt = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="user")
    queries = relationship("ResearchQuery", back_populates="user")
    reports = relationship("Report", back_populates="user")
    comparisons = relationship("ComparisonResult", back_populates="user")

class UserToken(Base):
    __tablename__ = "user_tokens"

    token = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.company_id"))

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="documents")
    company = relationship("Company", back_populates="documents")

    financial_metrics = relationship("FinancialMetric", back_populates="document")
    red_flags = relationship("RedFlag", back_populates="document")

class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    metric_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"))

    revenue = Column(Float)
    net_income = Column(Float)
    ebitda = Column(Float)
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
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    company1_id = Column(Integer, ForeignKey("companies.company_id"))
    company2_id = Column(Integer, ForeignKey("companies.company_id"))
    comparison_summary = Column(String(1000))

    user = relationship("User", back_populates="comparisons")

class ResearchQuery(Base):
    __tablename__ = "research_queries"

    query_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=True)
    question = Column(String(2000))
    answer = Column(String(8000))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="queries")

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    report_title = Column(String(200))
    report_path = Column(String(500))
    generated_at = Column(DateTime, default=datetime.utcnow)
    document_ids = Column(String(500))
    status = Column(String(20), default="ready")
    pages = Column(Integer)
    sections = Column(String(500))
    
    user = relationship("User", back_populates="reports")