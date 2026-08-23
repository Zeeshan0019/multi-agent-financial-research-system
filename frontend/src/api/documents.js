import { client, withFallback } from "./client.js";

export async function listDocuments() {
  return withFallback(() => client.get("/documents"), () => []);
}

// Upload — throws on error so Upload page shows real error message
export async function uploadDocument(file, onProgress) {
  const form = new FormData();
  form.append("file", file);
  const res = await client.post("/documents", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
    },
  });
  return res.data;
}

export async function getDocument(id) {
  return withFallback(() => client.get(`/documents/${id}`), () => null);
}

export async function getDocumentMetrics(id) {
  return withFallback(() => client.get(`/documents/${id}/metrics`), () => ({ highlights: [], citation: null }));
}

export async function getDocumentRedFlags(id) {
  return withFallback(() => client.get(`/documents/${id}/red-flags`), () => []);
}

export async function deleteDocument(id) {
  return withFallback(() => client.delete(`/documents/${id}`), () => ({ deleted: true }));
}

// Re-run red-flag detection + metric provenance on an existing document.
export async function reprocessDocument(id) {
  const res = await client.post(`/documents/${id}/reprocess`);
  return res.data;
}
