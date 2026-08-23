# Multi-Agent Financial Research System

A full-stack AI platform where a team of specialized agents collaborate to read, analyze, and generate insights from real company financial documents. Upload any PDF annual report, 10-K, or earnings filing and the system automatically extracts metrics, detects red flags, enables conversational research, benchmarks companies side-by-side, and compiles a structured analyst-style PDF report.

Built for Infosys Interns — Vidzai Digital.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│   Dashboard │ Upload │ Research │ Comparison │ Reports          │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API (Bearer token auth)
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend (port 8080)                   │
│                                                                  │
│  ┌──────────────┐  ┌─────────────────┐  ┌───────────────────┐  │
│  │ Document     │  │ Extraction      │  │ Red Flag          │  │
│  │ Agent        │  │ Agent           │  │ Agent             │  │
│  │              │  │                 │  │                   │  │
│  │ PDF parse    │  │ Groq LLM        │  │ LangGraph +       │  │
│  │ Chunk+embed  │  │ metric extract  │  │ Rule engine       │  │
│  │ FAISS index  │  │ revenue/EPS/etc │  │ 8 risk categories │  │
│  └──────┬───────┘  └────────┬────────┘  └─────────┬─────────┘  │
│         │                   │                      │            │
│  ┌──────▼───────────────────▼──────────────────────▼─────────┐ │
│  │               SQLite Database (SQLAlchemy ORM)             │ │
│  │  users │ documents │ financial_metrics │ red_flags │ ...   │ │
│  └──────┬──────────────────────────────────────────┬─────────┘ │
│         │                                          │            │
│  ┌──────▼───────┐                        ┌─────────▼─────────┐ │
│  │ Research     │                        │ Comparison +       │ │
│  │ Agent        │                        │ Report Agent       │ │
│  │              │                        │                    │ │
│  │ FAISS search │                        │ Cross-doc metrics  │ │
│  │ Groq LLM Q&A │                        │ ReportLab PDF      │ │
│  │ Citations    │                        │ 5-section brief    │ │
│  └──────────────┘                        └────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agents

| Agent | Responsibility |
|---|---|
| **Document Agent** | Parses PDF (text layer + OCR fallback), chunks content, generates HuggingFace embeddings, indexes into per-document FAISS store |
| **Extraction Agent** | Uses Groq LLM (LangGraph pipeline) to pull revenue, net income, EBITDA, EPS, assets, liabilities, debt/equity from the filing |
| **Red Flag Agent** | Runs a deterministic rule engine + LLM qualitative scan to surface high/medium/low risk anomalies: leverage, margin compression, going concern, material weakness, litigation |
| **Research Agent** | FAISS semantic search across indexed documents → Groq LLM generates grounded answers with page-level citations |
| **Comparison Agent** | Cross-references extracted `FinancialMetric` rows across 2+ documents, computes margins and ratios, returns ranked results |
| **Report Agent** | Compiles outputs of all agents into a 5-section analyst-style PDF via ReportLab: Executive Summary, Key Financials, Red Flags, Comparison, Outlook |

---

## Tech Stack

**Backend**
- Python 3.13 · FastAPI · Uvicorn
- SQLAlchemy ORM · SQLite
- PyMuPDF (fitz) — PDF text extraction
- LangChain + LangGraph — agent orchestration
- FAISS-CPU — vector similarity search
- HuggingFace sentence-transformers (`all-MiniLM-L6-v2`) — embeddings
- Groq API (`llama-3.3-70b-versatile`) — LLM inference
- ReportLab — PDF report generation
- python-dotenv — environment config

**Frontend**
- React 18 · Vite · React Router v6
- Axios — HTTP client with Bearer auth interceptors
- Tailwind CSS v3 — custom design system (ledger/parchment/flag scales)
- Space Grotesk · Inter · JetBrains Mono — typography

---

## Project Structure

```
project/
├── .env                          # GROQ_API_KEY (never commit to git)
├── backend/
│   ├── main.py                   # FastAPI app — all endpoints + pipeline orchestration
│   ├── database/
│   │   ├── database.py           # SQLAlchemy engine + SessionLocal
│   │   ├── models.py             # ORM models: User, Document, FinancialMetric, RedFlag, ...
│   │   ├── crud.py               # CRUD helpers
│   │   ├── init_db.py            # One-time table creation script
│   │   └── financial_research.db # SQLite database (auto-created)
│   ├── document Agent/
│   │   └── document_agent.py     # PDF parse → chunk → embed → FAISS index
│   ├── Extraction agent/
│   │   └── Extraction agent.py   # LangGraph + Groq metric extraction
│   ├── Red Flag Agent/
│   │   └── redflag_agent.py      # Rule engine + LLM risk scanner
│   ├── research_agent/
│   │   └── research_agent.py     # FAISS retrieval + Groq Q&A
│   ├── comparison_agent/
│   │   └── comparison_agent.py   # Cross-document metric benchmarking
│   └── report_agent/
│       └── report_agent.py       # ReportLab PDF generator
├── frontend/
│   ├── .env                      # VITE_API_BASE_URL=http://localhost:8080
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx              # React entry — AuthProvider wraps App
│       ├── App.jsx               # Route guard: PublicRoutes / PrivateRoutes
│       ├── context/
│       │   ├── AuthContext.jsx   # Token boot check, logIn, signUp, logOut
│       │   └── DocumentsContext.jsx  # Global document state + 3s polling
│       ├── api/
│       │   ├── client.js         # Axios instance + Bearer interceptor
│       │   ├── auth.js           # signUp, logIn, getMe
│       │   ├── documents.js      # CRUD + metrics + red flags
│       │   ├── chat.js           # getChatHistory, askResearchAgent
│       │   ├── comparison.js     # compareDocuments
│       │   └── reports.js        # listReports, generateReport, getReport
│       ├── components/
│       │   ├── Layout.jsx        # Sidebar nav + user info + logout
│       │   ├── ChatBubble.jsx    # UserBubble, AssistantBubble, ThinkingBubble
│       │   ├── MetricCard.jsx    # Single extracted metric display
│       │   ├── RiskBadge.jsx     # High / medium / low severity pill
│       │   ├── Citation.jsx      # Inline source citation popup
│       │   ├── CountUp.jsx       # Animated number counter
│       │   └── PageHeader.jsx    # Eyebrow + title + description
│       └── pages/
│           ├── SignIn.jsx        # Login form
│           ├── SignUp.jsx        # Registration form
│           ├── Dashboard.jsx     # Coverage overview + expandable agent output rows
│           ├── Upload.jsx        # Drag-and-drop PDF upload + pipeline animation
│           ├── Research.jsx      # Chat interface with document selector
│           ├── Comparison.jsx    # Side-by-side metric benchmarking
│           └── Reports.jsx       # Report builder + viewer modal + PDF download
└── uploads/                      # Uploaded PDFs (auto-created, per-user subdirs)
├── vector_store/                 # FAISS indexes (auto-created, per-document)
└── reports/                      # Generated PDFs (auto-created, per-user subdirs)
```

---

## Prerequisites

- Python 3.10+ with pip
- Node.js 18+ with npm
- A free [Groq API key](https://console.groq.com) for LLM inference

---

## Setup & Installation

### 1. Clone / extract the project

```bash
cd project
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
pip install fastapi uvicorn sqlalchemy pymupdf sentence-transformers faiss-cpu \
    reportlab langchain langchain-community langchain-groq langgraph \
    python-dotenv python-multipart
```

### 3. Create the environment file

Create `project/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

### 5. Confirm frontend API URL

`frontend/.env` should contain:

```env
VITE_API_BASE_URL=http://localhost:8080
```

---

## Running the Application

Open **two terminals** from the `project/` directory.

**Terminal 1 — Backend:**

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173) in your browser.

> The backend starts in ~3 seconds. The HuggingFace embedding model loads lazily on the first document query, not at startup.

---

## Usage Guide

### 1. Create an account
Go to [http://localhost:5173/signup](http://localhost:5173/signup), enter a username and password (min 4 chars).

### 2. Upload a financial document
- Navigate to **Upload** in the sidebar
- Drag and drop any PDF annual report, 10-K, or earnings filing
- Watch the 4-stage pipeline animate: Document Agent → Document Agent (indexing) → Extraction Agent → Red Flag Agent
- Click **View in Dashboard** when done

### 3. View extracted insights
- On the **Dashboard**, click any row with status **READY** to expand it
- The **Extraction Agent** output shows key financial metrics (revenue, EBITDA, EPS, etc.)
- The **Red Flag Agent** output lists risk anomalies with severity badges

### 4. Ask research questions
- Navigate to **Research**
- Select a document from the dropdown (or leave on "All documents" to search across all)
- Type any financial question: *"What were the main risk factors?"*, *"How did margins trend?"*
- The Research Agent retrieves relevant chunks from the FAISS index and answers using Groq LLM with citations

### 5. Compare companies
- Upload at least 2 documents
- Navigate to **Comparison**
- Select 2+ companies and a financial metric
- Click **Benchmark** to see a side-by-side bar chart with a narrative summary

### 6. Generate a report
- Navigate to **Reports**
- Select documents to include and toggle report sections
- Click **Compile Research Report**
- Click **View Report** to browse the in-app viewer or **Download PDF** for the ReportLab-generated PDF

---

## API Reference

All endpoints require a `Bearer <token>` header except `/auth/signup` and `/auth/login`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/signup` | Create account, returns `{ token, username }` |
| `POST` | `/auth/login` | Authenticate, returns `{ token, username }` |
| `GET` | `/auth/me` | Returns current user profile |
| `GET` | `/documents` | List all documents for authenticated user |
| `POST` | `/documents` | Upload a PDF, starts background pipeline |
| `GET` | `/documents/{id}` | Get document details + metrics + red flags |
| `GET` | `/documents/{id}/metrics` | Extraction Agent output |
| `GET` | `/documents/{id}/red-flags` | Red Flag Agent output |
| `GET` | `/documents/{id}/status` | Poll processing status |
| `DELETE` | `/documents/{id}` | Delete document + FAISS index + all data |
| `GET` | `/chat` | Chat history (optionally filtered by `?document_id=`) |
| `POST` | `/chat` | Ask the Research Agent `{ query, document_id? }` |
| `POST` | `/compare` | Run Comparison Agent `{ document_ids, metric? }` |
| `GET` | `/reports` | List generated reports |
| `POST` | `/reports` | Generate a new report `{ document_ids, sections? }` |
| `GET` | `/reports/{id}` | Get report metadata |
| `GET` | `/reports/{id}/download?token=` | Download report PDF |

Interactive API docs available at [http://localhost:8080/docs](http://localhost:8080/docs).

---

## Database Schema

```
users              — user_id, username, password_hash, password_salt, created_at
user_tokens        — token, user_id, created_at
companies          — company_id, company_name, industry, fiscal_year
documents          — document_id, user_id, company_id, file_name, file_path, upload_date
financial_metrics  — metric_id, document_id, revenue, net_income, ebitda, total_assets,
                     total_liabilities, eps, debt_to_equity
red_flags          — red_flag_id, document_id, risk_type, severity, description
research_queries   — query_id, user_id, document_id, question, answer, created_at
comparison_results — comparison_id, user_id, company1_id, company2_id, comparison_summary
reports            — report_id, user_id, report_title, report_path, generated_at,
                     document_ids, status, pages, sections
```

---

## Authentication Flow

1. User signs up → server generates `secrets.token_hex(32)` → stored in `user_tokens` table
2. Token returned to frontend → stored in `localStorage` as `ledger_token`
3. Every API request attaches `Authorization: Bearer <token>` header
4. On app load, `AuthContext` calls `GET /auth/me` to verify the stored token
5. If token is invalid/expired → localStorage cleared → user redirected to `/login`

---

## Document Pipeline (on upload)

```
POST /documents (PDF file)
        │
        ▼
  Save PDF to uploads/user_{id}/
        │
        ▼
  Return { id, company, status:"processing" } immediately
        │
        ▼ (BackgroundTask)
  1. PyMuPDF: extract text from all pages
  2. Detect company name (PDF metadata → first-page entity → filename)
  3. Document Agent: chunk → HuggingFace embed → FAISS index at vector_store/doc_{id}/
  4. Create Company record in DB
  5. Extraction Agent (Groq LLM): extract revenue/EPS/EBITDA/assets/liabilities
  6. Red Flag Agent (rule engine): analyze metrics for risk patterns
  7. Save FinancialMetric + RedFlag rows to DB
  8. DOCUMENT_STATUS[id] = "ready"
        │
        ▼
  Frontend polls status every 3s → updates Dashboard automatically
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key from [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | No | Groq model name (default: `llama-3.3-70b-versatile`) |
| `VITE_API_BASE_URL` | Yes (frontend) | Backend URL (default: `http://localhost:8080`) |

---

## Evaluation Criteria Mapping

Per the project specification from Vidzai Digital:

| Criterion | Implementation |
|---|---|
| Extraction accuracy + source faithfulness | Groq LLM grounded strictly in document chunks; fallback regex parser for non-LLM environments |
| Red flag quality and relevance | 8-category rule engine (leverage, margin, going concern, material weakness, litigation, etc.) + LLM qualitative scan |
| Research Agent query handling + citation accuracy | FAISS semantic search → top-k chunks → Groq LLM → page-level citations returned with every answer |
| Report completeness and clarity | 5-section ReportLab PDF: Executive Summary, Key Financials, Red Flags, Comparison, Outlook |
| Multi-agent collaboration smoothness | Sequential pipeline: Document → Extraction → Red Flag on upload; Research + Comparison + Report on demand |
| Implementation completeness | Full auth, all 6 agents, full CRUD, FAISS indexing, PDF generation, download |

---

## Known Limitations

- **Single-period metrics only** — Revenue Growth YoY cannot be computed because only one reporting period per document is stored. Upload multiple years of filings from the same company to work around this.
- **SQLite concurrency** — Fine for development and single-user use. Swap for PostgreSQL for multi-user production deployment.
- **DOCUMENT_STATUS is in-memory** — Status resets on server restart. The startup seeder (`_seed_document_status`) restores status based on whether metrics exist in the DB, so most docs will correctly show as `ready` or `failed`.
- **OCR requires Tesseract** — Scanned PDFs without a text layer need Tesseract installed. Text-layer PDFs work without it.

---

## Milestones Completed

- **Milestone 1** — Architecture, Document Agent (PDF parse, chunk, embed, FAISS), auth system
- **Milestone 2** — Extraction Agent (Groq LLM), Red Flag Agent (rule engine + LLM), multi-agent orchestration layer
- **Milestone 3** — Research Agent (FAISS + Groq Q&A + citations), Comparison Agent, conversational chat interface
- **Milestone 4** — Report Agent (ReportLab 5-section PDF), end-to-end testing, full frontend UI, documentation

---

## .gitignore Recommendations

Add the following before committing to any repository:

```
.env
*.db
uploads/
vector_store/
reports/
__pycache__/
node_modules/
dist/
.vite/
```

---

*Project developed as part of the Infosys Internship program at Vidzai Digital.*
