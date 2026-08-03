import { useEffect, useRef, useState } from "react";
import { useSession } from "../context/SessionContext.jsx";
import { getChatHistory, askResearchAgent } from "../api/chat.js";
import { listDocuments } from "../api/documents.js";
import PageHeader from "../components/PageHeader.jsx";
import { UserBubble, AssistantBubble, ThinkingBubble } from "../components/ChatBubble.jsx";

const SUGGESTIONS = [
  { text: "How did gross margin trend across all indexed companies?", color: "border-l-violet-400 bg-violet-50/10 text-violet-700" },
  { text: "What's driving the leverage increase at Aster Robotics?", color: "border-l-teal-400 bg-teal-50/10 text-teal-700" },
  { text: "Summarize the biggest red flag for Blue Harbor Foods.", color: "border-l-rose-400 bg-rose-50/10 text-rose-700" },
];

export default function Research() {
  const { activeSession, activeSessionId } = useSession();
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!activeSessionId) return;
    getChatHistory(activeSessionId).then(setMessages);
    listDocuments(activeSessionId).then((docs) =>
      setDocuments(docs.filter((d) => d.status === "ready"))
    );
  }, [activeSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  async function send(text) {
    const query = text ?? input;
    if (!query.trim() || !activeSessionId) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setThinking(true);
    try {
      const reply = await askResearchAgent(activeSessionId, query);
      setThinking(false);
      setMessages((prev) => [...prev, { role: "assistant", ...reply }]);
    } catch (err) {
      setThinking(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          answer: "Failed to connect to the Research Agent. Please make sure the backend is running.",
          steps: ["Attempted request dispatch", "Encountered server network timeout"],
          citations: [],
        },
      ]);
    }
  }

  return (
    <div className="flex h-[calc(100vh-6rem)] flex-col animate-fade-up">
      <PageHeader
        eyebrow="Research Agent"
        title="Conversational Copilot"
        description="Ask complex financial questions across all indexed reports. Every answer is strictly grounded in the filings and contains step-by-step reasoning."
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6 flex-1 min-h-0">
        {/* Left Side: Chat Workspace */}
        <div className="flex flex-col h-full min-h-0 bg-white/40 border border-slate-200/80 rounded-2xl p-4 shadow-sm shadow-slate-100/50">
          {/* Messages scrollarea */}
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
                  Choose a suggested prompt below or type a query to interrogate the documents.
                </p>
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
              </div>
            )}

            {messages.map((m, i) =>
              m.role === "user" ? (
                <UserBubble key={i} text={m.text} />
              ) : (
                <AssistantBubble key={i} steps={m.steps} answer={m.answer} citations={m.citations} />
              )
            )}
            {thinking && <ThinkingBubble />}
          </div>

          {/* Form input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
            className="flex items-center gap-2 border-t border-slate-100 pt-3.5 mt-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about financial trends, margins, or anomalies in your indexed filings..."
              className="field flex-1"
            />
            <button
              type="submit"
              className="btn-primary shrink-0 py-3.5 px-6 rounded-xl text-sm shadow-md"
              disabled={!input.trim() || thinking}
            >
              Ask Agent
            </button>
          </form>
        </div>

        {/* Right Side: Parsed Sources Panel */}
        <div className="hidden lg:flex flex-col bg-white border border-slate-200 rounded-2xl p-4.5 shadow-sm shadow-slate-150/40">
          <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-2.5">
            <span className="eyebrow flex items-center gap-1.5 text-ledger-950/60">
              Workspace Sources
            </span>
            <span className="font-mono text-[0.625rem] font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
              {documents.length} Files
            </span>
          </div>

          <p className="text-[0.7rem] leading-relaxed text-slate-400 font-semibold mb-4">
            The Research Agent retrieves context strictly from these indexings:
          </p>

          <div className="flex-1 overflow-y-auto space-y-3.5 pr-0.5">
            {documents.map((doc) => (
              <div key={doc.id} className="p-3 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-all duration-200">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-xs font-bold text-ledger-950 truncate max-w-[130px]">{doc.company}</span>
                  <span className="font-mono text-[0.6rem] font-extrabold text-violet-600 bg-violet-50 border border-violet-100 px-1.5 py-0.5 rounded">
                    {doc.fiscalYear || "FY —"}
                  </span>
                </div>
                <p className="mt-1 text-[0.65rem] font-semibold text-slate-400">
                  {doc.pages ? `${doc.pages} pages indexed` : "Indexed filing"}
                </p>
                <div className="mt-2.5 flex items-center justify-between text-[0.625rem] font-bold text-slate-400 border-t border-slate-100/50 pt-2">
                  <span>{doc.pages} pages</span>
                  <span className="text-emerald-600 flex items-center gap-1">
                    <span className="h-1 w-1 rounded-full bg-emerald-500" />
                    Indexed
                  </span>
                </div>
              </div>
            ))}

            {documents.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center py-10">
                <p className="text-xs font-semibold text-slate-400 leading-normal">
                  No indexed files in session. Upload documents to make them queryable.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
