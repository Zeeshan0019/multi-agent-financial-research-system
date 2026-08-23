import Citation from "./Citation.jsx";

const TONE_STYLES = {
  up: "text-flag-low",
  down: "text-flag-high",
  flat: "text-ledger-950/50",
};

const TONE_GLYPH = {
  up: "▲",
  down: "▼",
  flat: "▬",
};

const TONE_BORDER = {
  up: "#16A34A",
  down: "#E11D48",
  flat: "#8B5CF6",
};

export default function MetricCard({ label, value, delta, tone = "flat", citation, citationIndex }) {
  return (
    <div
      className="card card-hover relative px-4 py-3.5 border-l-[3px]"
      style={{ borderLeftColor: TONE_BORDER[tone] }}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="eyebrow mb-1.5">{label}</p>
        {citation && (
          <Citation
            index={citationIndex ?? "S"}
            label={citation.label}
            page={citation.page}
            section={citation.section}
            snippet={citation.snippet}
          />
        )}
      </div>
      <p className="font-display text-2xl font-semibold text-ledger-950">{value}</p>
      {delta && delta !== "—" && delta !== "--" && (
        <p className={`mt-1 flex items-center gap-1 font-mono text-xs ${TONE_STYLES[tone]}`}>
          <span aria-hidden>{TONE_GLYPH[tone]}</span>
          {delta}
        </p>
      )}
    </div>
  );
}
