from backend.database.database import SessionLocal
from backend.database.models import (
    ResearchSession,
    Company,
    Document,
    FinancialMetric,
    RedFlag,
    ComparisonResult,
    ResearchQuery,
    Report
)

# Create Database Session
db = SessionLocal()


# -----------------------------------
# RESEARCH SESSION
# -----------------------------------

def create_research_session(session_name, description):

    session = ResearchSession(
        session_name=session_name,
        description=description
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_all_research_sessions():

    return db.query(ResearchSession).all()


def get_research_session(session_id):

    return db.query(ResearchSession).filter(
        ResearchSession.session_id == session_id
    ).first()


def update_research_session(session_id, new_name):

    session = db.query(ResearchSession).filter(
        ResearchSession.session_id == session_id
    ).first()

    if session:
        session.session_name = new_name
        db.commit()
        db.refresh(session)

    return session


def delete_research_session(session_id):

    session = db.query(ResearchSession).filter(
        ResearchSession.session_id == session_id
    ).first()

    if session:
        db.delete(session)
        db.commit()

    return session
# -----------------------------
# COMPANY CRUD
# -----------------------------

def create_company(db, company_name, industry, fiscal_year):
    company = Company(
        company_name=company_name,
        industry=industry,
        fiscal_year=fiscal_year
    )

    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def get_company(db, company_id):
    return db.query(Company).filter(
        Company.company_id == company_id
    ).first()


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




def create_document(db, session_id, company_id, file_name, file_path):
    document = Document(
        session_id=session_id,
        company_id=company_id,
        file_name=file_name,
        file_path=file_path
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document

def get_document(db, document_id):
    return db.query(Document).filter(
        Document.document_id == document_id
    ).first()


def get_all_documents(db):
    return db.query(Document).all()


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

def create_financial_metric(
    db,
    document_id,
    revenue,
    net_income,
    total_assets,
    total_liabilities,
    eps,
    debt_to_equity
):
    metric = FinancialMetric(
        document_id=document_id,
        revenue=revenue,
        net_income=net_income,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        eps=eps,
        debt_to_equity=debt_to_equity
    )

    db.add(metric)
    db.commit()
    db.refresh(metric)

    return metric


def get_financial_metric(db, metric_id):
    return db.query(FinancialMetric).filter(
        FinancialMetric.metric_id == metric_id
    ).first()


def get_all_financial_metrics(db):
    return db.query(FinancialMetric).all()


def update_financial_metric(db, metric_id, new_revenue):
    metric = get_financial_metric(db, metric_id)

    if metric:
        metric.revenue = new_revenue
        db.commit()
        db.refresh(metric)

    return metric


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
    red_flag = RedFlag(
        document_id=document_id,
        risk_type=risk_type,
        severity=severity,
        description=description
    )

    db.add(red_flag)
    db.commit()
    db.refresh(red_flag)

    return red_flag


def get_red_flag(db, red_flag_id):
    return db.query(RedFlag).filter(
        RedFlag.red_flag_id == red_flag_id
    ).first()


def get_all_red_flags(db):
    return db.query(RedFlag).all()


def update_red_flag(db, red_flag_id, new_severity):
    red_flag = get_red_flag(db, red_flag_id)

    if red_flag:
        red_flag.severity = new_severity
        db.commit()
        db.refresh(red_flag)

    return red_flag


def delete_red_flag(db, red_flag_id):
    red_flag = get_red_flag(db, red_flag_id)

    if red_flag:
        db.delete(red_flag)
        db.commit()

    return red_flag

# -----------------------------
# COMPARISON RESULT CRUD
# -----------------------------

def create_comparison_result(db, company1_id, company2_id, comparison_summary):
    comparison = ComparisonResult(
        company1_id=company1_id,
        company2_id=company2_id,
        comparison_summary=comparison_summary
    )

    db.add(comparison)
    db.commit()
    db.refresh(comparison)

    return comparison


def get_comparison_result(db, comparison_id):
    return db.query(ComparisonResult).filter(
        ComparisonResult.comparison_id == comparison_id
    ).first()


def get_all_comparison_results(db):
    return db.query(ComparisonResult).all()


def update_comparison_result(db, comparison_id, summary):
    comparison = get_comparison_result(db, comparison_id)

    if comparison:
        comparison.comparison_summary = summary
        db.commit()
        db.refresh(comparison)

    return comparison


def delete_comparison_result(db, comparison_id):
    comparison = get_comparison_result(db, comparison_id)

    if comparison:
        db.delete(comparison)
        db.commit()

    return comparison
# -----------------------------
# RESEARCH QUERY CRUD
# -----------------------------

def create_research_query(db, question, answer):
    query = ResearchQuery(
        question=question,
        answer=answer
    )

    db.add(query)
    db.commit()
    db.refresh(query)

    return query


def get_research_query(db, query_id):
    return db.query(ResearchQuery).filter(
        ResearchQuery.query_id == query_id
    ).first()


def get_all_research_queries(db):
    return db.query(ResearchQuery).all()


def update_research_query(db, query_id, new_answer):
    query = get_research_query(db, query_id)

    if query:
        query.answer = new_answer
        db.commit()
        db.refresh(query)

    return query


def delete_research_query(db, query_id):
    query = get_research_query(db, query_id)

    if query:
        db.delete(query)
        db.commit()

    return query

# -----------------------------
# REPORT CRUD
# -----------------------------

def create_report(db, session_id, report_title, report_path):
    report = Report(
        session_id=session_id,
        report_title=report_title,
        report_path=report_path
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


def get_report(db, report_id):
    return db.query(Report).filter(
        Report.report_id == report_id
    ).first()


def get_all_reports(db):
    return db.query(Report).all()


def update_report(db, report_id, new_title):
    report = get_report(db, report_id)

    if report:
        report.report_title = new_title
        db.commit()
        db.refresh(report)

    return report


def delete_report(db, report_id):
    report = get_report(db, report_id)

    if report:
        db.delete(report)
        db.commit()

    return report