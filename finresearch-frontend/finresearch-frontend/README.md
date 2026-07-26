# Ledger — Multi-Agent Financial Research Frontend

React (Vite) frontend for the Multi-Agent Financial Research System. Covers all five screens from the design doc: Dashboard, Upload, Research (chat), Comparison, and Reports.

## What's inside

```
src/
  api/          axios calls — one file per backend resource (sessions, documents, chat, comparison, reports)
  components/   shared UI: Layout/sidebar, MetricCard, RiskBadge, ChatBubble, PageHeader
  context/      SessionContext — tracks the active research session across pages
  pages/        Dashboard, Upload, Research, Comparison, Reports
```

The API layer in `src/api/` is written against the REST contract implied by your project doc's agent pipeline (Document → Extraction → Red Flag → Comparison → Research → Report agents). If your FastAPI teammate's routes differ, the only files you need to touch are the ones in `src/api/` — the pages don't know or care about the URLs.

## 1. Run it locally

You need [Node.js 18+](https://nodejs.org) installed.

```bash
cd finresearch-frontend
npm install
cp .env.example .env
```

Open `.env` and point it at your backend:

```
VITE_API_BASE_URL=http://localhost:8000
```

(Use whatever URL your FastAPI teammate gives you — if the backend isn't ready yet, leave the default; pages will just show request errors until it's live, the UI itself will still render.)

Start the dev server:

```bash
npm run dev
```

Open the printed URL (usually `http://localhost:5173`).

## 2. Push it to GitHub

Deploying to Vercel or Render both work by connecting a GitHub repo.

```bash
cd finresearch-frontend
git init
git add .
git commit -m "Initial frontend"
```

Create an empty repo on GitHub (no README/license, so it stays empty), then:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

## 3. Deploy on Vercel (recommended for a Vite/React app)

1. Go to https://vercel.com and sign in with GitHub.
2. Click **Add New → Project**, and import the repo you just pushed.
3. Vercel auto-detects Vite. Confirm these build settings (they should be filled in automatically):
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL` = the URL of your deployed backend (e.g. `https://finresearch-backend.onrender.com`)
5. Click **Deploy**. Vercel gives you a live URL like `https://finresearch-frontend.vercel.app` in about a minute.
6. `vercel.json` is already included in this project — it makes sure refreshing a route like `/research` doesn't 404 (client-side routing).

Any time you push to `main`, Vercel redeploys automatically.

## 4. Deploy on Render (alternative)

1. Go to https://render.com and sign in with GitHub.
2. Click **New → Static Site**, and select the repo.
3. Fill in:
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. Under **Environment**, add:
   - `VITE_API_BASE_URL` = your backend URL
5. Under **Redirects/Rewrites**, add a rewrite rule so client-side routing works:
   - Source: `/*` → Destination: `/index.html` → Action: `Rewrite`
   (This project also ships a `render.yaml` with the same config, which Render picks up automatically if you deploy via "Blueprint" instead of the manual flow above.)
6. Click **Create Static Site**. Render builds and gives you a URL like `https://finresearch-frontend.onrender.com`.

## 5. Connect it to the backend

Whichever host you use, the frontend only needs one thing from the backend team: the base URL, set as `VITE_API_BASE_URL`. Make sure the backend's CORS settings allow requests from your deployed frontend origin (e.g. `https://finresearch-frontend.vercel.app`) — ask your backend teammate to add it to FastAPI's `CORSMiddleware allow_origins`.

## 6. API contract (share this with your backend teammate)

| Endpoint | Method | Purpose |
|---|---|---|
| `/sessions` | GET / POST | list / create research sessions |
| `/sessions/:id` | GET / DELETE | session detail / delete |
| `/sessions/:id/documents` | GET / POST (multipart) | list documents / upload a PDF |
| `/documents/:id` | GET | status + metrics + red flags (poll while `status: "processing"`) |
| `/documents/:id/metrics` | GET | Extraction Agent output |
| `/documents/:id/red-flags` | GET | Red Flag Agent output |
| `/sessions/:id/chat` | GET / POST `{ query }` | chat history / ask the Research Agent |
| `/sessions/:id/compare` | POST `{ document_ids }` | Comparison Agent output |
| `/sessions/:id/reports` | GET / POST `{ document_ids }` | report history / trigger Report Agent |
| `/reports/:id` | GET | poll while `status: "generating"` |

Full request/response shapes are documented as comments above each function in `src/api/`.

## Notes

- Styling uses Tailwind CSS (already configured — `tailwind.config.js`, `postcss.config.js`).
- No component library dependency, so there's nothing extra to install beyond `npm install`.
- Auth isn't wired up yet (the doc marks it optional) — `src/api/client.js` already attaches a `Bearer` token from `localStorage` if one is set, so adding a login screen later just means writing to `localStorage.setItem("ledger_token", ...)`.
