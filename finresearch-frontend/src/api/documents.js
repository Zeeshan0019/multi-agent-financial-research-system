import { client, withFallback } from "./client.js";
import { seedCompanies, seedMetrics, seedRedFlags } from "../mock/seed.js";
import { toFrontendDoc, toMetricsView, toRedFlagsView } from "./adapters.js";

// GET /sessions/:id/documents — list documents in a session
export async function listDocuments(sessionId) {
  return withFallback(
    () => client.get(`/sessions/${sessionId}/documents`).then((r) => r.data.map(toFrontendDoc)),
    () => seedCompanies
  );
}

// POST /sessions/:id/documents (multipart) — upload a filing for the
// Document Agent to parse, chunk, embed, index; Extraction + Red Flag agents
// then run automatically as a background pipeline (see orchestrator docs).
// Note: the orchestrator currently only accepts .pdf files.
export async function uploadDocument(sessionId, file, onProgress) {
  const form = new FormData();
  form.append("file", file);
  return withFallback(
    () =>
      client
        .post(`/sessions/${sessionId}/documents`, form, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (evt) => {
            if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
          },
        })
        .then((r) => toFrontendDoc(r.data)),
    () => {
      if (onProgress) onProgress(100);
      return {
        id: `doc-${Date.now()}`,
        company: file.name.replace(/\.[^/.]+$/, ""),
        ticker: null,
        docType: null,
        fiscalYear: null,
        uploadedAt: new Date().toISOString(),
        status: "processing",
        pages: null,
        sector: null,
      };
    }
  );
}

// GET /documents/:id — status + metrics + red flags (poll while "processing")
export async function getDocument(id) {
  return withFallback(
    () => client.get(`/documents/${id}`).then((r) => toFrontendDoc(r.data)),
    () => seedCompanies.find((d) => d.id === id) || null
  );
}

// GET /documents/:id/metrics — Extraction Agent output
export async function getDocumentMetrics(id) {
  return withFallback(
    () => client.get(`/documents/${id}/metrics`).then((r) => toMetricsView(r.data)),
    () => seedMetrics[id] || { highlights: [], citation: null }
  );
}

// GET /documents/:id/red-flags — Red Flag Agent output
export async function getDocumentRedFlags(id) {
  return withFallback(
    () => client.get(`/documents/${id}/red-flags`).then((r) => toRedFlagsView(r.data)),
    () => seedRedFlags[id] || []
  );
}

export async function deleteDocument(id) {
  return withFallback(
    () => client.delete(`/documents/${id}`).then((r) => r.data),
    () => ({ deleted: true, id })
  );
}
