import { useEffect, useRef, useState } from "react";
import { useSession } from "../context/SessionContext.jsx";
import { listDocuments } from "../api/documents.js";
import { listReports, generateReport, getReport, reportDownloadUrl } from "../api/reports.js";
import PageHeader from "../components/PageHeader.jsx";

export default function Reports() {
  const { activeSessionId } = useSession();
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [reports, setReports] = useState([]);
  const [generating, setGenerating] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => {
    if (!activeSessionId) return;
    listDocuments(activeSessionId).then((docs) => {
      const active = docs.filter((d) => d.status === "ready");
      setDocuments(active);
      if (active.length > 0) setSelectedDocs([active[0].id]);
    });
    listReports(activeSessionId).then(setReports);
    return () => clearInterval(pollRef.current);
  }, [activeSessionId]);

  function toggleDoc(id) {
    setSelectedDocs((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  // The Report Agent runs as a background task on the backend (reportlab
  // generation isn't instant), so we poll GET /reports/:id until it flips
  // away from "generating" -- same pattern as document processing.
  function pollReport(reportId) {
    const interval = setInterval(async () => {
      const updated = await getReport(reportId);
      setReports((prev) => prev.map((r) => (r.id === reportId ? updated : r)));
      if (updated.status === "ready" || updated.status === "failed") {
        clearInterval(interval);
      }
    }, 2000);
    pollRef.current = interval;
  }

  async function handleGenerate() {
    if (selectedDocs.length === 0 || !activeSessionId) return;
    setGenerating(true);
    try {
      const report = await generateReport(activeSessionId, selectedDocs);
      setReports((prev) => [report, ...prev]);
      if (report.status === "generating") pollReport(report.id);
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
        description="Trigger the Report Agent to compile the Extraction and Red Flag agents' output for the selected filings into a downloadable PDF."
      />

      <div className="grid grid-cols-1 gap-6 mb-8 max-w-2xl">
        <div className="card p-5 md:p-6 bg-white/60 flex flex-col justify-between">
          <div>
            <p className="eyebrow mb-3.5 flex items-center gap-1.5 text-violet-600">
              <span className="h-1.5 w-1.5 rounded-full bg-violet-600 animate-pulse" />
              Choose documents to include
            </p>
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {documents.map((doc) => (
                <label
                  key={doc.id}
                  className={`flex cursor-pointer items-center justify-between rounded-xl px-4 py-3 border transition-all duration-150 ${
                    selectedDocs.includes(doc.id)
                      ? "border-violet-300 bg-violet-50/20"
                      : "border-slate-200 bg-white/60 hover:bg-slate-50/50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={selectedDocs.includes(doc.id)}
                      onChange={() => toggleDoc(doc.id)}
                      className="h-4 w-4 rounded border-slate-300 text-violet-600 focus:ring-violet-500/20 cursor-pointer accent-violet-600"
                    />
                    <span className="text-xs font-bold text-ledger-950">{doc.company}</span>
                  </div>
                  <span className="font-mono text-[0.625rem] font-bold text-slate-400 bg-slate-100/60 px-2 py-0.5 rounded">
                    {doc.fiscalYear || "—"}
                  </span>
                </label>
              ))}
              {documents.length === 0 && (
                <p className="text-xs font-semibold text-slate-400 text-center py-6">
                  No indexed filings available in workspace.
                </p>
              )}
            </div>
          </div>

          <div className="mt-5 border-t border-slate-100 pt-4">
            <button
              onClick={handleGenerate}
              disabled={selectedDocs.length === 0 || generating}
              className="btn-primary w-full py-3.5 text-sm font-semibold rounded-xl"
            >
              {generating ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Requesting report...
                </span>
              ) : (
                "Generate Report"
              )}
            </button>
          </div>
        </div>
      </div>

      {/* History List */}
      <p className="eyebrow mb-3.5 flex items-center gap-1.5 text-ledger-950/50">
        Generated Analyst Briefs
      </p>
      <div className="card divide-y divide-slate-100 overflow-hidden border border-slate-200 shadow-sm bg-white/80">
        {reports.length === 0 && (
          <p className="px-5 py-10 text-center text-xs font-semibold text-slate-400">
            No research reports compiled in this session yet. Select filings above and generate one.
          </p>
        )}
        {reports.map((r) => (
          <div
            key={r.id}
            className="flex items-center justify-between px-5 py-4 transition-all duration-155 hover:bg-slate-50/50"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-500 border border-red-100">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-bold text-ledger-950">{r.title || "Untitled Report"}</p>
                <p className="mt-0.5 text-xs text-ledger-950/40 font-semibold">
                  {r.createdAt
                    ? new Date(r.createdAt).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })
                    : ""}
                  {r.error ? ` · ${r.error}` : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center rounded-lg px-2.5 py-1 font-mono text-[0.65rem] font-bold uppercase tracking-wider ${
                  r.status === "ready"
                    ? "bg-green-50 text-green-700 border border-green-200/50"
                    : r.status === "failed"
                    ? "bg-rose-50 text-rose-700 border border-rose-200/50"
                    : "bg-amber-50 text-amber-600 border border-amber-200/50 animate-pulse"
                }`}
              >
                {r.status}
              </span>
              <a
                href={r.status === "ready" ? reportDownloadUrl(r.downloadUrl) : undefined}
                target="_blank"
                rel="noreferrer"
                className={`btn-ghost px-4 py-2 text-xs font-semibold shadow-sm bg-white hover:bg-slate-50 border-slate-200 ${
                  r.status !== "ready" ? "pointer-events-none opacity-40" : ""
                }`}
              >
                Download PDF
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
