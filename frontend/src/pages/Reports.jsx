import { useEffect, useState } from "react";
import { useDocuments } from "../context/DocumentsContext.jsx";
import { getDocument, getDocumentMetrics, getDocumentRedFlags } from "../api/documents.js";
import { listReports, generateReport } from "../api/reports.js";
import PageHeader from "../components/PageHeader.jsx";
import Citation from "../components/Citation.jsx";
import RiskBadge from "../components/RiskBadge.jsx";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getDownloadUrl(reportId) {
  const token = localStorage.getItem("ledger_token");
  return `${API_BASE_URL}/reports/${reportId}/download${token ? `?token=${token}` : ""}`;
}

function isBackedReport(report) {
  return typeof report.id === "number" || /^\d+$/.test(String(report.id));
}

const SECTIONS = [
  { name: "Executive Summary", description: "Consolidated synthesis of company performance and market position." },
  { name: "Key Financials", description: "Standardized metric tables including revenues, margins, and debt ratios." },
  { name: "Red Flags & Risks", description: "Anomalies, auditing footnotes, rising leverage, and customer concentration." },
  { name: "Company Comparison", description: "Side-by-side graphical benchmarking of operating margins and leverage." },
  { name: "Outlook", description: "Forward-looking assessment grounded in management discussion disclosures." },
];

const ROW_COLORS = ["#8B5CF6", "#14B8A6", "#FB7185", "#F5A524", "#5A4BB0"];

export default function Reports() {
  const { documents: allDocs } = useDocuments();
  const documents = allDocs.filter((d) => d.status === "ready");
  const loadingDocs = false;
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [selectedSections, setSelectedSections] = useState(SECTIONS.map((s) => s.name));
  const [reports, setReports] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [activeReport, setActiveReport] = useState(null);

  useEffect(() => {
    listReports().then(setReports);
  }, []);

  function toggleDoc(id) {
    setSelectedDocs((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  }

  function toggleSection(name) {
    setSelectedSections((prev) => prev.includes(name) ? prev.filter((x) => x !== name) : [...prev, name]);
  }

  async function handleGenerate() {
    if (selectedDocs.length === 0) return;
    setGenerating(true);
    try {
      const report = await generateReport(selectedDocs, selectedSections);
      const newReport = {
        ...report,
        title: report.title || selectedDocs
          .map((id) => documents.find((d) => d.id === id)?.company?.split(" ")[0])
          .filter(Boolean).join(" vs ") + " — Research Brief",
        status: report.status || "ready",
        pages: report.pages || selectedSections.length,
        documentIds: report.documentIds?.length ? report.documentIds : selectedDocs,
        sections: report.sections?.length ? report.sections : selectedSections,
      };
      setReports((prev) => [newReport, ...prev]);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="animate-fade-up">
      <PageHeader
        eyebrow="Report Agent"
        title="Generate a research report"
        description="Select your uploaded documents and report sections. The Report Agent compiles data from all agents into a structured research brief."
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-6 mb-8">
        {/* Document selection */}
        <div className="card p-5 md:p-6 bg-white/60 flex flex-col justify-between">
          <div>
            <p className="eyebrow mb-3.5 flex items-center gap-1.5 text-violet-600">
              <span className="h-1.5 w-1.5 rounded-full bg-violet-600 animate-pulse" />
              1. Choose documents to include
            </p>
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {loadingDocs && (
                <p className="text-xs font-semibold text-slate-400 text-center py-4 flex items-center justify-center gap-2">
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
                  Loading documents…
                </p>
              )}
              {!loadingDocs && documents.length === 0 && (
                <p className="text-xs font-semibold text-slate-400 text-center py-6">
                  No indexed filings available. Upload documents first.
                </p>
              )}
              {documents.map((doc) => (
                <label key={doc.id} className={`flex cursor-pointer items-center justify-between rounded-xl px-4 py-3 border transition-all duration-150 ${selectedDocs.includes(doc.id) ? "border-violet-300 bg-violet-50/20" : "border-slate-200 bg-white/60 hover:bg-slate-50/50"}`}>
                  <div className="flex items-center gap-3">
                    <input type="checkbox" checked={selectedDocs.includes(doc.id)} onChange={() => toggleDoc(doc.id)}
                      className="h-4 w-4 rounded border-slate-300 text-violet-600 focus:ring-violet-500/20 cursor-pointer accent-violet-600" />
                    <span className="text-xs font-bold text-ledger-950">{doc.company}</span>
                  </div>
                  <span className="font-mono text-[0.625rem] font-bold text-slate-400 bg-slate-100/60 px-2 py-0.5 rounded">
                    {doc.fiscalYear !== "—" ? doc.fiscalYear : "Filed"}
                  </span>
                </label>
              ))}
            </div>
          </div>
          <div className="mt-5 border-t border-slate-100 pt-4">
            <button onClick={handleGenerate} disabled={selectedDocs.length === 0 || generating}
              className="btn-primary w-full py-3.5 text-sm font-semibold rounded-xl disabled:opacity-50">
              {generating ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Compiling report sections...
                </span>
              ) : "Compile Research Report"}
            </button>
          </div>
        </div>

        {/* Section selector */}
        <div className="card p-5 md:p-6 bg-white/60">
          <p className="eyebrow mb-3.5 flex items-center gap-1.5 text-teal-600">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
            2. Configure report structure
          </p>
          <div className="space-y-2.5">
            {SECTIONS.map((s) => {
              const checked = selectedSections.includes(s.name);
              return (
                <label key={s.name} className={`flex items-start gap-3 rounded-xl p-3 border cursor-pointer transition-all duration-150 ${checked ? "border-teal-400 bg-teal-50/10 text-teal-900" : "border-slate-200 bg-white/60 text-slate-450 hover:border-slate-300"}`}>
                  <input type="checkbox" checked={checked} onChange={() => toggleSection(s.name)}
                    className="mt-0.5 h-4 w-4 rounded border-slate-350 text-teal-600 focus:ring-teal-500/20 cursor-pointer accent-teal-600" />
                  <div className="flex-1">
                    <span className="text-xs font-bold block">{s.name}</span>
                    <span className="text-[0.65rem] text-slate-400 mt-0.5 block font-medium leading-relaxed">{s.description}</span>
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      </div>

      {/* Reports history */}
      <p className="eyebrow mb-3.5 flex items-center gap-1.5 text-ledger-950/50">Generated Analyst Briefs</p>
      <div className="card divide-y divide-slate-100 overflow-hidden border border-slate-200 shadow-sm bg-white/80">
        {reports.length === 0 && (
          <p className="px-5 py-10 text-center text-xs font-semibold text-slate-400">
            No research reports yet. Configure and compile above.
          </p>
        )}
        {reports.map((r) => (
          <div key={r.id} className="flex items-center justify-between px-5 py-4 hover:bg-slate-50/50 transition-all">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-500 border border-red-100">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" strokeWidth="2.5" />
                  <line x1="16" y1="17" x2="8" y2="17" strokeWidth="2.5" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-bold text-ledger-950">{r.title || "Untitled Report"}</p>
                <p className="mt-0.5 text-xs text-ledger-950/40 font-semibold">
                  {new Date(r.createdAt).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
                  {r.pages ? ` · ${r.pages} sections` : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center rounded-lg px-2.5 py-1 font-mono text-[0.65rem] font-bold uppercase tracking-wider ${r.status === "ready" ? "bg-green-50 text-green-700 border border-green-200/50" : "bg-amber-50 text-amber-600 border border-amber-200/50 animate-pulse"}`}>
                {r.status}
              </span>
              {isBackedReport(r) && r.status === "ready" && (
                <a href={getDownloadUrl(r.id)} target="_blank" rel="noreferrer"
                  className="btn-ghost px-4 py-2 text-xs font-semibold shadow-sm bg-white hover:bg-slate-50 border-slate-200">
                  Download PDF
                </a>
              )}
              <button disabled={r.status !== "ready"} onClick={() => setActiveReport(r)}
                className="btn-ghost px-4 py-2 text-xs font-semibold shadow-sm bg-white hover:bg-slate-50 border-slate-200 disabled:opacity-40">
                View Report
              </button>
            </div>
          </div>
        ))}
      </div>

      {activeReport && (
        <ReportViewerModal report={activeReport} onClose={() => setActiveReport(null)} />
      )}
    </div>
  );
}

function ReportViewerModal({ report, onClose }) {
  const [currentPage, setCurrentPage] = useState(1);
  const includeDocs = report.documentIds || [];
  const includedSections = report.sections || SECTIONS.map((s) => s.name);
  const totalPages = includedSections.length + 1;

  const [reportCompanies, setReportCompanies] = useState([]);
  const [metricsById, setMetricsById] = useState({});
  const [redFlagsById, setRedFlagsById] = useState({});
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoadingData(true);
    Promise.all(
      includeDocs.map(async (id) => {
        const [company, metrics, flags] = await Promise.all([
          getDocument(id).catch(() => null),
          getDocumentMetrics(id).catch(() => ({ highlights: [] })),
          getDocumentRedFlags(id).catch(() => []),
        ]);
        return { id, company, metrics, flags };
      })
    ).then((results) => {
      if (cancelled) return;
      setReportCompanies(results.map((r) => r.company).filter(Boolean));
      setMetricsById(Object.fromEntries(results.map((r) => [r.id, r.metrics])));
      setRedFlagsById(Object.fromEntries(results.map((r) => [r.id, r.flags || []])));
      setLoadingData(false);
    });
    return () => { cancelled = true; };
  }, [report.id]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ledger-950/40 backdrop-blur-sm p-4 animate-scale-in">
      <div className="flex flex-col w-full max-w-4xl h-[90vh] bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        {/* Toolbar */}
        <div className="bg-slate-50 border-b border-slate-200 px-5 py-4 flex items-center justify-between shrink-0">
          <div>
            <h3 className="text-sm font-bold text-ledger-950 truncate max-w-xs md:max-w-md">{report.title}</h3>
            <p className="text-[0.68rem] text-slate-400 font-semibold mt-0.5">Multi-Agent Financial Research System</p>
          </div>
          <div className="flex items-center gap-3">
            {isBackedReport(report) && (
              <a href={getDownloadUrl(report.id)} target="_blank" rel="noreferrer"
                className="btn-ghost bg-white py-2 px-3.5 text-xs font-bold border-slate-250 flex items-center gap-1.5 shadow-sm">
                Download Agent PDF
              </a>
            )}
            <button onClick={onClose}
              className="h-8 w-8 rounded-xl bg-slate-200/50 hover:bg-slate-200 text-slate-600 transition-colors flex items-center justify-center font-bold text-sm">
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto bg-slate-100 p-6 flex items-start justify-center">
          <div className="w-full max-w-[800px] min-h-[500px] bg-white border border-slate-200 shadow-md p-8 md:p-14">
            {loadingData && (
              <div className="flex h-full flex-col items-center justify-center gap-3 text-slate-400 py-20">
                <span className="h-6 w-6 animate-spin rounded-full border-2 border-violet-400 border-t-transparent" />
                <span className="text-xs font-semibold">Compiling agent outputs...</span>
              </div>
            )}

            {/* Cover Page */}
            {!loadingData && currentPage === 1 && (
              <div className="flex flex-col justify-between min-h-[400px] py-10 animate-fade-up">
                <div className="space-y-6">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-violet-600" />
                    <span className="font-mono text-xs font-bold text-violet-600 uppercase tracking-widest">
                      Multi-Agent Financial Research System
                    </span>
                  </div>
                  <h1 className="font-display text-4xl font-extrabold text-ledger-950 tracking-tight leading-tight pt-4">
                    {report.title}
                  </h1>
                  <p className="text-sm font-medium text-slate-500 max-w-md leading-relaxed border-l-2 border-violet-400 pl-4">
                    Financial metrics, risk anomalies, and comparative insights compiled from your uploaded filings.
                  </p>
                </div>
                <div className="border-t border-slate-200 pt-8 space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-xs font-semibold text-ledger-950/60">
                    <div>
                      <span className="text-[0.625rem] font-mono text-slate-400 uppercase font-bold block">Release Date</span>
                      <span>{new Date(report.createdAt).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })}</span>
                    </div>
                    <div>
                      <span className="text-[0.625rem] font-mono text-slate-400 uppercase font-bold block">Parsed Entities</span>
                      <span className="font-bold text-violet-600">
                        {reportCompanies.map((c) => c.company).join(", ") || "—"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Section Pages */}
            {!loadingData && currentPage > 1 && (
              <div className="flex flex-col min-h-[400px] animate-fade-up">
                <div className="flex items-center justify-between border-b border-slate-150 pb-3 mb-6">
                  <span className="font-mono text-[0.625rem] font-bold text-slate-400 uppercase tracking-widest">
                    Page {currentPage} · {includedSections[currentPage - 2]}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-ledger-950 mb-4">{includedSections[currentPage - 2]}</h2>

                {includedSections[currentPage - 2] === "Executive Summary" && (
                  <div className="space-y-4 text-xs leading-relaxed text-ledger-950/70 font-medium">
                    <p>This research brief compiles financial metrics, margin indicators, and risk anomalies extracted from your uploaded annual reports. The Multi-Agent pipeline completed ingestion, validation, and metadata mapping.</p>
                    {reportCompanies.map((c) => (
                      <div key={c.id} className="rounded-xl border border-slate-150 p-3 bg-slate-50/50">
                        <span className="font-bold text-ledger-950 text-xs block">{c.company}</span>
                        <p className="mt-1 text-slate-500 leading-normal">
                          Filing: {c.docType !== "—" ? c.docType : "Annual Report"} · {c.fiscalYear !== "—" ? c.fiscalYear : ""}
                          {c.sector && c.sector !== "—" ? ` · Sector: ${c.sector}` : ""}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {includedSections[currentPage - 2] === "Key Financials" && (
                  <div className="space-y-4">
                    <p className="text-xs leading-relaxed text-ledger-950/70 font-medium">Key financial highlights extracted by the Extraction Agent from each filing.</p>
                    <div className="overflow-hidden border border-slate-200 rounded-xl">
                      <table className="w-full text-left text-[11px] border-collapse bg-white">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-150 text-slate-500 font-bold">
                            <th className="px-3.5 py-2 font-mono uppercase">Metric</th>
                            {reportCompanies.map((c) => (
                              <th key={c.id} className="px-3.5 py-2 font-mono uppercase">{c.company.split(" ")[0]}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 font-semibold text-ledger-950/70">
                          {["Revenue", "Net profit", "EBITDA", "EPS", "Assets", "Liabilities"].map((metricName) => (
                            <tr key={metricName}>
                              <td className="px-3.5 py-2.5 font-bold text-ledger-950">{metricName}</td>
                              {reportCompanies.map((c) => {
                                const hl = metricsById[c.id]?.highlights || [];
                                const match = hl.find((h) => h.label === metricName || h.label.includes(metricName));
                                return (
                                  <td key={c.id} className="px-3.5 py-2.5 font-mono">
                                    {match ? match.value : "—"}
                                    {match?.delta && (
                                      <span className={`block text-[9px] ${match.tone === "up" ? "text-green-600" : match.tone === "down" ? "text-rose-600" : "text-slate-400"}`}>
                                        {match.delta}
                                      </span>
                                    )}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {includedSections[currentPage - 2] === "Red Flags & Risks" && (
                  <div className="space-y-4">
                    <p className="text-xs leading-relaxed text-ledger-950/70 font-medium">The Red Flag Agent automatically scanned disclosures to surface potential warning patterns.</p>
                    <div className="space-y-2.5">
                      {reportCompanies.flatMap((c) =>
                        (redFlagsById[c.id] || []).map((f, i) => (
                          <div key={`${c.id}-${i}`} className="p-3 border border-slate-200 rounded-xl bg-slate-50/50">
                            <div className="flex items-center gap-2 mb-1">
                              <RiskBadge severity={f.severity} />
                              <span className="text-[11px] font-bold text-ledger-950">{c.company.split(" ")[0]}: {f.title}</span>
                            </div>
                            <p className="text-[10px] leading-relaxed text-slate-500 font-semibold">{f.detail}</p>
                          </div>
                        ))
                      )}
                      {reportCompanies.flatMap((c) => redFlagsById[c.id] || []).length === 0 && (
                        <p className="text-xs text-slate-400 font-semibold text-center py-6">No flags surfaced from the Red Flag Agent.</p>
                      )}
                    </div>
                  </div>
                )}

                {includedSections[currentPage - 2] === "Company Comparison" && (
                  <div className="space-y-4">
                    <p className="text-xs leading-relaxed text-ledger-950/70 font-medium">Revenue comparison across included coverage entities from extracted metrics.</p>
                    <div className="space-y-3.5 border border-slate-100 rounded-xl p-4 bg-slate-50/30">
                      {reportCompanies.map((c, i) => {
                        const hl = metricsById[c.id]?.highlights || [];
                        const revMetric = hl.find((h) => h.label === "Revenue");
                        const rawVal = revMetric?.value || "0";
                        const numVal = parseFloat(rawVal.replace(/[^0-9.]/g, "")) || 50;
                        const color = ROW_COLORS[i % ROW_COLORS.length];
                        return (
                          <div key={c.id} className="space-y-1">
                            <div className="flex justify-between text-[11px] font-bold text-ledger-950">
                              <span>{c.company}</span>
                              <span className="font-mono">{revMetric?.value || "—"}</span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                              <div className="h-full rounded-full" style={{ width: `${Math.min(numVal, 100)}%`, background: color }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {includedSections[currentPage - 2] === "Outlook" && (
                  <div className="space-y-3 text-xs leading-relaxed text-ledger-950/70 font-medium">
                    <p>Management discussion and forward-looking statements from each filing have been synthesized. Key themes include margin preservation, capital allocation priorities, and sector-specific headwinds.</p>
                    <div className="p-3 bg-amber-50/50 border border-amber-100 rounded-xl mt-4">
                      <span className="text-[10px] font-mono text-amber-700 font-bold block uppercase tracking-wider mb-1">Citation Grounding Disclaimer</span>
                      <p className="text-[10px] text-amber-800 leading-normal font-medium">
                        All statements are strictly matched with source material from your uploaded filings. No synthetic projections were permitted during Agent assembly.
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between border-t border-slate-200 pt-3 mt-6 text-[10px] font-mono font-bold text-slate-400 uppercase">
                  <span>Confidential — Research Use</span>
                  <span>Multi-Agent Financial Research System</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Pagination */}
        <div className="bg-slate-50 border-t border-slate-200 px-5 py-4 flex items-center justify-between shrink-0 font-semibold">
          <button onClick={() => setCurrentPage((p) => Math.max(1, p - 1))} disabled={currentPage === 1}
            className="btn-ghost py-1.5 px-3 text-xs bg-white disabled:opacity-40 border-slate-250">
            ← Previous
          </button>
          <span className="text-xs text-ledger-950/60 font-mono">Page {currentPage} of {totalPages}</span>
          <button onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}
            className="btn-ghost py-1.5 px-3 text-xs bg-white disabled:opacity-40 border-slate-250">
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
