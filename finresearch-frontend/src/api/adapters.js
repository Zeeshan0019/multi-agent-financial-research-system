// This project's orchestrator returns real, flat, snake_case data (see
// backend/orchestrator/schemas.py). This frontend's components were designed
// against a richer, fictional shape (ticker, sector, docType, YoY deltas,
// named citation "sections"). None of those extra fields exist anywhere in
// the actual pipeline output, so rather than fabricate them, these adapters
// map real fields through and simply omit/placeholder what isn't available.
// Components (MetricCard, Citation, RiskBadge, ...) already handle missing
// optional fields gracefully.

const STATUS_MAP = {
  processing: "processing",
  ready: "ready",
  failed: "error",
};

export function mapStatus(status) {
  return STATUS_MAP[status] || status;
}

// Backend DocumentSummary / DocumentDetail -> frontend "doc" shape used by
// Dashboard.jsx, Upload.jsx, Research.jsx, Comparison.jsx, Reports.jsx.
export function toFrontendDoc(d) {
  return {
    id: d.id,
    company: d.company_name || d.file_name || "Untitled document",
    ticker: null, // not produced anywhere in the pipeline
    docType: null, // not classified by any agent
    fiscalYear: d.financial_year || null,
    uploadedAt: d.uploaded_at,
    status: mapStatus(d.status),
    pages: typeof d.page_count === "number" && d.page_count > 0 ? d.page_count : null,
    sector: null, // not classified by any agent
    error: d.error || null,
    warnings: d.warnings || [],
    confidenceScore: d.confidence_score ?? null,
    overallRisk: d.overall_risk || null,
    riskSummary: d.risk_summary || null,
  };
}

const METRIC_LABELS = {
  revenue: "Revenue",
  net_profit: "Net Profit",
  ebitda: "EBITDA",
  eps: "EPS",
  assets: "Total Assets",
  liabilities: "Total Liabilities",
  cash_flow: "Cash Flow",
};

// Backend DocumentMetrics (flat, no YoY deltas) -> { highlights, citation }
// shape MetricCard/Dashboard expect. No delta/tone is invented — the
// Extraction Agent doesn't compute period-over-period change, so those
// fields are simply left off (MetricCard renders fine without them).
export function toMetricsView(metrics) {
  if (!metrics) return { highlights: [], citation: null };
  const highlights = [];
  for (const [key, label] of Object.entries(METRIC_LABELS)) {
    const value = metrics[key];
    if (value !== null && value !== undefined && value !== "") {
      highlights.push({ label, value });
    }
  }
  if (metrics.ratios) {
    for (const [label, value] of Object.entries(metrics.ratios)) {
      if (value !== null && value !== undefined && value !== "") {
        highlights.push({ label, value });
      }
    }
  }
  // Everything the Extraction Agent found that isn't one of the ~15 named
  // fields above (payout ratios, contingent liabilities, goodwill, capex,
  // dividends, ad hoc margins, ...) comes through here instead — without
  // this the dashboard only ever shows a handful of metrics even when the
  // Extraction Agent found dozens.
  if (Array.isArray(metrics.other_metrics)) {
    for (const { label, value } of metrics.other_metrics) {
      if (label && value !== null && value !== undefined && value !== "") {
        highlights.push({ label, value });
      }
    }
  }
  return { highlights, citation: null };
}

// Backend RedFlagOut -> { severity, title, detail, citation } shape
// Dashboard.jsx expects. `source_page` (a real page number) is used as the
// citation reference instead of an invented "section" name.
export function toRedFlagsView(flags) {
  return (flags || []).map((f) => ({
    severity: normalizeSeverity(f.severity),
    title: f.title || f.category || "Red flag",
    detail: f.description || "",
    citation: {
      section: f.source_page ? `Page ${f.source_page}` : f.category || undefined,
    },
  }));
}

export function normalizeSeverity(severity) {
  const s = (severity || "").toLowerCase();
  if (s === "high" || s === "medium" || s === "low") return s;
  if (s === "critical") return "high";
  return "medium";
}
