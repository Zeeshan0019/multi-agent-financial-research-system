import React, { useEffect, useRef, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import ChatBubble from "../components/ChatBubble.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { getChatHistory, askQuestion } from "../api/chat.js";

const SUGGESTED = [
  "What are the major financial risks in this report?",
  "Why did net profit change year over year?",
  "Summarize the cash flow position.",
];

export default function Research() {
  const { activeSessionId, activeSessionName } = useSession();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    if (activeSessionId) loadHistory();
  }, [activeSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function loadHistory() {
    try {
      const data = await getChatHistory(activeSessionId);
      setMessages(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function send(text) {
    const query = (text ?? input).trim();
    if (!query || sending) return;
    setInput("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setSending(true);
    try {
      const reply = await askQuestion(activeSessionId, query);
      setMessages((prev) => [...prev, reply]);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => prev.slice(0, -1)); // roll back the optimistic user message on failure
      setInput(query);
    } finally {
      setSending(false);
    }
  }

  if (!activeSessionId) {
    return (
      <div>
        <PageHeader eyebrow="Research" title="Ask questions about your reports" />
        <div className="px-8 py-6">
          <div className="card p-8 text-center max-w-md">
            <p className="text-sm text-ledger-950/60">
              No active session. Go to the Dashboard to create or open one first.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      <PageHeader
        eyebrow="Research"
        title="Research workspace"
        description={`Session: ${activeSessionName}. Answers are grounded in your uploaded documents and cite the source page.`}
      />

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-8 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="max-w-lg mx-auto text-center py-12">
            <p className="text-sm text-ledger-950/50 mb-4">
              Try asking one of these:
            </p>
            <div className="flex flex-col gap-2">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="btn-secondary text-left justify-start"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <ChatBubble key={m.id ?? i} role={m.role} content={m.content} citations={m.citations} />
        ))}

        {sending && (
          <div className="flex justify-start">
            <div className="card px-4 py-3 text-sm text-ledger-950/50">Thinking…</div>
          </div>
        )}
      </div>

      {error && (
        <p className="px-8 text-sm text-flag-high" role="alert">
          {error}
        </p>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="px-8 py-4 border-t border-ledger-950/10 flex items-center gap-3"
      >
        <input
          className="input-field"
          placeholder="Ask about revenue, risks, or comparisons…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={sending || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
