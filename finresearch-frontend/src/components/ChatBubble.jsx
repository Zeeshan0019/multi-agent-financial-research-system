import { useState } from "react";
import Citation from "./Citation.jsx";

export function UserBubble({ text }) {
  return (
    <div className="flex justify-end items-start gap-3 animate-fade-up">
      <div className="flex flex-col items-end max-w-lg">
        <div
          className="rounded-2xl rounded-tr-sm px-4.5 py-3 text-sm font-semibold text-white shadow-md shadow-violet-100/40"
          style={{ background: "linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)" }}
        >
          {text}
        </div>
        <span className="mt-1 text-[0.625rem] font-bold text-slate-400 uppercase tracking-wider">
          You
        </span>
      </div>
      <div className="h-8 w-8 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center font-bold text-xs shadow-sm">
        U
      </div>
    </div>
  );
}

export function AssistantBubble({ steps = [], answer, citations = [] }) {
  const [showSteps, setShowSteps] = useState(false);

  return (
    <div className="flex justify-start items-start gap-3 animate-fade-up">
      <div className="h-8 w-8 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center font-bold text-xs shadow-sm">
        A
      </div>
      <div className="flex flex-col items-start max-w-2xl w-full">
        <div className="card rounded-2xl rounded-tl-sm p-5 border border-slate-200 bg-white shadow-sm w-full">
          {/* Agent Badge & Status */}
          <div className="mb-3.5 flex items-center justify-between border-b border-slate-100 pb-2.5">
            <span className="eyebrow flex items-center gap-1.5 text-emerald-600">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Research Agent
            </span>
            {steps.length > 0 && (
              <button
                type="button"
                onClick={() => setShowSteps(!showSteps)}
                className="text-[0.68rem] font-bold text-violet-600 hover:text-violet-700 transition-colors flex items-center gap-1 focus:outline-none"
              >
                {showSteps ? "Hide steps" : "Show reasoning pathway"}
                <svg
                  width="10"
                  height="10"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                  className={`transition-transform duration-200 ${showSteps ? "rotate-180" : ""}`}
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>
            )}
          </div>

          {/* Reasoning pathway steps (collapsible) */}
          {steps.length > 0 && showSteps && (
            <div className="mb-4 rounded-xl bg-slate-50/70 border border-slate-150 p-3.5 animate-scale-in">
              <p className="font-mono text-[0.65rem] uppercase font-bold text-ledger-950/40 tracking-wider mb-2">
                Agent Collaboration Log
              </p>
              <ul className="space-y-2">
                {steps.map((s, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-emerald-100/60 text-emerald-600 border border-emerald-200/50">
                      <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4">
                        <path d="M20 6L9 17l-5-5" />
                      </svg>
                    </span>
                    <span className="font-mono text-[0.68rem] leading-relaxed text-ledger-950/70 font-medium">
                      {s}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Main Answer */}
          <div className="text-sm leading-relaxed text-ledger-950 font-medium">
            <p className="whitespace-pre-line">{answer}</p>
            {citations.length > 0 && (
              <div className="mt-4 pt-3.5 border-t border-slate-100 flex flex-wrap gap-2 items-center">
                <span className="text-[0.68rem] font-bold text-slate-400 uppercase tracking-wider">
                  Grounded Sources:
                </span>
                <span className="flex flex-wrap gap-1.5">
                  {citations.map((c, i) => (
                    <Citation key={i} index={i + 1} label={c.label} section={c.section} />
                  ))}
                </span>
              </div>
            )}
          </div>
        </div>
        <span className="mt-1 text-[0.625rem] font-bold text-slate-400 uppercase tracking-wider">
          System Grounded Agent
        </span>
      </div>
    </div>
  );
}

export function ThinkingBubble() {
  return (
    <div className="flex justify-start items-center gap-3 animate-fade-up">
      <div className="h-8 w-8 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center font-bold text-xs shadow-sm">
        A
      </div>
      <div className="card flex items-center gap-2 rounded-2xl rounded-tl-sm px-4.5 py-3 border border-slate-200 shadow-sm bg-white">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-500 [animation-delay:-0.3s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.15s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-rose-500" />
        <span className="text-xs font-semibold text-slate-400 font-mono tracking-wider ml-1">
          Orchestrating agents...
        </span>
      </div>
    </div>
  );
}
