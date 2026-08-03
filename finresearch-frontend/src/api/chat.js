import { client, withFallback } from "./client.js";
import { seedChatReply } from "../mock/seed.js";

// Backend ChatMessageOut -> { role, text/answer, citations } shape used by
// Research.jsx / ChatBubble.jsx. The Research Agent doesn't emit a
// step-by-step reasoning log, so `steps` is left empty rather than invented
// (the "Show reasoning pathway" toggle simply won't appear for real answers).
// Citations use the real page number and retrieved snippet — no fabricated
// "section" names.
function toFrontendMessage(m) {
  if (m.role === "user") {
    return { role: "user", text: m.content };
  }
  return {
    role: "assistant",
    answer: m.content,
    steps: [],
    citations: (m.citations || []).map((c) => ({
      label: c.page ? `Page ${c.page}` : "Source document",
      section: c.snippet,
    })),
  };
}

// GET /sessions/:id/chat — chat history for the session
export async function getChatHistory(sessionId) {
  return withFallback(
    () => client.get(`/sessions/${sessionId}/chat`).then((r) => r.data.map(toFrontendMessage)),
    () => []
  );
}

// POST /sessions/:id/chat { query } — ask the Research Agent
export async function askResearchAgent(sessionId, query) {
  return withFallback(
    () =>
      client
        .post(`/sessions/${sessionId}/chat`, { query })
        .then((r) => toFrontendMessage(r.data)),
    () =>
      new Promise((resolve) => {
        setTimeout(() => resolve(seedChatReply(query)), 900);
      })
  );
}
