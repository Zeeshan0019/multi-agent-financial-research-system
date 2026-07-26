import React from "react";

export default function MetricCard({ label, value, sublabel }) {
  return (
    <div className="card p-4">
      <p className="label">{label}</p>
      <p className="text-xl font-serif font-semibold text-ledger-950 mt-1">
        {value ?? "—"}
      </p>
      {sublabel && <p className="text-xs text-ledger-950/50 mt-0.5">{sublabel}</p>}
    </div>
  );
}
