// Seed data for the 3–4 pre-loaded companies the project doc calls for.
// This lets every screen render real-looking analyst output before the
// FastAPI backend (Document/Extraction/Red Flag/Comparison/Research/Report
// agents) is live. src/api/*.js tries the real backend first and falls
// back to this file on failure — see src/api/client.js.

export const seedCompanies = [
  {
    id: "doc-aster",
    company: "Aster Robotics, Inc.",
    ticker: "ASTR",
    docType: "10-K",
    fiscalYear: "FY2025",
    uploadedAt: "2026-06-02T09:14:00Z",
    status: "ready",
    pages: 142,
    sector: "Industrial Automation",
  },
  {
    id: "doc-bluehbr",
    company: "Blue Harbor Foods Co.",
    ticker: "BHFC",
    docType: "Annual Report",
    fiscalYear: "FY2025",
    uploadedAt: "2026-06-04T11:40:00Z",
    status: "ready",
    pages: 98,
    sector: "Consumer Packaged Goods",
  },
  {
    id: "doc-nimbus",
    company: "Nimbus Cloud Systems",
    ticker: "NMBS",
    docType: "10-K",
    fiscalYear: "FY2025",
    uploadedAt: "2026-06-06T15:02:00Z",
    status: "ready",
    pages: 176,
    sector: "Enterprise SaaS",
  },
  {
    id: "doc-carrow",
    company: "Carrow Freight Holdings",
    ticker: "CRWF",
    docType: "10-K",
    fiscalYear: "FY2025",
    uploadedAt: "2026-06-08T08:20:00Z",
    status: "processing",
    pages: 121,
    sector: "Logistics",
  },
];

export const seedMetrics = {
  "doc-aster": {
    highlights: [
      { label: "Revenue", value: "$412.6M", delta: "+18.4% YoY", tone: "up" },
      { label: "Gross Margin", value: "47.2%", delta: "-1.1 pts YoY", tone: "down" },
      { label: "Operating Margin", value: "9.8%", delta: "+0.6 pts YoY", tone: "up" },
      { label: "Net Debt / EBITDA", value: "2.4x", delta: "+0.5x YoY", tone: "down" },
      { label: "Free Cash Flow", value: "$28.1M", delta: "-12.0% YoY", tone: "down" },
      { label: "R&D as % of Revenue", value: "14.3%", delta: "+2.0 pts YoY", tone: "flat" },
    ],
    citation: { page: 54, section: "Item 7 — MD&A, Results of Operations" },
  },
  "doc-bluehbr": {
    highlights: [
      { label: "Revenue", value: "$1.08B", delta: "+4.1% YoY", tone: "up" },
      { label: "Gross Margin", value: "32.6%", delta: "-2.3 pts YoY", tone: "down" },
      { label: "Operating Margin", value: "6.1%", delta: "-1.4 pts YoY", tone: "down" },
      { label: "Net Debt / EBITDA", value: "3.1x", delta: "+0.9x YoY", tone: "down" },
      { label: "Free Cash Flow", value: "$41.7M", delta: "-24.5% YoY", tone: "down" },
      { label: "Inventory Days", value: "58 days", delta: "+9 days YoY", tone: "down" },
    ],
    citation: { page: 39, section: "Financial Review, Segment Results" },
  },
  "doc-nimbus": {
    highlights: [
      { label: "ARR", value: "$602.3M", delta: "+31.2% YoY", tone: "up" },
      { label: "Gross Margin", value: "78.9%", delta: "+0.8 pts YoY", tone: "up" },
      { label: "Net Revenue Retention", value: "114%", delta: "-3 pts YoY", tone: "down" },
      { label: "Rule of 40", value: "46.5", delta: "+1.8 pts YoY", tone: "up" },
      { label: "Free Cash Flow Margin", value: "17.4%", delta: "+3.1 pts YoY", tone: "up" },
      { label: "Net Debt / EBITDA", value: "0.6x", delta: "-0.2x YoY", tone: "up" },
    ],
    citation: { page: 61, section: "Item 7 — MD&A, Key Business Metrics" },
  },
};

export const seedRedFlags = {
  "doc-aster": [
    {
      severity: "high",
      title: "Rising leverage against softening cash generation",
      detail:
        "Net debt/EBITDA climbed from 1.9x to 2.4x while free cash flow fell 12% YoY, narrowing the covenant headroom disclosed in the credit facility note.",
      citation: { page: 88, section: "Note 9 — Long-Term Debt" },
    },
    {
      severity: "medium",
      title: "Gross margin compression in the core segment",
      detail:
        "Gross margin declined 1.1 points as input costs in the Motion Systems segment outpaced pricing actions taken in Q3.",
      citation: { page: 55, section: "Item 7 — MD&A, Segment Discussion" },
    },
    {
      severity: "low",
      title: "Auditor added an emphasis-of-matter paragraph",
      detail:
        "The independent auditor's report flags a change in inventory costing method as worth separate reader attention, though it does not qualify the opinion.",
      citation: { page: 101, section: "Report of Independent Registered Public Accounting Firm" },
    },
  ],
  "doc-bluehbr": [
    {
      severity: "high",
      title: "Inventory building faster than sales",
      detail:
        "Inventory days rose from 49 to 58 while revenue grew only 4.1%, suggesting demand is not keeping pace with production build-out.",
      citation: { page: 41, section: "Financial Review, Working Capital" },
    },
    {
      severity: "high",
      title: "Leverage covenant headroom narrowing",
      detail:
        "Net debt/EBITDA rose to 3.1x, approaching the 3.5x maximum permitted under the revolving credit agreement described in the debt note.",
      citation: { page: 76, section: "Note 11 — Credit Facilities" },
    },
    {
      severity: "medium",
      title: "Concentration in two retail customers",
      detail:
        "Two customers together represent 34% of net sales, up from 29% last year, a concentration risk the filing itself calls out.",
      citation: { page: 12, section: "Item 1A — Risk Factors" },
    },
  ],
  "doc-nimbus": [
    {
      severity: "medium",
      title: "Net revenue retention decelerating",
      detail:
        "NRR slipped from 117% to 114%, the second consecutive year of decline, even as gross new bookings held up.",
      citation: { page: 62, section: "Item 7 — MD&A, Key Business Metrics" },
    },
    {
      severity: "low",
      title: "Stock-based compensation growing faster than headcount",
      detail:
        "SBC expense grew 22% YoY against 9% headcount growth, a widening gap versus the prior three fiscal years.",
      citation: { page: 70, section: "Note 14 — Stock-Based Compensation" },
    },
  ],
};

export const seedComparison = {
  metric: "Gross Margin (TTM)",
  rows: [
    { company: "Aster Robotics", value: 47.2 },
    { company: "Blue Harbor Foods", value: 32.6 },
    { company: "Nimbus Cloud Systems", value: 78.9 },
  ],
  citation: { section: "Compiled from Item 7 — MD&A across filings" },
};

export const seedReports = [
  {
    id: "rpt-001",
    title: "Aster Robotics vs. Nimbus Cloud Systems — Comparative Review",
    createdAt: "2026-07-14T10:02:00Z",
    documentIds: ["doc-aster", "doc-nimbus"],
    status: "ready",
    pages: 9,
  },
  {
    id: "rpt-002",
    title: "Blue Harbor Foods — Standalone Credit & Margin Review",
    createdAt: "2026-07-09T16:45:00Z",
    documentIds: ["doc-bluehbr"],
    status: "ready",
    pages: 6,
  },
];

export function seedChatReply(query) {
  return {
    id: `msg-${Date.now()}`,
    role: "assistant",
    createdAt: new Date().toISOString(),
    steps: [
      "Identified the metric and companies referenced in the question.",
      "Retrieved the relevant passages from the indexed filings.",
      "Compared the figures and checked for consistency across sections.",
    ],
    answer:
      "Aster Robotics' gross margin fell 1.1 points to 47.2% on rising input costs in Motion Systems, while Blue Harbor Foods' margin fell more sharply, down 2.3 points to 32.6%, driven by inventory build and freight cost inflation. Nimbus Cloud Systems moved the opposite direction, up 0.8 points to 78.9%, reflecting its software-heavy cost structure.",
    citations: [
      { label: "ASTR 10-K, p.55", section: "Item 7 — MD&A" },
      { label: "BHFC AR, p.39", section: "Financial Review" },
      { label: "NMBS 10-K, p.61", section: "Item 7 — MD&A" },
    ],
    query,
  };
}
