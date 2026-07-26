import React from "react";

const STYLES = {
  low: "bg-flag-low/15 text-flag-low border-flag-low/30",
  medium: "bg-flag-medium/15 text-flag-medium border-flag-medium/30",
  high: "bg-flag-high/15 text-flag-high border-flag-high/30",
};

export default function RiskBadge({ severity = "medium" }) {
  const key = String(severity).toLowerCase();
  const style = STYLES[key] || STYLES.medium;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${style}`}
    >
      {key}
    </span>
  );
}
