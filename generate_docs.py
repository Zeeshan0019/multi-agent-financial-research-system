from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime

OUTPUT = "Multi-Agent-Financial-Research-System-Documentation.pdf"

doc = SimpleDocTemplate(
    OUTPUT, pagesize=LETTER,
    leftMargin=0.9*inch, rightMargin=0.9*inch,
    topMargin=0.9*inch, bottomMargin=0.9*inch,
    title="Multi-Agent Financial Research System — Technical Documentation"
)

styles = getSampleStyleSheet()

# Custom styles
styles.add(ParagraphStyle("DocTitle",    fontName="Helvetica-Bold",   fontSize=26, leading=32, textColor=colors.HexColor("#1E1B3C"), spaceAfter=6,  alignment=TA_CENTER))
styles.add(ParagraphStyle("DocSubtitle",fontName="Helvetica",         fontSize=12, leading=16, textColor=colors.HexColor("#7C3AED"), spaceAfter=4,  alignment=TA_CENTER))
styles.add(ParagraphStyle("DocMeta",    fontName="Helvetica",         fontSize=9,  leading=12, textColor=colors.HexColor("#94A3B8"), spaceAfter=2,  alignment=TA_CENTER))
styles.add(ParagraphStyle("H1",         fontName="Helvetica-Bold",    fontSize=16, leading=20, textColor=colors.HexColor("#1E1B3C"), spaceBefore=18,spaceAfter=6))
styles.add(ParagraphStyle("H2",         fontName="Helvetica-Bold",    fontSize=12, leading=16, textColor=colors.HexColor("#7C3AED"), spaceBefore=12,spaceAfter=4))
styles.add(ParagraphStyle("H3",         fontName="Helvetica-Bold",    fontSize=10, leading=14, textColor=colors.HexColor("#0D9488"), spaceBefore=8, spaceAfter=3))
styles.add(ParagraphStyle("Body",       fontName="Helvetica",         fontSize=9.5,leading=14, textColor=colors.HexColor("#334155"), spaceAfter=6,  alignment=TA_JUSTIFY))
styles.add(ParagraphStyle("Bullet",     fontName="Helvetica",         fontSize=9.5,leading=14, textColor=colors.HexColor("#334155"), spaceAfter=3,  leftIndent=16, firstLineIndent=-12))
styles.add(ParagraphStyle("Code",       fontName="Courier",           fontSize=8.5,leading=12, textColor=colors.HexColor("#1E293B"), spaceAfter=6,  leftIndent=12, backColor=colors.HexColor("#F8FAFC")))
styles.add(ParagraphStyle("Eyebrow",    fontName="Helvetica-Bold",    fontSize=7.5,leading=10, textColor=colors.HexColor("#7C3AED"), spaceAfter=2,  alignment=TA_LEFT, letterSpacing=1.5))
styles.add(ParagraphStyle("Caption",    fontName="Helvetica-Oblique", fontSize=8,  leading=11, textColor=colors.HexColor("#94A3B8"), spaceAfter=8,  alignment=TA_CENTER))

ACCENT  = colors.HexColor("#7C3AED")
TEAL    = colors.HexColor("#0D9488")
ROSE    = colors.HexColor("#E11D48")
AMBER   = colors.HexColor("#D97706")
SLATE   = colors.HexColor("#F8FAFC")
BORDER  = colors.HexColor("#E2E8F0")

def hr(color=BORDER, thickness=0.5): return HRFlowable(width="100%", color=color, thickness=thickness, spaceAfter=6, spaceBefore=6)
def h1(t): return Paragraph(t, styles["H1"])
def h2(t): return Paragraph(t, styles["H2"])
def h3(t): return Paragraph(t, styles["H3"])
def body(t): return Paragraph(t, styles["Body"])
def bullet(t): return Paragraph(f"&#8226;  {t}", styles["Bullet"])
def code(t): return Paragraph(t, styles["Code"])
def eyebrow(t): return Paragraph(t.upper(), styles["Eyebrow"])
def sp(n=1): return Spacer(1, n*6)

def agent_header(name, color, tagline):
    tbl = Table([[Paragraph(f"<b>{name}</b>", ParagraphStyle("AH", fontName="Helvetica-Bold", fontSize=13, textColor=colors.white)),
                  Paragraph(tagline, ParagraphStyle("AT", fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#E2E8F0"), alignment=1))]],
                colWidths=[2.5*inch, 4.1*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), color),
        ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(0,-1),14), ("RIGHTPADDING",(-1,0),(-1,-1),14),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    return tbl

def info_table(rows):
    data = [[Paragraph(f"<b>{k}</b>", ParagraphStyle("IK", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#475569"))),
             Paragraph(v, ParagraphStyle("IV", fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#1E293B")))]
            for k, v in rows]
    t = Table(data, colWidths=[1.8*inch, 4.8*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1), SLATE),
        ("GRID",(0,0),(-1,-1),0.4, BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, SLATE]),
    ]))
    return t

story = []

# ── COVER PAGE ─────────────────────────────────────────────────────────────
cover_banner = Table([[
    Paragraph("<b>MULTI-AGENT FINANCIAL RESEARCH SYSTEM</b>",
              ParagraphStyle("CB", fontName="Helvetica-Bold", fontSize=7, textColor=colors.HexColor("#C4B5FD"), letterSpacing=2)),
]], colWidths=[6.6*inch])
cover_banner.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#1E1B3C")),
    ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
    ("LEFTPADDING",(0,0),(-1,-1),14), ("ALIGN",(0,0),(-1,-1),"CENTER"),
]))
story += [cover_banner, sp(4),
          Paragraph("Technical Documentation", styles["DocTitle"]),
          Paragraph("Architecture, Agent Design &amp; Implementation Guide", styles["DocSubtitle"]),
          sp(2),
          Paragraph(f"Project: Infosys Internship — Vidzai Digital", styles["DocMeta"]),
          Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles["DocMeta"]),
          Paragraph("Stack: Python 3.13 · FastAPI · React 18 · FAISS · Groq LLM · ReportLab", styles["DocMeta"]),
          sp(3), hr(ACCENT, 1.5), sp(3)]

# Quick summary table
story += [eyebrow("System at a Glance"), sp(1)]
summary = Table([
    ["Total Agents", "6", "Backend Framework", "FastAPI (Python 3.13)"],
    ["Frontend", "React 18 + Vite", "LLM Provider", "Groq (llama-3.3-70b-versatile)"],
    ["Vector DB", "FAISS (CPU)", "Embeddings", "all-MiniLM-L6-v2 (HuggingFace)"],
    ["Relational DB", "SQLite + SQLAlchemy", "PDF Generation", "ReportLab"],
    ["Auth", "Bearer Token (secrets)", "Frontend Port", "localhost:5173"],
    ["Backend Port", "localhost:8080", "API Docs", "localhost:8080/docs"],
], colWidths=[1.5*inch, 1.8*inch, 1.7*inch, 1.6*inch])
summary.setStyle(TableStyle([
    ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"), ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
    ("FONTNAME",(1,0),(1,-1),"Helvetica"),      ("FONTNAME",(3,0),(3,-1),"Helvetica"),
    ("FONTSIZE",(0,0),(-1,-1),8.5),
    ("TEXTCOLOR",(0,0),(0,-1), colors.HexColor("#475569")),
    ("TEXTCOLOR",(2,0),(2,-1), colors.HexColor("#475569")),
    ("TEXTCOLOR",(1,0),(1,-1), colors.HexColor("#1E293B")),
    ("TEXTCOLOR",(3,0),(3,-1), colors.HexColor("#1E293B")),
    ("GRID",(0,0),(-1,-1),0.4, BORDER),
    ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, SLATE]),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),8),
]))
story += [summary, PageBreak()]

# ── SECTION 1: OVERVIEW ────────────────────────────────────────────────────
story += [h1("1. Project Overview"), hr(),
body("The Multi-Agent Financial Research System is a full-stack AI platform built for Infosys Interns at Vidzai Digital. Finance students, MBA candidates, and early-career analysts struggle with the time-consuming task of reading lengthy annual reports and financial filings. This system solves that by deploying a coordinated team of six specialized AI agents that automatically parse, extract, analyze, and report on any uploaded financial document."),
sp(1),
body("When a user uploads a PDF annual report or 10-K filing, a four-stage pipeline triggers automatically in the background — the document is parsed and indexed, key financial metrics are extracted using a Groq LLM, risk anomalies are detected by a rule engine, and the results are stored in a structured database ready for querying, comparison, and report generation."),
sp(1),
eyebrow("Key Capabilities"), sp(1),
bullet("Upload any PDF financial filing (annual report, 10-K, earnings transcript)"),
bullet("Automatic extraction of 7 financial metrics: Revenue, Net Profit, EBITDA, EPS, Total Assets, Total Liabilities, Debt/Equity"),
bullet("Automatic detection of financial red flags: leverage risk, margin compression, going concern warnings, material weaknesses, legal contingencies"),
bullet("Conversational Q&A grounded strictly in uploaded documents with page-level citations"),
bullet("Side-by-side benchmarking of financial metrics across multiple companies"),
bullet("Structured analyst-style PDF report export covering 5 sections"),
bullet("JWT-style Bearer token authentication with per-user data isolation"),
sp(2)]

# ── SECTION 2: ARCHITECTURE ────────────────────────────────────────────────
story += [h1("2. System Architecture"), hr(),
body("The system follows a layered architecture: a React frontend communicates with a FastAPI backend over a REST API authenticated with Bearer tokens. On the backend, six specialized agents are orchestrated — three run automatically on document upload (Document, Extraction, Red Flag), and three are invoked on demand (Research, Comparison, Report)."),
sp(1), eyebrow("Architecture Layers"), sp(1)]

arch = Table([
    ["Layer", "Technology", "Responsibility"],
    ["Presentation", "React 18 + Vite + Tailwind CSS", "Dashboard, Upload, Research, Comparison, Reports pages"],
    ["API Gateway", "FastAPI + Uvicorn (port 8080)", "REST endpoints, CORS, Bearer auth, background tasks"],
    ["Agent Layer", "LangChain + LangGraph + Groq", "Six specialized agents coordinated by main.py"],
    ["Vector Store", "FAISS-CPU + HuggingFace Embeddings", "Per-document semantic search indexes at vector_store/doc_{id}/"],
    ["Relational DB", "SQLite + SQLAlchemy ORM", "Users, documents, metrics, red flags, queries, reports"],
    ["LLM Inference", "Groq API (llama-3.3-70b-versatile)", "Extraction, Research Agent Q&A, Red Flag qualitative analysis"],
    ["PDF Output", "ReportLab", "Analyst-style 5-section PDF research reports"],
], colWidths=[1.3*inch, 2.2*inch, 3.1*inch])
arch.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#1E1B3C")),
    ("TEXTCOLOR",(0,0),(-1,0), colors.white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
    ("FONTSIZE",(0,0),(-1,-1),8.5),
    ("GRID",(0,0),(-1,-1),0.4, BORDER),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, SLATE]),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),8), ("VALIGN",(0,0),(-1,-1),"TOP"),
]))
story += [arch, sp(2),
eyebrow("Document Upload Pipeline (Auto-triggered)"), sp(1),
body("Step 1 (Document Agent): PDF text extraction using PyMuPDF, chunking into 1000-char overlapping segments, HuggingFace embedding generation, FAISS index creation at vector_store/doc_{id}/."),
body("Step 2 (Extraction Agent): Groq LLM (LangGraph pipeline) reads the PDF bytes and extracts revenue, net income, EBITDA, EPS, assets, liabilities, debt/equity. Results saved to financial_metrics table."),
body("Step 3 (Red Flag Agent): Deterministic rule engine analyzes extracted metrics against 8 risk categories. LLM qualitative scan supplements for nuanced findings. Results saved to red_flags table."),
body("Step 4: DOCUMENT_STATUS[id] set to 'ready'. Frontend polls every 3 seconds and updates the Dashboard automatically."),
PageBreak()]

# ── SECTION 3: AGENT 1 — DOCUMENT AGENT ───────────────────────────────────
story += [agent_header("Agent 1 — Document Agent", colors.HexColor("#5A4BB0"), "Parses, chunks, embeds and indexes every uploaded PDF"), sp(2),
eyebrow("Purpose"), body("The Document Agent is the entry point of the pipeline. It converts a raw PDF file into a searchable vector index that all other agents can query. Every chunk of text is stored with metadata (company name, page number, document ID) so the Research Agent can provide exact page citations."),
sp(1), eyebrow("How It Works"), sp(1),
info_table([
    ("File", "backend/document Agent/document_agent.py"),
    ("Triggered by", "POST /documents — runs as FastAPI BackgroundTask immediately after upload"),
    ("PDF Parsing", "PyMuPDF (fitz) extracts text layer from all pages. Falls back to pytesseract OCR for scanned/image-based pages"),
    ("Chunking", "RecursiveCharacterTextSplitter: chunk_size=1000, chunk_overlap=150, separators=[newline, period, space]"),
    ("Embeddings", "HuggingFaceEmbeddings: sentence-transformers/all-MiniLM-L6-v2 (384-dim vectors, lazy-loaded on first use)"),
    ("Vector Store", "FAISS-CPU index saved to project/vector_store/doc_{document_id}/ (index.faiss + index.pkl)"),
    ("Metadata per chunk", "document_id, company_name, file_name, page_number, source (text_layer or ocr)"),
    ("Company detection", "Priority: PDF metadata title → first-page legal entity regex → filename stem cleanup"),
    ("Output", "ProcessResult(chunks_indexed=N, warnings=[...]) + Company row created in DB"),
]),
sp(1), eyebrow("Configuration"), sp(1),
code("CHUNK_SIZE = 1000  |  CHUNK_OVERLAP = 150  |  EMBEDDING_MODEL = sentence-transformers/all-MiniLM-L6-v2"),
sp(1), eyebrow("Key Design Decision"),
body("Embeddings are loaded lazily — the model is not loaded at server startup, only on the first document upload or first chat query. This keeps the server startup time under 3 seconds."),
sp(2)]

# ── SECTION 4: AGENT 2 — EXTRACTION AGENT ─────────────────────────────────
story += [agent_header("Agent 2 — Extraction Agent", TEAL, "Pulls key financial metrics from documents using Groq LLM"), sp(2),
eyebrow("Purpose"),
body("The Extraction Agent reads the uploaded PDF and extracts 7 standardized financial metrics using a LangGraph pipeline powered by the Groq LLM. These metrics are stored in the database and shown on the Dashboard Extraction Agent Output panel."),
sp(1), eyebrow("How It Works"), sp(1),
info_table([
    ("File", "backend/Extraction agent/Extraction agent.py"),
    ("Triggered by", "Called by process_document_pipeline() after Document Agent completes"),
    ("LLM", "Groq API: llama-3.3-70b-versatile via LangGraph multi-node pipeline"),
    ("Pipeline nodes", "1. Document Loader → 2. Chunk Processor → 3. LLM Extraction → 4. Merge Chunk Results → 5. Validate JSON → 6. Confidence Calculation → 7. Response Formatter"),
    ("Metrics extracted", "Revenue, Net Income / Net Profit, EBITDA, EPS (Earnings Per Share), Total Assets, Total Liabilities, Debt-to-Equity Ratio"),
    ("Fallback", "If LLM extraction fails: regex scan of PDF text for numeric values near financial keywords (revenue, net income, EBITDA, etc.)"),
    ("Result mapping", "Nested response fields (normalized_value, value, raw_value) mapped to FinancialMetric ORM model"),
    ("DB Table", "financial_metrics: metric_id, document_id, revenue, net_income, ebitda, total_assets, total_liabilities, eps, debt_to_equity"),
    ("API endpoint", "GET /documents/{id}/metrics → returns highlights array with label, value, delta, tone"),
]),
sp(1), eyebrow("Metrics Displayed on Dashboard"),
Table([["Metric", "Field in DB", "Example Value"],
       ["Revenue", "revenue", "98,450.00"],
       ["Net Profit", "net_income", "14,230.00"],
       ["EBITDA", "ebitda", "22,922.00"],
       ["EPS", "eps", "38.14"],
       ["Total Assets", "total_assets", "93,200.00"],
       ["Total Liabilities", "total_liabilities", "30,160.00"],
       ["Debt/Equity", "debt_to_equity", "0.32x"],
], colWidths=[1.8*inch, 2.0*inch, 2.8*inch],
).setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0), TEAL), ("TEXTCOLOR",(0,0),(-1,0), colors.white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
    ("FONTSIZE",(0,0),(-1,-1),8.5), ("GRID",(0,0),(-1,-1),0.4, BORDER),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,SLATE]),
    ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ("LEFTPADDING",(0,0),(-1,-1),8),
])),
sp(2), PageBreak()]

# ── SECTION 5: AGENT 3 — RED FLAG AGENT ───────────────────────────────────
story += [agent_header("Agent 3 — Red Flag Agent", ROSE, "Scans for financial anomalies, risk patterns and audit warnings"), sp(2),
eyebrow("Purpose"),
body("The Red Flag Agent automatically surfaces financial warning signals from the uploaded document without any user prompting. It combines a deterministic rule engine for quantitative checks with an LLM qualitative scan for nuanced risk language. Results appear on the Dashboard under 'Red Flag Agent Findings'."),
sp(1), eyebrow("How It Works"), sp(1),
info_table([
    ("File", "backend/Red Flag Agent/redflag_agent.py"),
    ("Triggered by", "Called automatically after Extraction Agent, within process_document_pipeline()"),
    ("Framework", "LangGraph workflow with RuleEngine + LLM qualitative analysis + EvidenceGrounder"),
    ("Rule engine", "Deterministic rules check 8 risk categories against extracted metric values"),
    ("LLM scan", "Groq LLM analyzes text chunks for qualitative risk language (auditor qualifications, going concern, material weakness, etc.)"),
    ("Severity levels", "HIGH (immediate concern) | MEDIUM (watch item) | LOW (minor note)"),
    ("DB Table", "red_flags: red_flag_id, document_id, risk_type, severity, description"),
    ("API endpoint", "GET /documents/{id}/red-flags → returns array of {severity, title, detail, citation}"),
]),
sp(1), eyebrow("8 Risk Categories Checked"), sp(1),
Table([
    ["Risk Category", "Severity", "Trigger Condition"],
    ["Operating Margin Compression", "HIGH", "Operating margin declining for 3+ consecutive years"],
    ["High Leverage Ratio", "HIGH", "Debt-to-equity ratio > 1.5x"],
    ["Declining Free Cash Flow", "MEDIUM", "FCF declining for 3+ consecutive years"],
    ["Dividend Payout Exceeds FCF", "MEDIUM", "Dividends paid > free cash flow generated"],
    ["Going Concern Risk", "HIGH", "Keywords: 'going concern', 'ability to continue'"],
    ["Material Weakness", "HIGH", "Keywords: 'material weakness', 'internal controls'"],
    ["Legal Contingency Risk", "MEDIUM", "Keywords: 'litigation', 'lawsuit', 'legal proceedings'"],
    ["Working Capital Deterioration", "MEDIUM", "DSO increasing for 4+ consecutive years"],
], colWidths=[2.2*inch, 1.0*inch, 3.4*inch]
).setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0), ROSE), ("TEXTCOLOR",(0,0),(-1,0), colors.white),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
    ("FONTSIZE",(0,0),(-1,-1),8.5), ("GRID",(0,0),(-1,-1),0.4, BORDER),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,SLATE]),
    ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ("LEFTPADDING",(0,0),(-1,-1),8), ("VALIGN",(0,0),(-1,-1),"TOP"),
])),
sp(2)]

# ── SECTION 6: AGENT 4 — RESEARCH AGENT ───────────────────────────────────
story += [agent_header("Agent 4 — Research Agent", colors.HexColor("#5A4BB0"), "Conversational Q&A grounded strictly in uploaded filings"), sp(2),
eyebrow("Purpose"),
body("The Research Agent allows users to ask multi-part financial questions in natural language and receive step-by-step reasoned answers with exact page-level citations. Every answer is strictly grounded in the FAISS vector index of the uploaded documents — the agent never generates information beyond what the documents contain."),
sp(1), eyebrow("How It Works"), sp(1),
info_table([
    ("File", "backend/research_agent/research_agent.py"),
    ("Triggered by", "POST /chat { query, document_id? } — on-demand, called when user asks a question"),
    ("Step 1: Retrieval", "FAISS similarity_search_with_score() on vector_store/doc_{id}/ — returns top-k=4 most relevant chunks"),
    ("Step 2: Ranking", "Chunks sorted by FAISS L2 distance score (lower = more similar)"),
    ("Step 3: Context building", "Top chunks formatted as: [Doc N | Page P | Company]: text"),
    ("Step 4: LLM generation", "Groq llama-3.3-70b-versatile generates answer using ONLY the provided context. System prompt enforces strict grounding."),
    ("Step 5: Citations", "Each chunk that contributed to the answer is returned as a citation with document_id and page number"),
    ("Document scope", "User selects a specific document OR queries across all their indexed documents simultaneously"),
    ("Fallback (no Groq)", "Local heuristic responder extracts relevant sentences from chunks based on query keywords"),
    ("DB persistence", "Every Q&A saved to research_queries table for chat history"),
    ("API endpoint", "GET /chat (history) | POST /chat (ask)"),
]),
sp(1), eyebrow("Why Research Agent is More Accurate Than Dashboard Metrics"),
body("The Research Agent reads directly from the FAISS vector store which contains exact text from the PDF. The Dashboard metrics come from the SQL database (financial_metrics table) which stores values extracted and mapped during the pipeline. If the LLM extraction mapping was incomplete, the dashboard shows partial values while the Research Agent can still find the correct figures by searching the raw text."),
sp(2), PageBreak()]
