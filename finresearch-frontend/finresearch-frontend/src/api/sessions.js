import client from "./client";

// GET /sessions -> [{ id, name, created_at, document_count }]
export const listSessions = () => client.get("/sessions").then((r) => r.data);

// POST /sessions { name } -> { id, name, created_at }
export const createSession = (name) =>
  client.post("/sessions", { name }).then((r) => r.data);

// GET /sessions/:id -> full session detail
export const getSession = (sessionId) =>
  client.get(`/sessions/${sessionId}`).then((r) => r.data);

// DELETE /sessions/:id
export const deleteSession = (sessionId) =>
  client.delete(`/sessions/${sessionId}`).then((r) => r.data);
