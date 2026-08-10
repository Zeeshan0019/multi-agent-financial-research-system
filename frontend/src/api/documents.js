import { client, withFallback } from "./client.js";

// GET /documents — list all documents for the logged-in user
export async function listDocuments() {
  return withFallback(
    () => client.get("/documents"),
    () => []
  );
}

// POST /documents (multipart) — upload a PDF filing
export async function uploadDocument(file, onProgress) {
  const form = new FormData();
  form.append("file", file);
  return withFallback(
    () =>
      client.post("/documents", form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (evt) => {
          if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
        },
      }),
    () => {
      if (onProgress) onProgress(100);
      return {
        id: null,
        company: file.name.replace(/\.[^/.]+$/, ""),
        ticker: "—",
        docType: "Uploaded filing",
        fiscalYear: "—",
        uploadedAt: new Date().toISOString(),
        status: "processing",
        pages: "—",
        sector: "—",
      };
    }
  );
}

// GET /documents/:id — poll document status, metrics, and red flags
export async function getDocument(id) {
  return withFallback(
    () => client.get(`/documents/${id}`),
    () => null
  );
}

// GET /documents/:id/metrics — Extraction Agent output
export async function getDocumentMetrics(id) {
  return withFallback(
    () => client.get(`/documents/${id}/metrics`),
    () => ({ highlights: [], citation: null })
  );
}

// GET /documents/:id/red-flags — Red Flag Agent output
export async function getDocumentRedFlags(id) {
  return withFallback(
    () => client.get(`/documents/${id}/red-flags`),
    () => []
  );
}

// DELETE /documents/:id — remove document and its indexes
export async function deleteDocument(id) {
  return withFallback(
    () => client.delete(`/documents/${id}`),
    () => ({ deleted: true })
  );
}
