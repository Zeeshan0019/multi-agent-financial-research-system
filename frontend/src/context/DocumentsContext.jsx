import {
  createContext, useContext, useState,
  useCallback, useEffect, useRef, useMemo,
} from "react";
import { listDocuments } from "../api/documents.js";

const DocumentsContext = createContext(null);

export function DocumentsProvider({ children }) {
  const [documents, setDocuments]   = useState([]);
  const [loading, setLoading]       = useState(true);
  const pollRef                     = useRef(null);
  const mountedRef                  = useRef(true);
  const fetchedOnce                 = useRef(false);

  // Track mounted state for async safety
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    };
  }, []);

  // ── fetch ──────────────────────────────────────────────────────────────────
  const refresh = useCallback(async () => {
    if (!mountedRef.current) return [];
    try {
      const docs = await listDocuments();
      if (mountedRef.current) {
        setDocuments(docs);
        setLoading(false);
        fetchedOnce.current = true;
      }
      return docs;
    } catch {
      if (mountedRef.current) setLoading(false);
      return [];
    }
  }, []);

  // Initial load once on mount
  useEffect(() => {
    refresh();
  }, []); // eslint-disable-line

  // Re-fetch when window gains focus (user comes back from another tab)
  useEffect(() => {
    const fn = () => refresh();
    window.addEventListener("focus", fn);
    return () => window.removeEventListener("focus", fn);
  }, []); // eslint-disable-line

  // ── polling — 3s while any doc is processing ──────────────────────────────
  const hasProcessing = useMemo(
    () => documents.some((d) => d.status === "processing"),
    [documents]
  );

  useEffect(() => {
    if (!hasProcessing) {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      return;
    }
    if (pollRef.current) return;

    pollRef.current = setInterval(async () => {
      if (!mountedRef.current) return;
      const docs = await listDocuments().catch(() => null);
      if (!docs || !mountedRef.current) return;
      setDocuments(docs);
      if (!docs.some((d) => d.status === "processing")) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    }, 3000);

    return () => {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    };
  }, [hasProcessing]); // eslint-disable-line

  // ── mutations ──────────────────────────────────────────────────────────────

  // Called immediately after upload so the doc appears in all pages at once
  const addDocument = useCallback((doc) => {
    if (!doc?.id) return;
    setDocuments((prev) =>
      prev.some((d) => d.id === doc.id) ? prev : [doc, ...prev]
    );
  }, []);

  const updateDocument = useCallback((id, patch) => {
    setDocuments((prev) => prev.map((d) => (d.id === id ? { ...d, ...patch } : d)));
  }, []);

  const removeDocument = useCallback((id) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }, []);

  return (
    <DocumentsContext.Provider
      value={{ documents, loading, refresh, addDocument, updateDocument, removeDocument }}
    >
      {children}
    </DocumentsContext.Provider>
  );
}

export function useDocuments() {
  const ctx = useContext(DocumentsContext);
  if (!ctx) throw new Error("useDocuments must be used within DocumentsProvider");
  return ctx;
}
