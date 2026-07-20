import React from "react";

export default function ChatBubble({ role, content, citations }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-ledger-950 text-parchment-50 rounded-br-sm"
            : "bg-white border border-parchment-200 text-ledger-950 rounded-bl-sm"
        }`}
      >
        <p className="whitespace-pre-wrap">{content}</p>

        {citations && citations.length > 0 && (
          <div className="mt-3 pt-3 border-t border-ledger-950/10 flex flex-wrap gap-1.5">
            {citations.map((c, i) => (
              <span
                key={i}
                title={c.snippet}
                className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-600 px-2 py-0.5 text-[11px] font-mono"
              >
                p.{c.page ?? "?"} {c.document_id ? `· ${c.document_id.slice(0, 6)}` : ""}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
