import { client, withFallback } from "./client.js";

const MOCK_SESSIONS_KEY = "ledger_mock_sessions";

function readMockSessions() {
  const raw = localStorage.getItem(MOCK_SESSIONS_KEY);
  if (raw) return JSON.parse(raw);
  const initial = [
    {
      id: "sess-default",
      name: "Q3 Coverage Review",
      createdAt: "2026-07-10T09:00:00Z",
      documentCount: 4,
    },
  ];
  localStorage.setItem(MOCK_SESSIONS_KEY, JSON.stringify(initial));
  return initial;
}

function writeMockSessions(sessions) {
  localStorage.setItem(MOCK_SESSIONS_KEY, JSON.stringify(sessions));
}

// Backend SessionSummary (snake_case) -> frontend shape (camelCase)
function toFrontendSession(s) {
  return {
    id: s.id,
    name: s.name,
    createdAt: s.created_at,
    documentCount: s.document_count,
  };
}

// GET /sessions — list research sessions
export async function listSessions() {
  return withFallback(
    () => client.get("/sessions").then((r) => r.data.map(toFrontendSession)),
    () => readMockSessions()
  );
}

// POST /sessions { name } — create a named research session
export async function createSession(name) {
  return withFallback(
    () => client.post("/sessions", { name }).then((r) => toFrontendSession(r.data)),
    () => {
      const sessions = readMockSessions();
      const created = {
        id: `sess-${Date.now()}`,
        name: name?.trim() || "Untitled session",
        createdAt: new Date().toISOString(),
        documentCount: 0,
      };
      const updated = [created, ...sessions];
      writeMockSessions(updated);
      return created;
    }
  );
}

// GET /sessions/:id — session detail
export async function getSession(id) {
  return withFallback(
    () => client.get(`/sessions/${id}`).then((r) => toFrontendSession(r.data)),
    () => readMockSessions().find((s) => s.id === id) || null
  );
}

// DELETE /sessions/:id
export async function deleteSession(id) {
  return withFallback(
    () => client.delete(`/sessions/${id}`).then((r) => r.data),
    () => {
      const updated = readMockSessions().filter((s) => s.id !== id);
      writeMockSessions(updated);
      return { ok: true };
    }
  );
}
