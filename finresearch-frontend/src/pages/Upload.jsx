import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSession } from "../context/SessionContext.jsx";
import { uploadDocument, getDocument } from "../api/documents.js";
import PageHeader from "../components/PageHeader.jsx";

export default function Upload() {
  const { activeSessionId } = useSession();
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const pollRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("idle"); // idle | uploading | processing | done | error
  const [doc, setDoc] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      const dropped = e.dataTransfer.files?.[0];
      if (dropped) handleFile(dropped);
    },
    [activeSessionId]
  );

  function handleFile(f) {
    // The orchestrator's /sessions/:id/documents endpoint only accepts PDFs.
    if (!/\.pdf$/i.test(f.name)) {
      setError("Only PDF files are supported by the Document Agent right now.");
      return;
    }
    setError(null);
    setFile(f);
    startPipeline(f);
  }

  async function startPipeline(f) {
    if (!activeSessionId) {
      setError("Create or select a research session in the sidebar first.");
      return;
    }
    setStatus("uploading");
    setProgress(0);
    setDoc(null);

    try {
      const uploaded = await uploadDocument(activeSessionId, f, (pct) => setProgress(pct));
      setStatus("processing");
      pollDocument(uploaded.id);
    } catch (err) {
      setError("Upload failed. Please check the backend connection.");
      setStatus("error");
    }
  }

  // Document Agent -> Extraction Agent -> Red Flag Agent run as a background
  // pipeline on the backend; the upload call returns immediately with
  // status "processing". We poll the real document record until it settles.
  function pollDocument(documentId) {
    const interval = setInterval(async () => {
      const updated = await getDocument(documentId);
      if (!updated) return;
      setDoc(updated);
      if (updated.status === "ready" || updated.status === "error") {
        clearInterval(interval);
        setStatus(updated.status === "ready" ? "done" : "error");
      }
    }, 2000);
    pollRef.current = interval;
  }

  function reset() {
    clearInterval(pollRef.current);
    setFile(null);
    setDoc(null);
    setStatus("idle");
    setProgress(0);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="animate-fade-up">
      <PageHeader
        eyebrow="Document Agent"
        title="Upload a filing"
        description="Drop in a PDF annual report or filing. The Document Agent parses, chunks, and indexes it, then the Extraction and Red Flag agents run automatically."
      />

      {status === "idle" && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 md:p-16 text-center cursor-pointer transition-all duration-300 ${
            dragging
              ? "border-violet-500 bg-violet-50/50 shadow-lg scale-[0.99] shadow-violet-100/30"
              : "border-slate-300 hover:border-violet-400 bg-white/60 hover:bg-violet-50/10 hover:shadow-[0_8px_30px_rgb(0,0,0,0.02)]"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-50 text-violet-600 shadow-inner">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M12 16V4" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M6 10l6-6 6 6" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M4 20h16" strokeLinecap="round" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-ledger-950">Drop a financial filing here</h3>
          <p className="mt-1 text-xs font-semibold text-slate-400">PDF only — up to 50MB</p>
          <button type="button" className="btn-ghost mt-5 text-xs py-2 px-4 shadow-sm bg-white border-slate-200">
            Browse files
          </button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-100 text-sm text-rose-700 font-semibold animate-scale-in">
          {error}
        </div>
      )}

      {status !== "idle" && file && (
        <div className="card animate-scale-in p-6 md:p-8 border border-slate-200/80 shadow-md max-w-2xl mx-auto">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <div>
                <p className="font-bold text-ledger-950 text-base">{file.name}</p>
                <p className="text-xs text-ledger-950/40 font-semibold">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            {status === "done" && (
              <span className="inline-flex items-center rounded-lg bg-green-50 px-2.5 py-1 font-mono text-[0.65rem] font-bold uppercase tracking-wider text-green-700 border border-green-200/60">
                Ready
              </span>
            )}
            {status === "error" && (
              <span className="inline-flex items-center rounded-lg bg-rose-50 px-2.5 py-1 font-mono text-[0.65rem] font-bold uppercase tracking-wider text-rose-700 border border-rose-200/60">
                Failed
              </span>
            )}
          </div>

          {status === "uploading" && (
            <div className="py-2">
              <div className="mb-2 flex justify-between text-xs font-bold text-ledger-950/50">
                <span>Uploading to Document Agent...</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div className="animate-shimmer h-full rounded-full transition-all duration-200" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}

          {status === "processing" && (
            <div className="flex items-center gap-2.5 text-sm text-ledger-950/60 py-3 font-semibold">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
              Document, Extraction, and Red Flag agents are processing this filing...
            </div>
          )}

          {(status === "done" || status === "error") && doc && (
            <div className="space-y-3">
              {doc.error && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-xs text-rose-700 font-semibold">
                  {doc.error}
                </div>
              )}
              {doc.warnings && doc.warnings.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-100 text-xs text-amber-700 font-semibold space-y-1">
                  <p className="uppercase font-mono text-[0.65rem] tracking-wider">Pipeline warnings</p>
                  {doc.warnings.map((w, i) => (
                    <p key={i}>{w}</p>
                  ))}
                </div>
              )}
              {status === "done" && !doc.warnings?.length && (
                <div className="p-3 rounded-xl bg-green-50 border border-green-100 text-xs text-green-700 font-semibold">
                  All agents completed without warnings.
                </div>
              )}
            </div>
          )}

          {(status === "done" || status === "error") && (
            <div className="mt-8 flex gap-3 border-t border-slate-100 pt-6 animate-scale-in">
              <button onClick={() => navigate("/")} className="btn-primary flex-1 py-3 text-sm">
                View in Coverage Dashboard
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
