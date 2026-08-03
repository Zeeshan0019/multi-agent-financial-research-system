import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useSession } from "../context/SessionContext.jsx";
import { listDocuments, getDocumentMetrics, getDocumentRedFlags } from "../api/documents.js";
import MetricCard from "../components/MetricCard.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import Citation from "../components/Citation.jsx";
import CountUp from "../components/CountUp.jsx";

const STATUS_STYLE = {
  ready: "bg-green-50 text-green-700 border border-green-200/50",
  processing: "bg-amber-50 text-amber-600 border border-amber-200/50 animate-pulse",
  error: "bg-rose-50 text-rose-700 border border-rose-200/50",
};

const AVATAR_COLORS = [
  "linear-gradient(135deg,#8B5CF6,#6D28D9)",
  "linear-gradient(135deg,#14B8A6,#0D9488)",
  "linear-gradient(135deg,#FB7185,#E11D48)",
  "linear-gradient(135deg,#F5A524,#DB8B0B)",
];

function avatarColor(name) {
  const idx = name.split("").reduce((a, c) => a + c.charCodeAt(0), 0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[idx];
}

export default function Dashboard() {
  const { activeSession, activeSessionId } = useSession();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    if (!activeSessionId) return;
    setLoading(true);
    listDocuments(activeSessionId).then((docs) => {
      setDocuments(docs);
      setLoading(false);
    });
  }, [activeSessionId]);

  const readyCount = documents.filter((d) => d.status === "ready").length;

  function toggleRow(doc) {
    if (doc.status !== "ready") return;
    setExpandedId((cur) => (cur === doc.id ? null : doc.id));
  }

  return (
    <div className="animate-fade-up">
      {/* Hero banner */}
      <div
        className="relative mb-8 overflow-hidden rounded-2xl border border-slate-200/80 bg-white px-8 py-9 shadow-[0_12px_30px_rgba(30,27,60,0.02)]"
      >
        <div
          className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full opacity-40 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(139,92,246,0.25) 0%, rgba(20,184,166,0.12) 100%)" }}
        />
        <div
          className="pointer-events-none absolute -bottom-20 left-1/3 h-52 w-52 rounded-full opacity-35 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(251,113,133,0.15) 0%, transparent 100%)" }}
        />
        <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-6 z-10">
          <div>
            <p className="mb-2 font-mono text-[0.68rem] font-bold uppercase tracking-[0.16em] text-violet-600">
              {activeSession ? activeSession.name : "Research Workspace"}
            </p>
            <h1 className="font-display text-[2rem] font-extrabold leading-tight text-ledger-950">
              Coverage Overview
            </h1>
            <p className="mt-2.5 max-w-xl text-sm leading-relaxed text-ledger-950/60">
              Every document below is automatically indexed by the **Document Agent**, and analyzed by the **Extraction** and **Red Flag** agents. Click a row to see the live metrics and risk indicators, or ask questions in the **Research** workspace.
            </p>
          </div>
          <Link
            to="/upload"
            className="shrink-0 inline-flex items-center justify-center gap-2 rounded-xl bg-violet-600 hover:bg-violet-700 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-200 hover:-translate-y-0.5 transition-all duration-200"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 16V4" />
              <path d="M6 10l6-6 6 6" />
              <path d="M4 20h16" />
            </svg>
            Upload Filing
          </Link>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mb-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryStat label="Documents indexed" value={documents.length} accent="#8B5CF6" />
        <SummaryStat label="Ready for analysis" value={readyCount} accent="#14B8A6" />
        <SummaryStat
          label="Flagged for risk"
          value={documents.filter((d) => d.overallRisk && d.overallRisk !== "low").length}
          accent="#FB7185"
        />
      </div>

      {/* Documents table list */}
      <div className="card overflow-hidden border border-slate-200/80 shadow-md shadow-slate-100/20">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-100 text-ledger-950/50">
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Company</th>
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Filing</th>
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Sector</th>
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Uploaded</th>
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-ledger-950/40 font-semibold">
                    <div className="flex items-center justify-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
                      Loading coverage…
                    </div>
                  </td>
                </tr>
              )}
              {!loading && documents.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-10 text-center text-ledger-950/40">
                    No documents yet. Upload a filing to start the multi-agent pipeline.
                  </td>
                </tr>
              )}
              {documents.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  expanded={expandedId === doc.id}
                  onToggle={() => toggleRow(doc)}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SummaryStat({ label, value, accent }) {
  return (
    <div className="card card-hover px-5 py-4 border-t-[3.5px]" style={{ borderTopColor: accent }}>
      <div className="mb-2 flex items-center justify-between">
        <p className="eyebrow" style={{ color: accent }}>{label}</p>
        <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: accent }} />
      </div>
      <p className="font-display text-3xl font-bold text-ledger-950 tracking-tight">
        <CountUp value={value} />
      </p>
    </div>
  );
}

function DocumentRow({ doc, expanded, onToggle }) {
  const [metrics, setMetrics] = useState(null);
  const [flags, setFlags] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!expanded || metrics) return;
    setLoading(true);
    Promise.all([getDocumentMetrics(doc.id), getDocumentRedFlags(doc.id)]).then(
      ([m, f]) => {
        setMetrics(m);
        setFlags(f);
        setLoading(false);
      }
    );
  }, [expanded]);

  const initials = doc.company
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <>
      <tr
        onClick={() => onToggle(doc)}
        className={`transition-all duration-200 ${
          doc.status === "ready" ? "cursor-pointer hover:bg-violet-50/20" : "opacity-75"
        } ${expanded ? "bg-violet-50/40" : ""}`}
      >
        <td className="px-5 py-4">
          <div className="flex items-center gap-3">
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-display text-xs font-bold text-white shadow-sm"
              style={{ background: avatarColor(doc.company) }}
            >
              {initials}
            </span>
            <div>
              <p className="font-semibold text-ledger-950">{doc.company}</p>
              <p className="font-mono text-xs text-ledger-950/40 font-medium">{doc.fiscalYear || "—"}</p>
            </div>
          </div>
        </td>
        <td className="px-5 py-4 text-ledger-950/70 font-medium">
          {doc.pages ? `${doc.pages} pages` : "Filing"}
        </td>
        <td className="px-5 py-4 text-ledger-950/65 font-medium">{doc.fiscalYear || "—"}</td>
        <td className="px-5 py-4 text-ledger-950/50 font-medium">
          {new Date(doc.uploadedAt).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric",
          })}
        </td>
        <td className="px-5 py-4">
          <span
            className={`inline-flex items-center rounded-lg px-2.5 py-1 font-mono text-[0.65rem] font-bold uppercase tracking-wider ${STATUS_STYLE[doc.status]}`}
          >
            {doc.status}
          </span>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-violet-50/15">
          <td colSpan={5} className="px-6 py-6 border-t border-slate-100">
            {loading && (
              <div className="flex items-center gap-2.5 text-sm text-ledger-950/45 py-2 font-medium">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
                Retrieving insights from Extraction & Red Flag agents…
              </div>
            )}
            {!loading && metrics && (
              <div className="animate-fade-up space-y-6">
                <div>
                  <div className="mb-4 flex items-center justify-between">
                    <p className="eyebrow flex items-center gap-1.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-violet-600" />
                      Extraction Agent Output
                    </p>
                    {metrics.citation && (
                      <Citation index="M" label={`${doc.company} ${doc.fiscalYear}`} section={metrics.citation.section} />
                    )}
                  </div>
                  {metrics.highlights.length === 0 ? (
                    <p className="text-sm text-ledger-950/40">No key metrics extracted yet.</p>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {metrics.highlights.map((h) => (
                        <MetricCard key={h.label} {...h} />
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <p className="eyebrow mb-4 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-coral-500" />
                    Red Flag Agent Findings
                  </p>
                  {flags.length === 0 ? (
                    <div className="card px-5 py-4 border-l-4 border-l-green-500 bg-white/60">
                      <p className="text-sm text-green-700 font-semibold flex items-center gap-2">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <path d="M20 6L9 17l-5-5" />
                        </svg>
                        All checks passed: No material anomalies detected.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3.5">
                      {flags.map((f, i) => (
                        <div key={i} className="card card-hover px-5 py-4 border-l-[3.5px] border-l-rose-400 bg-white/60">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <RiskBadge severity={f.severity} />
                            <p className="text-sm font-bold text-ledger-950">{f.title}</p>
                            <Citation index={i + 1} label={`${doc.company} ${doc.fiscalYear}`} section={f.citation.section} />
                          </div>
                          <p className="text-xs leading-relaxed text-ledger-950/60 font-medium">{f.detail}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
