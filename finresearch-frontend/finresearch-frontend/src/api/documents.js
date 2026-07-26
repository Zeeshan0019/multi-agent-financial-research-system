import client from "./client";

// POST /sessions/:id/documents  (multipart/form-data, field name "file")
// -> { id, file_name, company_name, status: "processing" }
// Backend flow this triggers: Document Agent (parse -> chunk -> embed -> index)
// then Extraction Agent + Red Flag Agent run automatically.
export const uploadDocument = (sessionId, file, onUploadProgress) => {
  const formData = new FormData();
  formData.append("file", file);
  return client
    .post(`/sessions/${sessionId}/documents`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress,
    })
    .then((r) => r.data);
};

// GET /sessions/:id/documents -> [{ id, file_name, company_name, status, uploaded_at }]
export const listDocuments = (sessionId) =>
  client.get(`/sessions/${sessionId}/documents`).then((r) => r.data);

// GET /documents/:id -> { id, status, metrics, red_flags }
// Poll this while status === "processing" until it flips to "ready" or "failed"
export const getDocument = (documentId) =>
  client.get(`/documents/${documentId}`).then((r) => r.data);

// GET /documents/:id/metrics -> { revenue, net_profit, ebitda, eps, assets, liabilities, cash_flow, ratios }
export const getDocumentMetrics = (documentId) =>
  client.get(`/documents/${documentId}/metrics`).then((r) => r.data);

// GET /documents/:id/red-flags -> [{ id, description, severity, source_page }]
export const getDocumentRedFlags = (documentId) =>
  client.get(`/documents/${documentId}/red-flags`).then((r) => r.data);

export const deleteDocument = (documentId) =>
  client.delete(`/documents/${documentId}`).then((r) => r.data);
