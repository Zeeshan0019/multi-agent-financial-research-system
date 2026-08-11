import { client, withFallback } from "./client.js";

// GET /reports — report history for logged-in user
export async function listReports() {
  return withFallback(
    () => client.get("/reports"),
    () => []
  );
}

// POST /reports { document_ids, sections } — trigger the Report Agent
export async function generateReport(documentIds, sections) {
  return withFallback(
    () => client.post("/reports", { document_ids: documentIds, sections }),
    () => ({
      id: `rpt-${Date.now()}`,
      title: "New analyst report",
      createdAt: new Date().toISOString(),
      documentIds,
      status: "generating",
      pages: null,
    })
  );
}

// GET /reports/:id — poll while status is "generating"
export async function getReport(id) {
  return withFallback(
    () => client.get(`/reports/${id}`),
    () => ({ id, status: "ready", pages: 5 })
  );
}
