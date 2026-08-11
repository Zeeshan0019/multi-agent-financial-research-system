import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDocuments } from "../context/DocumentsContext.jsx";
import { getDocumentMetrics, getDocumentRedFlags, deleteDocument } from "../api/documents.js";
import MetricCard from "../components/MetricCard.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import Citation from "../components/Citation.jsx";
import CountUp from "../components/CountUp.jsx";

const STATUS_STYLE = {
  ready:      "bg-green-50 text-green-700 border border-green-200/50",
  processing: "bg-amber-50 text-amber-600 border border-amber-200/50",
  failed:     "bg-rose-50 text-rose-700 border border-rose-200/50",
};

const AVATAR_COLORS = [
  "linear-gradient(135deg,#8B5CF6,#6D28D9)",
  "linear-gradient(135deg,#14B8A6,#0D9488)",
  "linear-gradient(135deg,#FB7185,#E11D48)",
  "linear-gradient(135deg,#F5A524,#DB8B0B)",
  "linear-gradient(135deg,#3B82F6,#1D4ED8)",
];
function avatarColor(name = "") {
  const idx = name.split("").reduce((a, c) => a + c.charCodeAt(0), 0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[idx];
}

export default function Dashboard() {
  const { documents, loading, refresh, removeDocument } = useDocuments();
  const [expandedId, setExpandedId] = useState(null);
  const navigate = useNavigate();

  // Refresh every time we land on this page (handles post-upload navigation)
  useEffect(() => {
    refresh();
  }, []); // eslint-disable-line

  const readyCount = documents.filter((d) => d.status === "ready").length;

  function toggleRow(doc) {
    if (doc.status !== "ready") return;
    setExpandedId((cur) => (cur === doc.id ? null : doc.id));
  }

  async function handleDelete(e, docId) {
    e.stopPropagation();
    if (!window.confirm("Delete this document? This removes all extracted data and vector indexes.")) return;
    removeDocument(docId); // optimistic — remove from UI immediately
    await deleteDocument(docId).catch(() => refresh()); // roll back on error
    if (expandedId === docId) setExpandedId(null);
  }

  return (
    <div className="animate-fade-up">
      {/* Hero banner */}
      <div className="relative mb-8 overflow-hidden rounded-2xl border border-slate-200/80 bg-white px-8 py-9 shadow-[0_12px_30px_rgba(30,27,60,0.02)]">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full opacity-40 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(139,92,246,0.25) 0%, rgba(20,184,166,0.12) 100%)" }} />
        <div className="pointer-events-none absolute -bottom-20 left-1/3 h-52 w-52 rounded-full opacity-35 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(251,113,133,0.15) 0%, transparent 100%)" }} />
        <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-6 z-10">
          <div>
            <p className="mb-2 font-mono text-[0.68rem] font-bold uppercase tracking-[0.16em] text-violet-600">
              Research Workspace
            </p>
            <h1 className="font-display text-[2rem] font-extrabold leading-tight text-ledger-950">
              Coverage Overview
            </h1>
            <p className="mt-2.5 max-w-xl text-sm leading-relaxed text-ledger-950/60">
              Every document you upload is automatically indexed by the Document Agent, then analyzed by the Extraction and Red Flag agents. Click a row to see live metrics and risk indicators.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button onClick={() => refresh()}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 px-4 py-2.5 text-sm font-semibold text-ledger-950/70 shadow-sm transition-all">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              Refresh
            </button>
            <Link to="/upload"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-violet-600 hover:bg-violet-700 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-200 hover:-translate-y-0.5 transition-all duration-200">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 16V4"/><path d="M6 10l6-6 6 6"/><path d="M4 20h16"/>
              </svg>
              Upload Filing
            </Link>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mb-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryStat label="Documents indexed" value={documents.length} accent="#8B5CF6" />
        <SummaryStat label="Ready for analysis" value={readyCount} accent="#14B8A6" />
        <SummaryStat
          label="Sectors covered"
          value={new Set(documents.map((d) => d.sector).filter((s) => s && s !== "—")).size}
          accent="#FB7185"
        />
      </div>

      {/* Documents table */}
      <div className="card overflow-hidden border border-slate-200/80 shadow-md shadow-slate-100/20">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-100 text-ledger-950/50">
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Company / File</th>
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Filing</th>
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Sector</th>
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Uploaded</th>
                <th className="px-5 py-3.5 font-mono text-[0.68rem] font-bold uppercase tracking-wider">Status</th>
                <th className="px-5 py-3.5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading && documents.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-ledger-950/40 font-semibold">
                    <div className="flex items-center justify-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
                      Loading coverage…
                    </div>
                  </td>
                </tr>
              )}
              {!loading && documents.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-ledger-950/40">
                    <div className="flex flex-col items-center gap-3">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-300">
                        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                        <polyline points="14 2 14 8 20 8"/>
                      </svg>
                      <p className="font-semibold">No documents yet.</p>
                      <Link to="/upload" className="text-violet-600 text-xs font-bold underline">Upload a PDF filing to start →</Link>
                    </div>
                  </td>
                </tr>
              )}
              {documents.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  expanded={expandedId === doc.id}
                  onToggle={() => toggleRow(doc)}
                  onDelete={(e) => handleDelete(e, doc.id)}
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

function DocumentRow({ doc, expanded, onToggle, onDelete }) {
  const [metrics, setMetrics] = useState(null);
  const [flags, setFlags] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!expanded || metrics) return;
    setDetailLoading(true);
    Promise.all([getDocumentMetrics(doc.id), getDocumentRedFlags(doc.id)]).then(([m, f]) => {
      setMetrics(m);
      setFlags(f);
      setDetailLoading(false);
    });
  }, [expanded, doc.id, metrics]);

  // Reset detail cache when doc status changes to ready (just finished processing)
  useEffect(() => {
    if (doc.status === "ready") {
      setMetrics(null);
      setFlags(null);
    }
  }, [doc.status]);

  const companyName = doc.company || doc.fileName?.replace(/\.pdf$/i, "") || "Unknown";
  const initials = companyName.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";

  return (
    <>
      <tr
        onClick={() => onToggle(doc)}
        className={`transition-all duration-200 ${
          doc.status === "ready" ? "cursor-pointer hover:bg-violet-50/20" : "opacity-80"
        } ${expanded ? "bg-violet-50/40" : ""}`}
      >
        <td className="px-5 py-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-display text-xs font-bold text-white shadow-sm"
              style={{ background: avatarColor(companyName) }}>
              {initials}
            </span>
            <div>
              <p className="font-semibold text-ledger-950">{companyName}</p>
              {doc.fileName && (
                <p className="font-mono text-[0.65rem] text-ledger-950/35 truncate max-w-[180px]">{doc.fileName}</p>
              )}
            </div>
          </div>
        </td>
        <td className="px-5 py-4 text-ledger-950/70 font-medium">
          {doc.docType !== "—" ? doc.docType : "Annual Report"}
          {doc.fiscalYear && doc.fiscalYear !== "—" ? ` · ${doc.fiscalYear}` : ""}
        </td>
        <td className="px-5 py-4 text-ledger-950/65 font-medium">{doc.sector && doc.sector !== "—" ? doc.sector : "—"}</td>
        <td className="px-5 py-4 text-ledger-950/50 font-medium">
          {new Date(doc.uploadedAt).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
        </td>
        <td className="px-5 py-4">
          <span className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 font-mono text-[0.65rem] font-bold uppercase tracking-wider ${STATUS_STYLE[doc.status] || STATUS_STYLE.processing}`}>
            {doc.status === "processing" && (
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-ping" />
            )}
            {doc.status}
          </span>
        </td>
        <td className="px-5 py-4">
          <button onClick={onDelete}
            className="p-1.5 rounded-lg text-slate-300 hover:text-rose-500 hover:bg-rose-50 transition-all">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14H6L5 6"/>
              <path d="M10 11v6"/><path d="M14 11v6"/>
              <path d="M9 6V4h6v2"/>
            </svg>
          </button>
        </td>
      </tr>

      {/* Expanded detail row */}
      {expanded && (
        <tr className="bg-violet-50/15">
          <td colSpan={6} className="px-6 py-6 border-t border-slate-100">
            {detailLoading && (
              <div className="flex items-center gap-2.5 text-sm text-ledger-950/45 py-2 font-medium">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
                Retrieving insights from Extraction & Red Flag agents…
              </div>
            )}
            {!detailLoading && metrics && (
              <div className="animate-fade-up space-y-6">
                {/* Extraction Agent */}
                <div>
                  <div className="mb-4 flex items-center justify-between">
                    <p className="eyebrow flex items-center gap-1.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-violet-600" />
                      Extraction Agent Output
                    </p>
                    {metrics.citation && (
                      <Citation index="M" label={companyName} section={metrics.citation.section} />
                    )}
                  </div>
                  {!metrics.highlights || metrics.highlights.length === 0 ? (
                    <p className="text-sm text-ledger-950/40">No metrics extracted yet — the Extraction Agent may still be running.</p>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {metrics.highlights.map((h) => <MetricCard key={h.label} {...h} />)}
                    </div>
                  )}
                </div>

                {/* Red Flag Agent */}
                <div>
                  <p className="eyebrow mb-4 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
                    Red Flag Agent Findings
                  </p>
                  {!flags || flags.length === 0 ? (
                    <div className="card px-5 py-4 border-l-4 border-l-green-500 bg-white/60">
                      <p className="text-sm text-green-700 font-semibold flex items-center gap-2">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <path d="M20 6L9 17l-5-5"/>
                        </svg>
                        No material anomalies detected.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3.5">
                      {flags.map((f, i) => (
                        <div key={i} className="card card-hover px-5 py-4 border-l-[3.5px] border-l-rose-400 bg-white/60">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <RiskBadge severity={f.severity} />
                            <p className="text-sm font-bold text-ledger-950">{f.title}</p>
                            {f.citation && <Citation index={i + 1} label={companyName} section={f.citation.section} />}
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
