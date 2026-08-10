# Multi-Agent Financial Research System — Frontend

This is the React (Vite) frontend for the **Multi-Agent Financial Research System**, designed for finance students, MBA candidates, and early-career analysts. The platform streamlines parsing, key metrics extraction, risk auditing, benchmarking, and report generation from company annual reports (10-K filings) using a team of specialized AI agents.

---

## 🚀 What This Frontend Does

The application provides a highly visual, bright-themed, and interactive workspace divided into five primary views:

1. **Coverage Dashboard**: 
   * Provides quick statistics on indexed filings (documents count, ready state, sector coverage).
   * Renders a list of companies. Clicking any row expands to reveal extracted metrics (Revenues, Margin trend, Leverage ratios) from the **Extraction Agent** and risk callouts from the **Red Flag Agent**.
2. **Document Ingestion (Upload)**:
   * Drag-and-drop area for new filings (PDF, TXT, CSV, or HTML).
   * Renders a sequential checklist representing the multi-agent orchestration stages (Document Agent parsing/indexing → Extraction Agent metric compilation → Red Flag Agent anomaly scanning).
3. **Conversational Research Workspace**:
   * A chat panel where users ask multi-part financial questions.
   * Renders User messages alongside Assistant answers that include a collapsible **Reasoning Pathway** (backend agent logs) and hoverable source citations pointing to the page number of the filing.
   * Pins a **Workspace Sources** side-drawer showing exactly which files are queryable in the active session.
4. **Benchmark Comparison**:
   * Enables selection of two or more companies and a financial indicator.
   * Compiles data into an interactive horizontal bar chart displaying values side-by-side.
5. **Analyst Report Compiler**:
   * Compiles the output from all agents into a structured analyst brief.
   * Clicking "View Analyst PDF" opens a simulated multi-page, print-ready document reader modal covering:
     * **Cover Page** (Metadata and audit details)
     * **Executive Summary** (Company and sector summaries)
     * **Key Financials Table** (Structured side-by-side metric comparisons)
     * **Red Flags & Risks** (Anomaly warning levels with document citations)
     * **Benchmark Charts** (Side-by-side margins graph)
     * **Grounded Outlook** (Management discussion summaries)

---

## 📂 How It Gets Files (Mock Fallback Layer)

To ensure the frontend is instantly usable and can be developed independently of the FastAPI backend, it utilizes a **mock fallback layer** configured in `src/api/client.js`:

* **Active Backend Detected**: If a FastAPI backend is running and configured via environment variables, the system directly communicates with the REST endpoints (uploading PDFs, retrieving index status, querying vector databases, compiling PDFs).
* **No Live Backend (Local Dev)**: If the backend is not running, the application catches the network error and automatically falls back to the seed database located in **`src/mock/seed.js`**. 

This seed data pre-loads four realistic company profiles with associated metrics and red flags:
* **Aster Robotics, Inc. (ASTR)** — *Industrial Automation sector* (MD&A margin compressions)
* **Blue Harbor Foods Co. (BHFC)** — *Consumer Packaged Goods sector* (Inventory days increase)
* **Nimbus Cloud Systems (NMBS)** — *Enterprise SaaS sector* (ARR growth and retention benchmarks)
* **Carrow Freight Holdings (CRWF)** — *Logistics sector* (Processing status mockup)

This guarantees that every screen, button click, uploader stepper, reasoning log, citation tooltip, comparison bar, and PDF pagination compiles real-looking analyst data immediately on start.

---

## 🛠️ How to Run the Application

### Prerequisites
* [Node.js](https://nodejs.org) (v18 or higher recommended)
* NPM (comes packaged with Node.js)

### Step 1: Install Dependencies
Open your terminal in the `finresearch-frontend` directory and run:
```bash
npm install
```

### Step 2: Configure Environment Variables
Copy the template `.env.example` file to create a local `.env` configuration:
```bash
cp .env.example .env
```
Open the `.env` file. If you are integrating with a live FastAPI backend, set its base URL:
```env
VITE_API_BASE_URL=http://localhost:8000
```
*(If the backend teammate's server is not live, you can leave it as default; the frontend will seamlessly switch to the fallback seed data).*

### Step 3: Run the Development Server
Start the local server by running:
```bash
npm run dev
```

### Step 4: Open in Web Browser
Once Vite launches, open the printed URL:
* **`http://localhost:5173`** *(or `http://localhost:5174` if port 5173 is occupied)*

---

## 📦 Project Structure

```
finresearch-frontend/
├── src/
│   ├── api/          # Axios wrappers per backend resource (sessions, documents, chat, comparison, reports)
│   ├── components/   # Shared UI components (Sidebar Layout, MetricCard, RiskBadge, Citations, ChatBubbles)
│   ├── context/      # SessionContext (tracks current active research session globally)
│   ├── mock/         # seed.js (Fallback seed companies, ratios, red flags, and chat prompts)
│   └── pages/        # Dashboard, Ingest/Upload, Research chat, Comparison chart, Reports viewer
├── tailwind.config.js# Custom color configurations, typography, and animation tokens
├── index.html        # App wrapper importing Inter, Space Grotesk, and JetBrains Mono fonts
└── package.json      # Node scripts and package dependencies
```
