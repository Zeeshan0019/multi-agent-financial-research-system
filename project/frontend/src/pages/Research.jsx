import { useEffect, useRef, useState, useCallback } from "react";
import { getChatHistory, askResearchAgent } from "../api/chat.js";
import { useDocuments } from "../context/DocumentsContext.jsx";
import PageHeader from "../components/PageHeader.jsx";
import { UserBubble, AssistantBubble, ThinkingBubble } from "../components/ChatBubble.jsx";

const SUGGESTIONS = [
  { text: "Summarize the key financial highlights of the selected document.", color: "border-l-violet-400 bg-violet-50/10 text-violet-700" },
  { text: "What are the main risk factors identified in this filing?", color: "border-l-rose-400 bg-rose-50/10 text-rose-700" },
  { text: "How did revenue and profit margins trend compared to prior year?", color: "border-l-teal-400 bg-teal-50/10 text-teal-700" },
];

export default function Research() {
  const { documents: allDocs } = useDocuments();
  const documents = allDocs.filter((d) => d.status === "ready");
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef(null);

  // When selected doc changes, load chat history for that doc
  useEffect(() => {
    getChatHistory(selectedDocId || undefined).then((history) => {
      // Map backend response: { role, content, citations } to { role, text/answer, citations }
      const mapped = history.map((m) => ({
        ...m,
        text: m.role === "user" ? m.content : undefined,
        answer: m.role === "assistant" ? m.content : undefined,
      }));
      setMessages(mapped);
    });
  }, [selectedDocId]);

  // Auto-scroll to bottom
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  async function send(text) {
    const query = (text ?? input).trim();
    if (!query || thinking) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setThinking(true);
    try {
      const reply = await askResearchAgent(query, selectedDocId || undefined);
      setThinking(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          answer: reply.content || reply.answer || "No response received.",
          steps: reply.steps || [],
          citations: reply.citations || [],
        },
      ]);
    } catch (err) {
      setThinking(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          answer: "Failed to connect to the Research Agent. Please make sure the backend is running.",
          steps: [],
          citations: [],
        },
      ]);
    }
  }

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  return (
    <div className="flex h-[calc(100vh-6rem)] flex-col animate-fade-up">
      <PageHeader
        eyebrow="Research Agent"
        title="Conversational Copilot"
        description="Select a document below then ask financial questions. Every answer is strictly grounded in the filing you choose."
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6 flex-1 min-h-0">
        {/* Left Side: Chat Workspace */}
        <div className="flex flex-col h-full min-h-0 bg-white/40 border border-slate-200/80 rounded-2xl p-4 shadow-sm shadow-slate-100/50">

          {/* Document selector */}
          <div className="mb-3 flex items-center gap-3 border-b border-slate-100 pb-3">
            <label className="text-xs font-bold text-ledger-950/60 shrink-0 uppercase tracking-wide">
              Document:
            </label>
            {documents.length === 0 ? (
              <span className="text-xs text-slate-400 font-semibold">No indexed documents. Upload a filing first.</span>
            ) : (
              <select
                value={selectedDocId ?? ""}
                onChange={(e) => setSelectedDocId(e.target.value ? Number(e.target.value) : null)}
                className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-ledger-950 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/10 focus:outline-none shadow-sm transition-all"
              >
                <option value="">All documents</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.company} {doc.fiscalYear !== "—" ? `· ${doc.fiscalYear}` : ""}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Messages scroll area */}
          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto pr-2 pb-4">
            {messages.length === 0 && !thinking && (
              <div className="flex h-full flex-col items-center justify-center text-center p-6">
                <span
                  className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl text-white shadow-md shadow-violet-200"
                  style={{ background: "linear-gradient(135deg,#8B5CF6,#14B8A6)" }}
                >
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <circle cx="11" cy="11" r="7" />
                    <path d="M21 21l-4.3-4.3" />
                  </svg>
                </span>
                <h3 className="text-base font-bold text-ledger-950">Start financial research</h3>
                <p className="mt-1 text-xs text-slate-400 max-w-xs font-semibold leading-relaxed">
                  {documents.length === 0
                    ? "Upload documents first, then come back to ask questions."
                    : "Select a document above (or query all), then ask a question."}
                </p>
                {documents.length > 0 && (
                  <div className="mt-6 flex flex-col gap-2.5 w-full max-w-md">
                    {SUGGESTIONS.map((s, i) => (
                      <button
                        key={i}
                        onClick={() => send(s.text)}
                        className={`card card-hover rounded-xl border-l-[4px] p-3 text-left text-xs font-bold transition-all shadow-sm ${s.color}`}
                      >
                        {s.text}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {messages.map((m, i) =>
              m.role === "user" ? (
                <UserBubble key={i} text={m.text} />
              ) : (
                <AssistantBubble key={i} steps={m.steps || []} answer={m.answer} citations={m.citations || []} />
              )
            )}
            {thinking && <ThinkingBubble />}
          </div>

          {/* Input form */}
          <form
            onSubmit={(e) => { e.preventDefault(); send(); }}
            className="flex items-center gap-2 border-t border-slate-100 pt-3.5 mt-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                documents.length === 0
                  ? "Upload a document first…"
                  : selectedDoc
                  ? `Ask about ${selectedDoc.company}…`
                  : "Ask across all your indexed documents…"
              }
              disabled={documents.length === 0}
              className="field flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              className="btn-primary shrink-0 py-3.5 px-6 rounded-xl text-sm shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!input.trim() || thinking || documents.length === 0}
            >
              Ask Agent
            </button>
          </form>
        </div>

        {/* Right Side: Sources Panel */}
        <div className="hidden lg:flex flex-col bg-white border border-slate-200 rounded-2xl p-4 shadow-sm shadow-slate-150/40">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-2.5">
            <span className="eyebrow flex items-center gap-1.5 text-ledger-950/60">
              Indexed Documents
            </span>
            <span className="font-mono text-[0.625rem] font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
              {documents.length} Files
            </span>
          </div>

          <p className="text-[0.7rem] leading-relaxed text-slate-400 font-semibold mb-4">
            The Research Agent retrieves context strictly from your uploaded and indexed filings:
          </p>

          <div className="flex-1 overflow-y-auto space-y-3 pr-0.5">
            {documents.map((doc) => {
              const isSelected = selectedDocId === doc.id;
              return (
                <button
                  key={doc.id}
                  onClick={() => setSelectedDocId(isSelected ? null : doc.id)}
                  className={`w-full text-left p-3 rounded-xl border transition-all duration-200 ${
                    isSelected
                      ? "border-violet-300 bg-violet-50/40 shadow-sm"
                      : "border-slate-100 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs font-bold text-ledger-950 truncate max-w-[130px]">{doc.company}</span>
                    {isSelected && (
                      <span className="font-mono text-[0.55rem] font-extrabold text-violet-600 bg-violet-100 border border-violet-200 px-1.5 py-0.5 rounded">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-[0.65rem] font-semibold text-slate-400">
                    {doc.docType !== "—" ? `${doc.docType} · ` : ""}{doc.fiscalYear !== "—" ? doc.fiscalYear : ""}
                  </p>
                  <div className="mt-2 flex items-center gap-1 text-[0.625rem] font-bold text-emerald-600">
                    <span className="h-1 w-1 rounded-full bg-emerald-500" />
                    Indexed
                  </div>
                </button>
              );
            })}

            {documents.length === 0 && (
              <div className="flex flex-col items-center justify-center text-center py-10">
                <p className="text-xs font-semibold text-slate-400 leading-normal">
                  No indexed documents yet. Upload a PDF filing to start.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
