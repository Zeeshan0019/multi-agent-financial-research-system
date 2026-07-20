import client from "./client";

// GET /sessions/:id/reports -> [{ id, file_name, generated_at, download_url }]
export const listReports = (sessionId) =>
  client.get(`/sessions/${sessionId}/reports`).then((r) => r.data);

// POST /sessions/:id/reports { document_ids } -> { id, status: "generating" }
// Triggers the Report Agent to build the analyst-style PDF.
export const generateReport = (sessionId, documentIds) =>
  client
    .post(`/sessions/${sessionId}/reports`, { document_ids: documentIds })
    .then((r) => r.data);

// GET /reports/:id -> { id, status, download_url }
// Poll while status === "generating"
export const getReport = (reportId) =>
  client.get(`/reports/${reportId}`).then((r) => r.data);
