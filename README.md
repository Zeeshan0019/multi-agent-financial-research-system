# multi-agent-financial-research-system
An AI-powered Multi-Agent Financial Research System that analyzes financial reports, extracts key metrics, detects risks, answers financial questions with citations, and generates analyst-style reports.

# Orchestrator — Run Guide

This is the integration layer that turns the four separate agents in this
repo into one working system for the `finresearch-frontend` app. It is the
**only** backend the frontend talks to (`VITE_API_BASE_URL`).

```
                        ┌─────────────────────────┐
   finresearch-frontend │   Orchestrator (:8000)  │
   (VITE_API_BASE_URL) ─▶  main.py / routers/*    │
                        │                         │
                        │  ┌───────────────────┐  │
                        │  │ Document Agent     │  │  in-process import
                        │  │ (FAISS index)      │  │  (document_agent_loader.py)
                        │  └───────────────────┘  │
                        │  ┌───────────────────┐  │      HTTP
                        │  │ Extraction Agent   │◀─┼──── :8001
                        │  └───────────────────┘  │
                        │  ┌───────────────────┐  │      HTTP
                        │  │ Red Flag Agent     │◀─┼──── :8002
                        │  └───────────────────┘  │
                        │  ┌───────────────────┐  │
                        │  │ Research Agent     │  │  in-process (services/research.py)
                        │  │ Report Agent       │  │  in-process (services/reports.py)
                        │  └───────────────────┘  │
                        └─────────────────────────┘
```

## 1. One-time setup: remove spaces from the two agent folder names

`Extraction agent/` and `Red Flag Agent/` have spaces in their names, which
makes them awkward (though not impossible) to launch as `module:app` uvicorn
targets. Renaming them once is the path of least friction:

```bash
cd backend
mv "Extraction agent" extraction_agent
mv "Red Flag Agent" redflag_agent
```

(If you'd rather not rename anything, see the "Without renaming" note in
step 3 below — it works too, just with a manual port edit.)

## 2. Install dependencies

Each agent has its own dependency set; install all of them into one
environment (a virtualenv is recommended):

```bash
cd backend
pip install -r ../requirements.txt          # Document Agent deps
pip install -r extraction_agent/requirements.txt  # if present, else see its docs
pip install -r redflag_agent/requirements.txt
pip install -r orchestrator/requirements.txt
```

> The Extraction Agent's own `requirements.txt` may not exist in this repo
> snapshot — check `backend/Extraction agent doumentation.pdf` for its full
> dependency list (it needs `fastapi`, `langgraph`, `langchain-groq`,
> `pdfplumber`, `pandas`, `openpyxl`, `docx2txt`, `rapidfuzz`, `tenacity`,
> `orjson`, `httpx`, `opencv-python`, an OCR backend, etc.).

## 3. Environment variables

Copy `orchestrator/.env.example` to `orchestrator/.env` and fill in
`GROQ_API_KEY` (shared by the Extraction Agent, Red Flag Agent, and the
Research Agent / Comparison summaries in the orchestrator). Also set
`GROQ_API_KEY` in whatever env the Extraction Agent and Red Flag Agent
processes run in (each reads it independently).

## 4. Start all three services (separate terminals)

```bash
# Terminal 1 — Extraction Agent
cd backend/extraction_agent
GROQ_API_KEY=... python3 "extraction_agent.py"   # runs on :8000 by default — see note below

# Terminal 2 — Red Flag Agent
cd backend/redflag_agent
PORT=8002 GROQ_API_KEY=... python3 redflag_agent.py

# Terminal 3 — Orchestrator (this folder)
cd backend/orchestrator
uvicorn main:app --reload --port 8000
```

**Port note:** the Extraction Agent's `__main__` block hard-codes
`port=8000`, which collides with the orchestrator. Either:
- edit that one line to `port=8001` (recommended, one-time), or
- launch it via `uvicorn "extraction_agent:app" --app-dir backend/extraction_agent --port 8001`
  instead of running the script directly.

Then set `EXTRACTION_AGENT_URL=http://localhost:8001` in `orchestrator/.env`
(already the default).

### Without renaming the folders
You can skip step 1 and instead run each agent exactly as documented in its
own PDF/README (as a script, `python3 "Extraction agent.py"`), just make sure
the ports end up as 8001 (extraction) and 8002 (red flag), and that
`orchestrator/.env` points at wherever they actually end up.

## 5. Point the frontend at the orchestrator

In `finresearch-frontend/finresearch-frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

Then `npm install && npm run dev` in that folder as usual.

## 6. Verify everything is wired up

```bash
curl http://localhost:8000/health
```

Returns whether the orchestrator can reach the Extraction Agent and Red Flag
Agent, and whether a Groq key is configured:

```json
{
  "status": "ok",
  "extraction_agent": {"url": "http://localhost:8001", "reachable": true},
  "redflag_agent": {"url": "http://localhost:8002", "reachable": true},
  "groq_configured": true
}
```

## What happens on upload

`POST /sessions/{id}/documents` saves the PDF, creates a `Document` row with
`status="processing"`, and returns immediately. A background task then:

1. Runs it through the **Document Agent** (parse → OCR fallback → chunk →
   embed → FAISS index scoped to the session).
2. Sends the raw file to the **Extraction Agent** (`/extract`) for structured
   financial metrics.
3. Pulls a few qualitative passages (risk factors, auditor notes, debt
   covenants, related-party transactions) back out of the freshly-built FAISS
   index and sends those plus the extracted metrics to the **Red Flag Agent**
   (`/redflags`).
4. Marks the document `status="ready"` (or `"failed"` with an `error`
   message) and stores everything. Any one of steps 2–3 failing just adds a
   warning and continues — the document is still indexed and chat-able even
   if, say, the Red Flag Agent is down.

The frontend polls `GET /sessions/{id}/documents` (see `Upload.jsx`) until
`status` flips away from `"processing"`.

## Notes / known limitations

- **SQLite** is used for simplicity (`orchestrator/data/orchestrator.db`).
  Fine for local/demo use; swap `DATABASE_URL` for Postgres for anything
  multi-user or concurrent.
- **Background tasks** run in-process via FastAPI's `BackgroundTasks`, not a
  real task queue — fine for a single-instance deployment, but won't survive
  a process restart mid-pipeline (the document would need to be re-uploaded).
- The **Research Agent** (`services/research.py`) degrades gracefully to an
  extractive (LLM-free) answer if `GROQ_API_KEY` isn't set, so chat still
  works without a key — just without synthesis.
- The **Report Agent** (`services/reports.py`) is new — it wasn't in the
  original repo — and renders metrics + red flags for the requested documents
  into a PDF with `reportlab`.
