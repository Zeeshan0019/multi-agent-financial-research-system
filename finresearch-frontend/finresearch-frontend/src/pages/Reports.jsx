import React, { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { listDocuments } from "../api/documents.js";
import { listReports, generateReport, getReport } from "../api/reports.js";

export default function Reports() {
  const { activeSessionId, activeSessionName } = useSession();
  const [documents, setDocuments] = useState([]);
  const [selected, setSelected] = useState([]);
  const [reports, setReports] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (activeSessionId) {
      listDocuments(activeSessionId).then(setDocuments).catch((err) => setError(err.message));
      listReports(activeSessionId).then(setReports).catch((err) => setError(err.message));
    }
  }, [activeSessionId]);

  function toggle(id) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  async function handleGenerate() {
    if (selected.length === 0) {
      setError("Select at least one document to include in the report.");
      return;
    }
    setError("");
    setGenerating(true);
    try {
      const job = await generateReport(activeSessionId, selected);
      await pollUntilReady(job.id);
      const updated = await listReports(activeSessionId);
      setReports(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  function pollUntilReady(reportId, attempt = 0) {
    return getReport(reportId).then((r) => {
      if (r.status === "ready" || attempt > 20) return r;
      return new Promise((resolve) => setTimeout(resolve, 3000)).then(() =>
        pollUntilReady(reportId, attempt + 1)
      );
    });
  }

  if (!activeSessionId) {
    return (
      <div>
        <PageHeader eyebrow="Reports" title="Analyst reports" />
        <div className="px-8 py-6">
          <div className="card p-8 text-center max-w-md">
            <p className="text-sm text-ledger-950/60">
              No active session. Go to the Dashboard to create or open one first.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow="Reports"
        title="Analyst reports"
        description={`Session: ${activeSessionName}. Generates a PDF with an executive summary, metrics, red flags, and comparison.`}
        actions={
          <button className="btn-primary" onClick={handleGenerate} disabled={generating}>
            {generating ? "Generating…" : "Generate report"}
          </button>
        }
      />

      <div className="px-8 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div>
          <p className="label mb-2">Include documents</p>
          {documents.length === 0 ? (
            <p className="text-sm text-ledger-950/50">Upload documents first.</p>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc) => (
                <li key={doc.id}>
                  <label className="card p-3 flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selected.includes(doc.id)}
                      onChange={() => toggle(doc.id)}
                      className="accent-amber-600"
                    />
                    <span className="text-sm truncate">
                      {doc.company_name || doc.file_name}
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          )}
          {error && (
            <p className="text-sm text-flag-high mt-3" role="alert">
              {error}
            </p>
          )}
        </div>

        <div className="lg:col-span-2">
          <p className="label mb-2">Report history</p>
          {reports.length === 0 ? (
            <div className="card p-8 text-center text-sm text-ledger-950/50">
              No reports generated yet.
            </div>
          ) : (
            <ul className="space-y-2">
              {reports.map((r) => (
                <li key={r.id} className="card p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{r.file_name}</p>
                    <p className="text-xs text-ledger-950/50">
                      {r.generated_at ? new Date(r.generated_at).toLocaleString() : ""}
                    </p>
                  </div>
                  {r.download_url ? (
                    <a href={r.download_url} className="btn-secondary" download>
                      Download
                    </a>
                  ) : (
                    <span className="text-xs text-amber-600">Generating…</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
