// Offline seed data - used only when the FastAPI backend is unreachable.
// Returns empty collections so the UI clearly shows "no data yet" rather
// than fake companies, making it obvious when the real backend is needed.

export const seedCompanies = [];

export const seedMetrics = {};

export const seedRedFlags = {};

export const seedComparison = {
  metric: "Gross Margin (TTM)",
  rows: [],
  citation: { section: "Compiled from indexed filings" },
};

export const seedReports = [];

export function seedChatReply(query) {
  return {
    id: `msg-${Date.now()}`,
    role: "assistant",
    createdAt: new Date().toISOString(),
    steps: [],
    content: "The backend Research Agent is not reachable right now. Please start the FastAPI backend and try again.",
    citations: [],
    query,
  };
}
