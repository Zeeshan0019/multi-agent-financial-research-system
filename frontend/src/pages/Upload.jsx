import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadDocument } from "../api/documents.js";
import { useDocuments } from "../context/DocumentsContext.jsx";
import PageHeader from "../components/PageHeader.jsx";

const PIPELINE_STAGES = [
  { key: "parsing",    label: "Document Agent — parsing & chunking",        color: "#8B5CF6" },
  { key: "embedding",  label: "Document Agent — embedding & indexing",       color: "#5A4BB0" },
  { key: "extraction", label: "Extraction Agent — pulling metrics & ratios", color: "#14B8A6" },
  { key: "redflag",    label: "Red Flag Agent — scanning for anomalies",     color: "#FB7185" },
];

export default function Upload() {
  const navigate = useNavigate();
  const { addDocument } = useDocuments();
  const inputRef = useRef(null);

  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [stageIndex, setStageIndex] = useState(-1);
  const [status, setStatus] = useState("idle"); // idle | uploading | processing | done | error
  const [error, setError] = useState(null);
  const [uploadedDoc, setUploadedDoc] = useState(null);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) handleFile(dropped);
  }, []);

  function handleFile(f) {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    setError(null);
    setFile(f);
    startPipeline(f);
  }

  async function startPipeline(f) {
    setStatus("uploading");
    setProgress(0);
    setStageIndex(-1);
    setUploadedDoc(null);

    try {
      // 1. Upload — server returns doc info immediately, pipeline runs in background
      const doc = await uploadDocument(f, (pct) => setProgress(pct));

      // 2. Push to global context RIGHT NOW so dashboard shows it instantly
      if (doc && doc.id) {
        addDocument(doc);
        setUploadedDoc(doc);
      }

      // 3. Animate pipeline stages (visual only)
      setStatus("processing");
      for (let i = 0; i < PIPELINE_STAGES.length; i++) {
        setStageIndex(i);
        // eslint-disable-next-line no-await-in-loop
        await new Promise((res) => setTimeout(res, 900));
      }
      setStatus("done");
    } catch (err) {
      const msg = err?.response?.data?.detail || "Upload failed. Please check your connection and try again.";
      setError(msg);
      setStatus("error");
    }
  }

  function reset() {
    setFile(null);
    setStatus("idle");
    setProgress(0);
    setStageIndex(-1);
    setError(null);
    setUploadedDoc(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  const displayName = uploadedDoc?.company
    || (file ? file.name.replace(/\.pdf$/i, "").replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : "");

  return (
    <div className="animate-fade-up">
      <PageHeader
        eyebrow="Document Agent"
        title="Upload a filing"
        description="Drop in a PDF annual report, 10-K, or earnings filing. The Document Agent parses, chunks, and indexes it — then Extraction and Red Flag agents run automatically."
      />

      {/* Drop zone */}
      {status === "idle" && (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 md:p-16 text-center cursor-pointer transition-all duration-300 ${
            dragging
              ? "border-violet-500 bg-violet-50/50 shadow-lg scale-[0.99]"
              : "border-slate-300 hover:border-violet-400 bg-white/60 hover:bg-violet-50/10"
          }`}
        >
          <input ref={inputRef} type="file" accept=".pdf" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
          <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-50 text-violet-600 shadow-inner">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 16V4"/><path d="M6 10l6-6 6 6"/><path d="M4 20h16"/>
            </svg>
          </div>
          <h3 className="text-base font-bold text-ledger-950">Drop a PDF filing here</h3>
          <p className="mt-1 text-xs font-semibold text-slate-400">PDF only — annual reports, 10-K, earnings filings</p>
          <button type="button" className="btn-ghost mt-5 text-xs py-2 px-4 shadow-sm bg-white border-slate-200">
            Browse files
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-100 text-sm text-rose-700 font-semibold animate-scale-in flex items-start gap-3">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="shrink-0 mt-0.5">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <div>
            <p>{error}</p>
            {status === "error" && <button onClick={reset} className="mt-2 text-rose-600 underline text-xs">Try again</button>}
          </div>
        </div>
      )}

      {/* Progress card */}
      {status !== "idle" && status !== "error" && file && (
        <div className="card animate-scale-in p-6 md:p-8 border border-slate-200/80 shadow-md max-w-2xl mx-auto">

          {/* File header */}
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <div>
                <p className="font-bold text-ledger-950 text-base">{displayName}</p>
                <p className="text-xs text-ledger-950/40 font-semibold">{file.name} · {(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            {status === "done" && (
              <span className="inline-flex items-center rounded-lg bg-green-50 px-2.5 py-1 font-mono text-[0.65rem] font-bold uppercase tracking-wider text-green-700 border border-green-200/60">
                Queued
              </span>
            )}
          </div>

          {/* Upload bar */}
          {status === "uploading" && (
            <div className="py-2">
              <div className="mb-2 flex justify-between text-xs font-bold text-ledger-950/50">
                <span>Uploading…</span><span>{progress}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-violet-500 transition-all duration-200" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}

          {/* Pipeline stages */}
          {(status === "processing" || status === "done") && (
            <div className="space-y-4">
              <div className="mb-2 flex items-center justify-between text-xs font-bold text-ledger-950/50 border-b border-slate-100 pb-2">
                <span>Pipeline Stage</span><span>Status</span>
              </div>
              <ul className="space-y-3">
                {PIPELINE_STAGES.map((stage, i) => {
                  const isDone = status === "done" || i < stageIndex;
                  const isActive = status === "processing" && i === stageIndex;
                  return (
                    <li key={stage.key} className={`flex items-center justify-between rounded-xl px-4 py-3 border transition-all duration-300 ${
                      isDone ? "bg-slate-50/50 border-slate-200/80 text-ledger-950"
                        : isActive ? "bg-violet-50/30 border-violet-200/50 text-violet-800 font-semibold shadow-sm"
                        : "border-transparent text-slate-400"
                    }`}>
                      <div className="flex items-center gap-3">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border transition-all duration-300"
                          style={isDone
                            ? { borderColor: stage.color, background: `${stage.color}15`, color: stage.color }
                            : isActive
                            ? { borderColor: stage.color, background: `${stage.color}10`, color: stage.color }
                            : { borderColor: "rgba(148,163,184,0.3)", color: "rgba(148,163,184,0.5)" }}>
                          {isDone
                            ? <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M20 6L9 17l-5-5"/></svg>
                            : isActive
                            ? <span className="h-2 w-2 rounded-full animate-ping" style={{ background: stage.color }} />
                            : <span className="text-[0.625rem] font-mono font-bold">{i + 1}</span>}
                        </span>
                        <span className="text-sm font-semibold">{stage.label}</span>
                      </div>
                      <div>
                        {isDone && <span className="text-xs font-mono font-bold text-green-600">Complete</span>}
                        {isActive && <span className="text-xs font-mono font-bold text-violet-600 flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-violet-600 animate-ping"/>Running</span>}
                        {!isDone && !isActive && <span className="text-xs font-mono font-medium text-slate-300">Pending</span>}
                      </div>
                    </li>
                  );
                })}
              </ul>
              {status === "processing" && (
                <p className="text-xs text-center text-slate-400 font-semibold pt-2">
                  Processing in background — you can go to the Dashboard now.
                </p>
              )}
            </div>
          )}

          {/* Done actions */}
          {status === "done" && (
            <div className="mt-8 flex gap-3 border-t border-slate-100 pt-6 animate-scale-in">
              <button onClick={() => navigate("/")} className="btn-primary flex-1 py-3 text-sm">
                View in Dashboard
              </button>
              <button onClick={reset} className="btn-ghost flex-1 py-3 text-sm">
                Upload another
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
