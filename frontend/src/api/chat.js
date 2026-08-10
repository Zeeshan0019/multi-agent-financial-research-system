import { client, withFallback } from "./client.js";

// GET /chat?document_id=<id> — chat history for the logged-in user
export async function getChatHistory(documentId) {
  const url = documentId != null ? `/chat?document_id=${documentId}` : "/chat";
  return withFallback(
    () => client.get(url),
    () => []
  );
}

// POST /chat { query, document_id } — ask the Research Agent
export async function askResearchAgent(query, documentId) {
  return withFallback(
    () => client.post("/chat", { query, document_id: documentId ?? null }),
    () =>
      new Promise((resolve) => {
        setTimeout(() => resolve({
          content: "The backend Research Agent is not reachable. Please start the FastAPI backend and try again.",
          citations: [],
        }), 900);
      })
  );
}
