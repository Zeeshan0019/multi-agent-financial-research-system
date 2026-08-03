import { useEffect, useState } from "react";
import { useSession } from "../context/SessionContext.jsx";
import { listDocuments } from "../api/documents.js";
import { compareDocuments } from "../api/comparison.js";
import PageHeader from "../components/PageHeader.jsx";
import Citation from "../components/Citation.jsx";

// These four keys match what the Comparison Agent actually returns per
// company (backend schemas.CompanyComparison): revenue, net_profit, debt,
// margin. Units are left blank where the backend returns a formatted
// currency string rather than a bare percentage/ratio.
const METRIC_DETAILS = [
  { key: "revenue", label: "Revenue", desc: "Total reported revenue for the period.", unit: "" },
  { key: "net_profit", label: "Net Profit", desc: "Bottom-line profit after tax.", unit: "" },
  { key: "debt", label: "Debt", desc: "Reported total debt position.", unit: "" },
  { key: "margin", label: "Margin", desc: "Reported profitability margin.", unit: "%" },
];

const ROW_COLORS = ["#8B5CF6", "#14B8A6", "#FB7185", "#F5A524", "#5A4BB0"];

export default function Comparison() {
  const { activeSessionId } = useSession();
  const [documents, setDocuments] = useState([]);
  const [selected, setSelected] = useState([]);
  const [metricKey, setMetricKey] = useState(METRIC_DETAILS[0].key);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeSessionId) return;
    listDocuments(activeSessionId).then((docs) => {
      const activeDocs = docs.filter((d) => d.status === "ready");
      setDocuments(activeDocs);
      // Pre-select first two companies if available
      if (activeDocs.length >= 2 && selected.length === 0) {
        setSelected([activeDocs[0].id, activeDocs[1].id]);
      }
    });
  }, [activeSessionId]);

  function toggle(id) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function run() {
    if (selected.length < 2) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await compareDocuments(activeSessionId, selected, metricKey);
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const activeMetricObj = METRIC_DETAILS.find((m) => m.key === metricKey) || METRIC_DETAILS[0];
  const maxValue = result ? Math.max(...result.rows.map((r) => r.value), 0.1) : 0;

  return (
    <div className="animate-fade-up">
      <PageHeader
        eyebrow="Comparison Agent"
        title="Benchmark companies"
        description="Select two or more indexed filings and an analyst metric. The Comparison Agent cross-references company filings side-by-side."
      />

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6 mb-8">
        {/* Company Selection Panel */}
        <div className="card p-5 md:p-6 bg-white/60">
          <p className="eyebrow mb-4 flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-600" />
            1. Select companies to compare
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {documents.map((doc, i) => {
              const color = ROW_COLORS[i % ROW_COLORS.length];
              const active = selected.includes(doc.id);
              const initials = doc.company.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase();
              return (
                <div
                  key={doc.id}
                  onClick={() => toggle(doc.id)}
                  className={`flex items-center gap-3.5 rounded-xl border p-4.5 cursor-pointer transition-all duration-200 ${
                    active
                      ? "border-violet-400 bg-violet-50/20 shadow-sm"
                      : "border-slate-200 bg-white/75 hover:bg-slate-50/50 hover:border-slate-300"
                  }`}
                >
                  <div
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-display text-xs font-bold text-white shadow-sm"
                    style={{ background: color }}
                  >
                    {initials}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-ledger-950 truncate">{doc.company}</p>
                    <p className="text-[0.68rem] font-bold text-slate-400 font-mono mt-0.5">{doc.fiscalYear || "Fiscal year not extracted"}</p>
                  </div>
                  <div className="shrink-0 flex items-center">
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => {}} // toggled on container click
                      className="h-4 w-4 rounded border-slate-350 text-violet-600 focus:ring-violet-500/20 cursor-pointer accent-violet-600"
                    />
                  </div>
                </div>
              );
            })}
            {documents.length === 0 && (
              <p className="col-span-2 text-sm text-ledger-950/45 font-semibold text-center py-6">
                No indexed files in session. Please upload filings first.
              </p>
            )}
          </div>
        </div>

        {/* Metric Selector Panel */}
        <div className="card p-5 md:p-6 bg-white/60">
          <p className="eyebrow mb-4 flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
            2. Choose financial metric
          </p>
          <div className="flex flex-col gap-2.5">
            {METRIC_DETAILS.map((m) => {
              const active = metricKey === m.key;
              return (
                <button
                  key={m.key}
                  onClick={() => setMetricKey(m.key)}
                  className={`w-full rounded-xl border p-3 text-left transition-all duration-200 ${
                    active
                      ? "border-teal-500 bg-teal-50/10 text-teal-900 shadow-sm"
                      : "border-slate-200 bg-white/70 text-slate-600 hover:border-slate-300 hover:bg-slate-50/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold">{m.label}</span>
                    <span className="font-mono text-[0.625rem] font-bold px-1.5 py-0.5 rounded bg-slate-100/80 text-slate-500">
                      {m.unit}
                    </span>
                  </div>
                  <p className="text-[0.65rem] text-slate-400 mt-1 font-medium leading-relaxed">{m.desc}</p>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex justify-center mb-8">
        <button
          onClick={run}
          disabled={selected.length < 2 || loading}
          className="btn-primary px-8 py-3.5 shadow-md shadow-violet-200/50 text-sm font-semibold rounded-xl"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Benchmarking filings...
            </span>
          ) : (
            `Benchmark ${selected.length} Companies`
          )}
        </button>
      </div>

      {result && (
        <div className="card animate-scale-in p-6 md:p-8 bg-white border border-slate-200 shadow-md">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <p className="eyebrow flex items-center gap-1.5 text-violet-600 mb-1">
                <span className="h-1.5 w-1.5 rounded-full bg-violet-600 animate-pulse" />
                Comparison Agent Report
              </p>
              <h2 className="text-lg font-bold text-ledger-950">{activeMetricObj.label}</h2>
            </div>
            {result.citation && (
              <Citation index={1} label="Comparison Agent" section={result.citation.section} />
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-[1fr_300px] gap-8">
            {/* SVG/CSS Chart Column */}
            <div className="space-y-6">
              <div className="relative border-b border-slate-200 pb-2">
                <p className="text-[0.68rem] font-mono font-bold text-slate-400 uppercase tracking-wider">
                  Side-By-Side Visualizer
                </p>
              </div>

              <div className="space-y-5 py-2">
                {result.rows.map((row, i) => {
                  const color = ROW_COLORS[i % ROW_COLORS.length];
                  const percentage = Math.max(5, (row.value / maxValue) * 100);
                  return (
                    <div key={row.company} className="space-y-1.5 group">
                      <div className="flex items-baseline justify-between text-xs">
                        <span className="flex items-center gap-2 font-semibold text-ledger-950">
                          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color }} />
                          {row.company}
                        </span>
                        <span className="font-mono font-bold text-ledger-950/80">
                          {row.displayValue ?? `${row.value.toFixed(1)}${activeMetricObj.unit}`}
                        </span>
                      </div>
                      <div className="relative h-4 w-full rounded-lg bg-slate-100/80 overflow-hidden shadow-inner border border-slate-200/20">
                        <div
                          className="h-full rounded-lg transition-all duration-700 ease-out shadow-sm flex items-center justify-end pr-2"
                          style={{
                            width: `${percentage}%`,
                            background: `linear-gradient(90deg, ${color}cc, ${color})`,
                          }}
                        >
                          <span className="text-[0.55rem] font-bold text-white font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                            {row.value.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Analyst Insights Column */}
            <div className="rounded-2xl bg-slate-50/80 border border-slate-200/60 p-5 flex flex-col justify-between shadow-inner">
              <div>
                <span className="eyebrow text-slate-500 block mb-2 font-bold text-[0.625rem]">
                  Comparison Summary
                </span>
                <p className="text-xs leading-relaxed text-ledger-950/70 font-semibold mb-4">
                  {result.summary || "No summary available for this comparison."}
                </p>
                <div className="space-y-2 border-t border-slate-150 pt-3">
                  <span className="text-[0.65rem] font-mono text-slate-400 font-bold uppercase block">
                    Analyzed Data Points:
                  </span>
                  <div className="flex justify-between items-center text-[0.68rem] text-ledger-950/60 font-semibold">
                    <span>Selected metric</span>
                    <span className="font-bold">{activeMetricObj.label}</span>
                  </div>
                  <div className="flex justify-between items-center text-[0.68rem] text-ledger-950/60 font-semibold">
                    <span>Highest value</span>
                    <span className="font-bold font-mono text-teal-600">
                      {maxValue.toFixed(1)}
                      {activeMetricObj.unit}
                    </span>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-150 pt-3.5 mt-4 text-[0.65rem] text-slate-400 leading-normal font-semibold">
                * Findings compiled automatically across all session filings via multi-agent grounding rules.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
