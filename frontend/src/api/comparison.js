import { client, withFallback } from "./client.js";

// POST /compare { document_ids, metric } — Comparison Agent output
export async function compareDocuments(documentIds, metric) {
  return withFallback(
    () => client.post("/compare", { document_ids: documentIds, metric }),
    () =>
      new Promise((resolve) => {
        setTimeout(() => resolve({
          metric: metric || "Operating Margin (TTM)",
          rows: [],
          citation: { section: "Backend unavailable — start FastAPI to run comparisons." },
        }), 700);
      })
  );
}
