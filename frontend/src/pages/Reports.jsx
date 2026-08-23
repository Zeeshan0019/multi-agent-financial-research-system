import { useEffect, useState } from "react";
import { useDocuments } from "../context/DocumentsContext.jsx";
import { getDocument, getDocumentMetrics, getDocumentRedFlags } from "../api/documents.js";
import { listReports, generateReport } from "../api/reports.js";
import PageHeader from "../components/PageHeader.jsx";
import RiskBadge from "../components/RiskBadge.jsx";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

function getDownloadUrl(id) {
  const token = localStorage.getItem("ledger_token");
  return `${API_BASE_URL}/reports/${id}/download${token ? `?token=${token}` : ""}`;
}

function isReal(report) {
  return typeof report.id === "number" || /^\d+$/.test(String(report.id));
}

const SECTIONS = [
  { name: "Executive Summary",  description: "Synthesis of company performance and pipeline findings." },
  { name: "Key Financials",     description: "Revenue, net income, EBITDA, EPS, assets, liabilities." },
  { name: "Red Flags & Risks",  description: "Anomalies, leverage warnings, auditor qualifications." },
  { name: "Company Comparison", description: "Side-by-side benchmarking across uploaded entities." },
  { name: "Outlook",            description: "Forward-looking assessment grounded in disclosures." },
];

export default function Reports() {
  const { documents: allDocs } = useDocuments();
  const documents = allDocs.filter((d) => d.status === "ready");
  const [selectedDocs, setSelectedDocs]       = useState([]);
  const [selectedSections, setSelectedSections] = useState(SECTIONS.map((s) => s.name));
  const [reports, setReports]     = useState([]);
  const [generating, setGenerating] = useState(false);
  const [activeReport, setActiveReport] = useState(null);

  useEffect(() => { listReports().then(setReports); }, []);

  function toggleDoc(id) {
    setSelectedDocs((p) => p.includes(id) ? p.filter((x) => x !== id) : [...p, id]);
  }
  function toggleSection(name) {
    setSelectedSections((p) => p.includes(name) ? p.filter((x) => x !== name) : [...p, name]);
  }

  async function handleGenerate() {
    if (!selectedDocs.length) return;
    setGenerating(true);
    try {
      const r = await generateReport(selectedDocs, selectedSections);
      const nr = {
        ...r,
        title: r.title || selectedDocs.map((id) => documents.find((d) => d.id === id)?.company?.split(" ")[0]).filter(Boolean).join(" vs ") + " — Research Brief",
        status: r.status || "ready",
        pages: r.pages || selectedSections.length,
        documentIds: r.documentIds?.length ? r.documentIds : selectedDocs,
        sections: r.sections?.length ? r.sections : selectedSections,
      };
      setReports((p) => [nr, ...p]);
    } catch (e) { console.error(e); }
    finally { setGenerating(false); }
  }

  return (
    <div className="animate-fade-up">
      <PageHeader eyebrow="Report Agent" title="Generate a research report"
        description="Select documents and sections. The Report Agent compiles all agent outputs into a structured analyst brief." />

      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-6 mb-8">
        {/* Doc selection */}
        <div className="card p-5 bg-white/60 flex flex-col justify-between">
          <div>
            <p className="eyebrow mb-3 flex items-center gap-1.5 text-violet-600">
              <span className="h-1.5 w-1.5 rounded-full bg-violet-600 animate-pulse" />
              1. Choose documents
            </p>
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {documents.length === 0 && <p className="text-xs text-slate-400 text-center py-6">No indexed documents. Upload first.</p>}
              {documents.map((doc) => (
                <label key={doc.id} className={`flex cursor-pointer items-center justify-between rounded-xl px-4 py-3 border transition-all ${selectedDocs.includes(doc.id) ? "border-violet-300 bg-violet-50/20" : "border-slate-200 bg-white/60 hover:bg-slate-50/50"}`}>
                  <div className="flex items-center gap-3">
                    <input type="checkbox" checked={selectedDocs.includes(doc.id)} onChange={() => toggleDoc(doc.id)} className="h-4 w-4 accent-violet-600" />
                    <span className="text-xs font-bold text-ledger-950">{doc.company}</span>
                  </div>
                  <span className="font-mono text-[0.6rem] font-bold text-slate-400 bg-slate-100/60 px-2 py-0.5 rounded">{doc.fiscalYear !== "—" ? doc.fiscalYear : "Filed"}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="mt-5 border-t border-slate-100 pt-4">
            <button onClick={handleGenerate} disabled={!selectedDocs.length || generating}
              className="btn-primary w-full py-3.5 text-sm rounded-xl disabled:opacity-50">
              {generating ? <span className="flex items-center justify-center gap-2"><span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"/>Compiling...</span> : "Compile Research Report"}
            </button>
          </div>
        </div>

        {/* Section selector */}
        <div className="card p-5 bg-white/60">
          <p className="eyebrow mb-3 flex items-center gap-1.5 text-teal-600">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
            2. Configure sections
          </p>
          <div className="space-y-2">
            {SECTIONS.map((s) => {
              const on = selectedSections.includes(s.name);
              return (
                <label key={s.name} className={`flex items-start gap-3 rounded-xl p-3 border cursor-pointer transition-all ${on ? "border-teal-400 bg-teal-50/10" : "border-slate-200 bg-white/60 hover:border-slate-300"}`}>
                  <input type="checkbox" checked={on} onChange={() => toggleSection(s.name)} className="mt-0.5 h-4 w-4 accent-teal-600" />
                  <div>
                    <span className="text-xs font-bold block">{s.name}</span>
                    <span className="text-[0.65rem] text-slate-400 font-medium">{s.description}</span>
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      </div>

      {/* Reports list */}
      <p className="eyebrow mb-3 text-ledger-950/50">Generated Reports</p>
      <div className="card divide-y divide-slate-100 border border-slate-200 shadow-sm bg-white/80">
        {reports.length === 0 && <p className="px-5 py-10 text-center text-xs font-semibold text-slate-400">No reports yet.</p>}
        {reports.map((r) => (
          <div key={r.id} className="flex items-center justify-between px-5 py-4 hover:bg-slate-50/50 transition-all">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-50 text-red-500 border border-red-100">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </div>
              <div>
                <p className="text-sm font-bold text-ledger-950">{r.title || "Research Brief"}</p>
                <p className="text-xs text-slate-400 font-semibold mt-0.5">
                  {r.createdAt ? new Date(r.createdAt).toLocaleDateString(undefined, {month:"short",day:"numeric",year:"numeric"}) : ""}
                  {r.pages ? ` · ${r.pages} sections` : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-1 rounded-lg font-mono text-[0.65rem] font-bold uppercase ${r.status === "ready" ? "bg-green-50 text-green-700 border border-green-200/50" : "bg-amber-50 text-amber-600 border border-amber-200/50 animate-pulse"}`}>{r.status}</span>
              {isReal(r) && r.status === "ready" && (
                <a href={getDownloadUrl(r.id)} target="_blank" rel="noreferrer"
                  className="btn-ghost px-4 py-2 text-xs font-semibold bg-white border-slate-200 flex items-center gap-1.5">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  Download PDF
                </a>
              )}
              <button disabled={r.status !== "ready"} onClick={() => setActiveReport(r)}
                className="btn-ghost px-4 py-2 text-xs font-semibold bg-white border-slate-200 disabled:opacity-40">
                View
              </button>
            </div>
          </div>
        ))}
      </div>

      {activeReport && <ReportViewer report={activeReport} onClose={() => setActiveReport(null)} />}
    </div>
  );
}

function ReportViewer({ report, onClose }) {
  const includeDocs = report.documentIds || [];
  const [companies, setCompanies]     = useState([]);
  const [metricsById, setMetricsById] = useState({});
  const [flagsById, setFlagsById]     = useState({});
  const [loading, setLoading]         = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all(includeDocs.map(async (id) => {
      const [co, m, f] = await Promise.all([
        getDocument(id).catch(() => null),
        getDocumentMetrics(id).catch(() => ({ highlights: [] })),
        getDocumentRedFlags(id).catch(() => []),
      ]);
      return { id, co, m, f };
    })).then((res) => {
      if (cancelled) return;
      setCompanies(res.map((r) => r.co).filter(Boolean));
      setMetricsById(Object.fromEntries(res.map((r) => [r.id, r.m])));
      setFlagsById(Object.fromEntries(res.map((r) => [r.id, r.f || []])));
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [report.id]); // eslint-disable-line

  const val = (id, label) => (metricsById[id]?.highlights || []).find((h) => h.label === label)?.value || "—";
  const allFlags = companies.flatMap((c) => (flagsById[c.id] || []).map((f) => ({ ...f, company: c.company })));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="flex flex-col w-full max-w-3xl h-[92vh] bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 shrink-0 bg-white">
          <div>
            <p className="font-mono text-[0.6rem] text-violet-600 font-bold uppercase tracking-widest">Research Brief</p>
            <h3 className="text-sm font-bold text-ledger-950 truncate max-w-sm">{report.title}</h3>
          </div>
          <div className="flex items-center gap-2">
            {isReal(report) && (
              <a href={getDownloadUrl(report.id)} target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1.5 bg-violet-600 hover:bg-violet-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Download PDF
              </a>
            )}
            <button onClick={onClose} className="h-8 w-8 flex items-center justify-center rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 font-bold text-sm">✕</button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto bg-slate-50 px-4 py-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-400">
              <span className="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
              <span className="text-xs font-semibold">Loading report data…</span>
            </div>
          ) : (
            <div className="max-w-[680px] mx-auto bg-white border border-slate-200 shadow-sm rounded-xl px-8 py-10 space-y-8">

              {/* Cover */}
              <div className="pb-6 border-b border-slate-100">
                <span className="inline-flex items-center gap-2 mb-3">
                  <span className="h-2 w-2 rounded-full bg-violet-600" />
                  <span className="font-mono text-[0.6rem] font-bold text-violet-600 uppercase tracking-widest">Multi-Agent Financial Research System</span>
                </span>
                <h1 className="font-display text-2xl font-extrabold text-ledger-950 leading-tight mb-2">{report.title}</h1>
                <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                  This research brief was compiled by the Multi-Agent Financial Research System. All figures and
                  findings are grounded strictly in the uploaded source filings — no external data or synthetic
                  projections have been introduced.
                </p>
                <div className="mt-4 grid grid-cols-2 gap-3 text-[11px]">
                  <div><span className="font-mono text-[9px] text-slate-400 uppercase font-bold block mb-0.5">Date</span>{report.createdAt ? new Date(report.createdAt).toLocaleDateString(undefined,{month:"long",day:"numeric",year:"numeric"}) : "—"}</div>
                  <div><span className="font-mono text-[9px] text-slate-400 uppercase font-bold block mb-0.5">Entities</span>{companies.map((c)=>c.company).join(", ")||"—"}</div>
                  <div><span className="font-mono text-[9px] text-slate-400 uppercase font-bold block mb-0.5">Sections</span>{(report.sections||[]).join(", ")||"All sections"}</div>
                  <div><span className="font-mono text-[9px] text-slate-400 uppercase font-bold block mb-0.5">Agents</span>Document · Extraction · Red Flag · Comparison · Report</div>
                </div>
              </div>

              {/* Executive Summary */}
              <Section title="1. Executive Summary" color="#7C3AED">
                <P>This research brief has been compiled by the Multi-Agent Financial Research System pipeline.
                  A Document Agent parsed and indexed each filing into a FAISS vector store; an Extraction Agent
                  retrieved key financial metrics using a Groq LLM pipeline; a Red Flag Agent scanned disclosures
                  for anomalies; a Comparison Agent benchmarked performance across entities; and this Report Agent
                  synthesised all outputs. Every figure and finding is grounded in the source filings — no external
                  data or projections have been incorporated.</P>
                {companies.map((c) => (
                  <div key={c.id} className="mt-3 pl-4 border-l-2 border-violet-300">
                    <p className="text-xs font-bold text-ledger-950">{c.company}</p>
                    <p className="text-[11px] text-slate-500 leading-relaxed mt-1">
                      {c.sector && c.sector !== "—" ? `Sector: ${c.sector}. ` : ""}
                      Revenue: {val(c.id,"Revenue")}. Net Profit: {val(c.id,"Net profit")}. EBITDA: {val(c.id,"EBITDA")}.
                      Red flags identified: {(flagsById[c.id]||[]).length}.
                    </p>
                  </div>
                ))}
              </Section>

              {/* Key Financials */}
              <Section title="2. Key Financials" color="#0D9488">
                <P>The Extraction Agent retrieved the following headline financial figures directly from each
                  filing's income statement and balance sheet. All values are expressed in the currency and unit
                  reported in the source document. Where a metric could not be located, the field is shown as a dash.</P>
                <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full text-[11px] border-collapse">
                    <thead>
                      <tr className="bg-slate-800 text-white">
                        <th className="px-4 py-2.5 text-left font-bold">Metric</th>
                        {companies.map((c) => <th key={c.id} className="px-4 py-2.5 text-right font-bold">{c.company.split(" ")[0]}</th>)}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {["Revenue","Net profit","EBITDA","EPS","Assets","Liabilities","Debt/Equity"].map((label) => (
                        <tr key={label} className="odd:bg-white even:bg-slate-50">
                          <td className="px-4 py-2 font-bold text-slate-700">{label}</td>
                          {companies.map((c) => <td key={c.id} className="px-4 py-2 text-right font-mono text-slate-600">{val(c.id,label)}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {companies.map((c) => {
                  const rev=val(c.id,"Revenue"), ni=val(c.id,"Net profit"), eb=val(c.id,"EBITDA"), ta=val(c.id,"Assets"), d2e=val(c.id,"Debt/Equity");
                  if (rev==="—") return null;
                  return (
                    <div key={c.id} className="mt-4">
                      <p className="text-[11px] font-bold text-ledger-950 mb-1">{c.company} — Financial Commentary</p>
                      <P>{c.company} reported revenue of {rev} with net income of {ni}.{eb!=="—"?` EBITDA stands at ${eb}, reflecting operating cash generation before financing costs.`:""}
                        {ta!=="—"?` Total assets are recorded at ${ta}.`:""}
                        {d2e!=="—"?` The debt-to-equity ratio is ${d2e}, indicating the company's financial leverage position.`:""}</P>
                    </div>
                  );
                })}
              </Section>

              {/* Red Flags */}
              <Section title="3. Red Flags &amp; Risks" color="#E11D48">
                <P>The Red Flag Agent conducted an automated scan of each filing's financial disclosures and
                  balance sheet ratios across eight risk categories — leverage, margin compression, going concern
                  qualifications, material weakness disclosures, litigation exposure, working capital deterioration,
                  dividend sustainability, and client concentration.</P>
                {allFlags.length === 0 ? (
                  <div className="mt-3 p-4 rounded-xl bg-green-50 border border-green-200">
                    <p className="text-xs font-semibold text-green-700">No material risk indicators were surfaced across the selected documents.</p>
                  </div>
                ) : (
                  <div className="mt-3 space-y-3">
                    {allFlags.map((f, i) => (
                      <div key={i} className={`p-4 rounded-xl border-l-4 ${f.severity==="high"?"border-l-red-500 bg-red-50/40":f.severity==="medium"?"border-l-amber-500 bg-amber-50/40":"border-l-green-500 bg-green-50/40"}`}>
                        <div className="flex items-center gap-2 mb-1.5">
                          <RiskBadge severity={f.severity} />
                          <span className="text-xs font-bold text-ledger-950">{f.title}</span>
                          <span className="text-[10px] text-slate-400">· {f.company?.split(" ")[0]}</span>
                        </div>
                        <P>{f.detail} This finding was detected programmatically from the extracted financial data and should be cross-referenced with the original filing for full context.</P>
                      </div>
                    ))}
                  </div>
                )}
              </Section>

              {/* Comparison */}
              {companies.length >= 2 && (
                <Section title="4. Company Comparison" color="#D97706">
                  <P>The Comparison Agent benchmarked the included entities side-by-side. All values are derived
                    directly from the extraction pipeline — no external market data was consulted.</P>
                  <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
                    <table className="w-full text-[11px] border-collapse">
                      <thead>
                        <tr className="bg-slate-800 text-white">
                          <th className="px-4 py-2.5 text-left font-bold">Company</th>
                          <th className="px-4 py-2.5 text-right font-bold">Revenue</th>
                          <th className="px-4 py-2.5 text-right font-bold">Net Profit</th>
                          <th className="px-4 py-2.5 text-right font-bold">EBITDA</th>
                          <th className="px-4 py-2.5 text-right font-bold">Flags</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {companies.map((c) => (
                          <tr key={c.id} className="odd:bg-white even:bg-slate-50">
                            <td className="px-4 py-2 font-bold text-slate-700 max-w-[140px] truncate">{c.company}</td>
                            <td className="px-4 py-2 text-right font-mono text-slate-600">{val(c.id,"Revenue")}</td>
                            <td className="px-4 py-2 text-right font-mono text-slate-600">{val(c.id,"Net profit")}</td>
                            <td className="px-4 py-2 text-right font-mono text-slate-600">{val(c.id,"EBITDA")}</td>
                            <td className="px-4 py-2 text-right font-mono text-slate-600">{(flagsById[c.id]||[]).length}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Section>
              )}

              {/* Outlook */}
              <Section title="5. Outlook" color="#6366F1">
                <P>The following forward-looking assessment is synthesised exclusively from the metrics and
                  red flag findings extracted above. No external market data, analyst forecasts, or generative
                  projections have been introduced.</P>
                {companies.map((c) => {
                  const flags = flagsById[c.id]||[];
                  const high = flags.filter((f)=>f.severity==="high");
                  const med  = flags.filter((f)=>f.severity==="medium");
                  const rev  = val(c.id,"Revenue");
                  return (
                    <div key={c.id} className="mt-3">
                      <p className="text-[11px] font-bold text-ledger-950 mb-1">{c.company}</p>
                      <P>{high.length>0
                        ?`Primary watch items for ${c.company}: ${high.map(f=>f.title).join("; ")}. These high-severity findings require proactive management response.`
                        :med.length>0
                        ?`${c.company} shows medium-severity indicators including ${med[0].title}. These merit monitoring over the coming periods.`
                        :`No material risk flags were raised for ${c.company}. This is a positive indicator of financial stability.`
                      }{rev!=="—"?` Revenue of ${rev} provides the baseline for assessing future performance trajectory.`:""}</P>
                    </div>
                  );
                })}
                <div className="mt-6 p-4 rounded-xl bg-amber-50 border border-amber-200">
                  <p className="text-[9px] font-mono text-amber-700 font-bold uppercase tracking-wider mb-1.5">Citation Grounding Disclaimer</p>
                  <P>All statements, figures, and assessments in this report are derived exclusively from data
                    extracted by the Document Agent, Extraction Agent, and Red Flag Agent from the source filings.
                    No generative projections or external market data have been incorporated. This report is intended
                    for research and educational purposes and does not constitute investment advice.</P>
                </div>
              </Section>

              {/* Footer */}
              <div className="border-t border-slate-200 pt-4 flex justify-between text-[9px] font-mono text-slate-400 uppercase font-bold">
                <span>Confidential — Research Use Only</span>
                <span>Multi-Agent Financial Research System</span>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, color, children }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <span className="h-3 w-1 rounded-full shrink-0" style={{ background: color }} />
        <h2 className="text-sm font-bold text-ledger-950" dangerouslySetInnerHTML={{ __html: title }} />
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function P({ children }) {
  return <p className="text-[11px] leading-relaxed text-slate-600 font-medium">{children}</p>;
}
