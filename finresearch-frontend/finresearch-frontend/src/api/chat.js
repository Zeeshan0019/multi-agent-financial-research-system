import client from "./client";

// GET /sessions/:id/chat -> [{ id, role: "user"|"assistant", content, citations, created_at }]
export const getChatHistory = (sessionId) =>
  client.get(`/sessions/${sessionId}/chat`).then((r) => r.data);

// POST /sessions/:id/chat { query }
// -> { id, role: "assistant", content, citations: [{ document_id, page, snippet }] }
// This hits the Research Agent, which retrieves chunks from the vector DB
// (FAISS/ChromaDB) and grounds the answer with citations.
export const askQuestion = (sessionId, query) =>
  client.post(`/sessions/${sessionId}/chat`, { query }).then((r) => r.data);
