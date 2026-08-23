import { client, withFallback } from "./client.js";

export async function listReports() {
  return withFallback(() => client.get("/reports"), () => []);
}

// Report generation can take time — use a dedicated long-timeout client call
export async function generateReport(documentIds, sections) {
  const res = await client.post(
    "/reports",
    { document_ids: documentIds, sections },
    { timeout: 180000 } // 3 minutes for large PDFs
  );
  return res.data;
}

export async function getReport(id) {
  return withFallback(() => client.get(`/reports/${id}`), () => ({ id, status: "ready", pages: 5 }));
}
