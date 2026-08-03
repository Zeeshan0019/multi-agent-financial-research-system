import { client, withFallback } from "./client.js";
import { seedComparison } from "../mock/seed.js";

// Backend CompanyComparison fields are formatted display strings (e.g.
// "₹98,450 cr", "23.9%") rather than raw numbers, since that's what the
// Extraction Agent produces. To drive the bar-chart visualizer we pull the
// first numeric token out of the string. This is a best-effort magnitude
// comparison, not a unit-normalized calculation — fine for a relative bar
// chart, not authoritative for exact analysis.
function parseNumeric(value) {
  if (typeof value === "number") return value;
  if (!value) return 0;
  const match = String(value).replace(/,/g, "").match(/-?\d+(\.\d+)?/);
  return match ? parseFloat(match[0]) : 0;
}

const METRIC_FIELD = {
  revenue: "revenue",
  net_profit: "net_profit",
  debt: "debt",
  margin: "margin",
};

// POST /sessions/:id/compare { document_ids } — Comparison Agent output.
// `metricKey` is applied client-side against the returned fields rather than
// sent to the backend, since the backend always returns all four metrics per
// company in one call.
export async function compareDocuments(sessionId, documentIds, metricKey) {
  return withFallback(
    () =>
      client
        .post(`/sessions/${sessionId}/compare`, { document_ids: documentIds })
        .then((r) => {
          const field = METRIC_FIELD[metricKey] || "revenue";
          const rows = r.data.companies.map((c) => ({
            company: c.company_name || c.document_id,
            value: parseNumeric(c[field]),
            displayValue: c[field],
          }));
          return { metric: metricKey, rows, summary: r.data.summary, citation: null };
        }),
    () =>
      new Promise((resolve) => {
        setTimeout(() => resolve(seedComparison), 700);
      })
  );
}
