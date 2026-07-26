import React, { useCallback, useEffect, useRef, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import MetricCard from "../components/MetricCard.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { uploadDocument, listDocuments, getDocument } from "../api/documents.js";

const POLL_INTERVAL_MS = 3000;

export default function Upload() {
  const { activeSessionId, activeSessionName } = useSession();
  const [documents, setDocuments] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const fileInputRef = useRef(null);
  const pollRef = useRef(null);

  useEffect(() => {
    if (activeSessionId) refresh();
    return () => clearInterval(pollRef.current);
  }, [activeSessionId]);

  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === "processing");
    clearInterval(pollRef.current);
    if (hasProcessing) {
      pollRef.current = setInterval(refresh, POLL_INTERVAL_MS);
    }
    return () => clearInterval(pollRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents]);

  async function refresh() {
    try {
      const data = await listDocuments(activeSessionId);
      setDocuments(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleFiles(files) {
    if (!activeSessionId) {
      setError("Create or select a session first, from the Dashboard.");
      return;
    }
    const file = files[0];
    if (!file) return;
    if (file.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      return;
    }
    setError("");
    setUploading(true);
    setProgress(0);
    try {
      await uploadDocument(activeSessionId, file, (evt) => {
        if (evt.total) setProgress(Math.round((evt.loaded / evt.total) * 100));
      });
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      setProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      handleFiles(e.dataTransfer.files);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [activeSessionId]
  );

  async function viewDocument(doc) {
    try {
      const full = await getDocument(doc.id);
      setSelectedDoc(full);
    } catch (err) {
      setError(err.message);
    }
  }

  if (!activeSessionId) {
    return (
      <div>
        <PageHeader eyebrow="Upload" title="Upload financial reports" />
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
        eyebrow="Upload"
        title="Upload financial reports"
        description={`Session: ${activeSessionName}. Each PDF runs through the Document Agent (parse → chunk → embed → index), then the Extraction and Red Flag agents.`}
      />

      <div className="px-8 py-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`card border-dashed cursor-pointer flex flex-col items-center justify-center text-center px-6 py-12 transition-colors ${
              dragOver ? "border-amber-500 bg-amber-500/5" : ""
            }`}
          >
            <span className="text-3xl text-amber-600 mb-2">↑</span>
            <p className="text-sm font-medium text-ledger-950">
              Drop a PDF here, or click to browse
            </p>
            <p className="text-xs text-ledger-950/50 mt-1">
              10-K filings, annual reports, earnings statements
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>

          {uploading && (
            <div className="mt-3">
              <div className="h-1.5 rounded-full bg-parchment-200 overflow-hidden">
                <div
                  className="h-full bg-amber-500 transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-ledger-950/50 mt-1">Uploading… {progress}%</p>
            </div>
          )}

          {error && (
            <p className="text-sm text-flag-high mt-3" role="alert">
              {error}
            </p>
          )}

          <div className="mt-6">
            <p className="label mb-2">Documents in this session</p>
            {documents.length === 0 ? (
              <p className="text-sm text-ledger-950/50">Nothing uploaded yet.</p>
            ) : (
              <ul className="space-y-2">
                {documents.map((doc) => (
                  <li key={doc.id}>
                    <button
                      onClick={() => viewDocument(doc)}
                      className="w-full text-left card p-3 flex items-center justify-between hover:border-amber-500/40"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{doc.file_name}</p>
                        <p className="text-xs text-ledger-950/50">
                          {doc.company_name || "Company unresolved"}
                        </p>
                      </div>
                      <StatusPill status={doc.status} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div>
          {!selectedDoc ? (
            <div className="card p-8 text-center text-sm text-ledger-950/50">
              Select a document to view its extracted metrics and red flags.
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="label">Extracted metrics</p>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  <MetricCard label="Revenue" value={selectedDoc.metrics?.revenue} />
                  <MetricCard label="Net profit" value={selectedDoc.metrics?.net_profit} />
                  <MetricCard label="EBITDA" value={selectedDoc.metrics?.ebitda} />
                  <MetricCard label="EPS" value={selectedDoc.metrics?.eps} />
                  <MetricCard label="Assets" value={selectedDoc.metrics?.assets} />
                  <MetricCard label="Liabilities" value={selectedDoc.metrics?.liabilities} />
                </div>
              </div>

              <div>
                <p className="label">Red flags</p>
                {!selectedDoc.red_flags || selectedDoc.red_flags.length === 0 ? (
                  <p className="text-sm text-ledger-950/50 mt-2">
                    None detected yet, or analysis still running.
                  </p>
                ) : (
                  <ul className="mt-2 space-y-2">
                    {selectedDoc.red_flags.map((flag) => (
                      <li key={flag.id} className="card p-3 flex items-start gap-3">
                        <RiskBadge severity={flag.severity} />
                        <div className="min-w-0">
                          <p className="text-sm text-ledger-950">{flag.description}</p>
                          {flag.source_page && (
                            <p className="text-xs text-ledger-950/50 mt-0.5">
                              Source: page {flag.source_page}
                            </p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusPill({ status }) {
  const styles = {
    processing: "bg-amber-500/15 text-amber-600",
    ready: "bg-flag-low/15 text-flag-low",
    failed: "bg-flag-high/15 text-flag-high",
  };
  return (
    <span
      className={`text-[11px] font-semibold uppercase tracking-wide rounded-full px-2.5 py-1 shrink-0 ml-3 ${
        styles[status] || "bg-parchment-200 text-ledger-950/50"
      }`}
    >
      {status || "unknown"}
    </span>
  );
}
