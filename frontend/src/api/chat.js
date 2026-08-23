import { client } from "./client.js";

// GET /chat?document_id=<id>
export async function getChatHistory(documentId) {
  try {
    const url = documentId != null ? `/chat?document_id=${documentId}` : "/chat";
    const res = await client.get(url);
    return res.data;
  } catch {
    return [];
  }
}

// POST /chat — ask the Research Agent (no fallback — throw real errors)
export async function askResearchAgent(query, documentId) {
  const res = await client.post("/chat", { query, document_id: documentId ?? null });
  return res.data;
}

// DELETE /chat — clear research history (optionally scoped to one document)
export async function clearChatHistory(documentId) {
  const url = documentId != null ? `/chat?document_id=${documentId}` : "/chat";
  const res = await client.delete(url);
  return res.data;
}
