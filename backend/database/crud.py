"""
CRUD helpers for the Multi-Agent Financial Research System.
ResearchSession has been removed — all data is scoped to authenticated users.
"""
from backend.database.database import SessionLocal
from backend.database.models import (
    Company,
    Document,
    FinancialMetric,
    RedFlag,
    ComparisonResult,
    ResearchQuery,
    Report,
)

# Shared module-level session (convenience for scripts; prefer per-request sessions in FastAPI routes)
db = SessionLocal()

# -----------------------------
# COMPANY CRUD
# -----------------------------

def create_company(db, company_name, industry, fiscal_year):
    company = Company(company_name=company_name, industry=industry, fiscal_year=fiscal_year)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def get_company(db, company_id):
    return db.query(Company).filter(Company.company_id == company_id).first()


def get_all_companies(db):
    return db.query(Company).all()


def update_company(db, company_id, name):
    company = get_company(db, company_id)
    if company:
        company.company_name = name
        db.commit()
    return company


def delete_company(db, company_id):
    company = get_company(db, company_id)
    if company:
        db.delete(company)
        db.commit()
    return company


# -----------------------------
# DOCUMENT CRUD
# -----------------------------

def create_document(db, user_id, company_id, file_name, file_path):
    document = Document(user_id=user_id, company_id=company_id, file_name=file_name, file_path=file_path)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document(db, document_id):
    return db.query(Document).filter(Document.document_id == document_id).first()


def get_all_documents(db):
    return db.query(Document).all()


def get_documents_by_user(db, user_id):
    return db.query(Document).filter(Document.user_id == user_id).all()


def update_document(db, document_id, new_name):
    document = get_document(db, document_id)
    if document:
        document.file_name = new_name
        db.commit()
    return document


def delete_document(db, document_id):
    document = get_document(db, document_id)
    if document:
        db.delete(document)
        db.commit()
    return document


# -----------------------------
# FINANCIAL METRIC CRUD
# -----------------------------

def create_financial_metric(db, document_id, revenue, net_income, ebitda, total_assets, total_liabilities, eps, debt_to_equity):
    metric = FinancialMetric(
        document_id=document_id,
        revenue=revenue,
        net_income=net_income,
        ebitda=ebitda,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        eps=eps,
        debt_to_equity=debt_to_equity,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def get_financial_metric(db, metric_id):
    return db.query(FinancialMetric).filter(FinancialMetric.metric_id == metric_id).first()


def get_metrics_by_document(db, document_id):
    return db.query(FinancialMetric).filter(FinancialMetric.document_id == document_id).first()


def delete_financial_metric(db, metric_id):
    metric = get_financial_metric(db, metric_id)
    if metric:
        db.delete(metric)
        db.commit()
    return metric


# -----------------------------
# RED FLAG CRUD
# -----------------------------

def create_red_flag(db, document_id, risk_type, severity, description):
    red_flag = RedFlag(document_id=document_id, risk_type=risk_type, severity=severity, description=description)
    db.add(red_flag)
    db.commit()
    db.refresh(red_flag)
    return red_flag


def get_red_flag(db, red_flag_id):
    return db.query(RedFlag).filter(RedFlag.red_flag_id == red_flag_id).first()


def get_red_flags_by_document(db, document_id):
    return db.query(RedFlag).filter(RedFlag.document_id == document_id).all()


def delete_red_flag(db, red_flag_id):
    red_flag = get_red_flag(db, red_flag_id)
    if red_flag:
        db.delete(red_flag)
        db.commit()
    return red_flag


# -----------------------------
# COMPARISON RESULT CRUD
# -----------------------------

def create_comparison_result(db, user_id, company1_id, company2_id, comparison_summary):
    comparison = ComparisonResult(
        user_id=user_id,
        company1_id=company1_id,
        company2_id=company2_id,
        comparison_summary=comparison_summary,
    )
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return comparison


def get_comparison_result(db, comparison_id):
    return db.query(ComparisonResult).filter(ComparisonResult.comparison_id == comparison_id).first()


def delete_comparison_result(db, comparison_id):
    comparison = get_comparison_result(db, comparison_id)
    if comparison:
        db.delete(comparison)
        db.commit()
    return comparison


# -----------------------------
# RESEARCH QUERY CRUD
# -----------------------------

def create_research_query(db, user_id, document_id, question, answer):
    query = ResearchQuery(user_id=user_id, document_id=document_id, question=question, answer=answer)
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


def get_research_query(db, query_id):
    return db.query(ResearchQuery).filter(ResearchQuery.query_id == query_id).first()


def get_queries_by_user(db, user_id):
    return db.query(ResearchQuery).filter(ResearchQuery.user_id == user_id).all()


def delete_research_query(db, query_id):
    query = get_research_query(db, query_id)
    if query:
        db.delete(query)
        db.commit()
    return query


# -----------------------------
# REPORT CRUD
# -----------------------------

def create_report(db, user_id, report_title, report_path, document_ids, sections):
    report = Report(
        user_id=user_id,
        report_title=report_title,
        report_path=report_path,
        document_ids=document_ids,
        sections=sections,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db, report_id):
    return db.query(Report).filter(Report.report_id == report_id).first()


def get_reports_by_user(db, user_id):
    return db.query(Report).filter(Report.user_id == user_id).all()


def delete_report(db, report_id):
    report = get_report(db, report_id)
    if report:
        db.delete(report)
        db.commit()
    return report
