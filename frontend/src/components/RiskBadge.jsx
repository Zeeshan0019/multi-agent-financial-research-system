const STYLES = {
  high: "bg-flag-high/[0.12] text-flag-high border-flag-high/30",
  medium: "bg-flag-medium/[0.14] text-flag-medium border-flag-medium/35",
  low: "bg-flag-low/[0.12] text-flag-low border-flag-low/30",
};

const DOT = { high: "#E11D48", medium: "#F97316", low: "#16A34A" };
const LABELS = { high: "High risk", medium: "Watch", low: "Minor" };

export default function RiskBadge({ severity = "low" }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[0.65rem] font-medium uppercase tracking-wide ${STYLES[severity]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: DOT[severity] }} />
      {LABELS[severity]}
    </span>
  );
}
