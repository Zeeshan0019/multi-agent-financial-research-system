import { client, withFallback } from "./client.js";
import { seedReports } from "../mock/seed.js";

// Backend ReportSummary / ReportStatus -> frontend shape used by Reports.jsx
function toFrontendReport(r) {
  return {
    id: r.id,
    title: r.file_name || "Untitled report",
    createdAt: r.generated_at || new Date().toISOString(),
    status: r.status || (r.download_url ? "ready" : "generating"),
    downloadUrl: r.download_url || null,
    error: r.error || null,
  };
}

// GET /sessions/:id/reports — report history
export async function listReports(sessionId) {
  return withFallback(
    () => client.get(`/sessions/${sessionId}/reports`).then((r) => r.data.map(toFrontendReport)),
    () => seedReports
  );
}

// POST /sessions/:id/reports { document_ids } — trigger the Report Agent.
// Note: the backend generates one fixed report structure (metrics + red
// flags for the selected documents) — it doesn't support choosing which
// sections to include, so that option isn't sent.
export async function generateReport(sessionId, documentIds) {
  return withFallback(
    () =>
      client
        .post(`/sessions/${sessionId}/reports`, { document_ids: documentIds })
        .then((r) => toFrontendReport(r.data)),
    () => ({
      id: `rpt-${Date.now()}`,
      title: "New analyst report",
      createdAt: new Date().toISOString(),
      documentIds,
      status: "generating",
      downloadUrl: null,
    })
  );
}

// GET /reports/:id — poll while status is "generating"
export async function getReport(id) {
  return withFallback(
    () => client.get(`/reports/${id}`).then((r) => toFrontendReport(r.data)),
    () => seedReports.find((r) => r.id === id) || { id, status: "ready" }
  );
}

// Full URL for the actual generated PDF (opens/downloads via the browser)
export function reportDownloadUrl(downloadPath) {
  if (!downloadPath) return null;
  const base = client.defaults.baseURL || "";
  return downloadPath.startsWith("http") ? downloadPath : `${base}${downloadPath}`;
}
