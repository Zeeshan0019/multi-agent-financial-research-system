import React, { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { listDocuments } from "../api/documents.js";
import { compareCompanies } from "../api/comparison.js";

const METRIC_ROWS = [
  { key: "revenue", label: "Revenue" },
  { key: "net_profit", label: "Net profit" },
  { key: "debt", label: "Debt" },
  { key: "margin", label: "Margin" },
];

export default function Comparison() {
  const { activeSessionId, activeSessionName } = useSession();
  const [documents, setDocuments] = useState([]);
  const [selected, setSelected] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (activeSessionId) {
      listDocuments(activeSessionId).then(setDocuments).catch((err) => setError(err.message));
    }
  }, [activeSessionId]);

  function toggle(id) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  async function runComparison() {
    if (selected.length < 2) {
      setError("Select at least two documents to compare.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const data = await compareCompanies(activeSessionId, selected);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (!activeSessionId) {
    return (
      <div>
        <PageHeader eyebrow="Comparison" title="Compare companies" />
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
        eyebrow="Comparison"
        title="Compare companies"
        description={`Session: ${activeSessionName}. Pick two or more uploaded reports to benchmark revenue, profit, debt, and margin.`}
        actions={
          <button className="btn-primary" onClick={runComparison} disabled={loading}>
            {loading ? "Comparing…" : "Run comparison"}
          </button>
        }
      />

      <div className="px-8 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <p className="label mb-2">Select documents</p>
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
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">
                        {doc.company_name || doc.file_name}
                      </p>
                      <p className="text-xs text-ledger-950/50 truncate">{doc.file_name}</p>
                    </div>
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
          {!result ? (
            <div className="card p-8 text-center text-sm text-ledger-950/50">
              Results will appear here after you run a comparison.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="card overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-ledger-950 text-parchment-50">
                      <th className="text-left px-4 py-3 font-medium">Metric</th>
                      {result.companies.map((c) => (
                        <th key={c.document_id} className="text-left px-4 py-3 font-medium">
                          {c.company_name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {METRIC_ROWS.map((row, i) => (
                      <tr key={row.key} className={i % 2 ? "bg-parchment-100" : "bg-white"}>
                        <td className="px-4 py-2.5 text-ledger-950/60 font-medium">
                          {row.label}
                        </td>
                        {result.companies.map((c) => (
                          <td key={c.document_id} className="px-4 py-2.5 font-mono">
                            {c[row.key] ?? "—"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {result.summary && (
                <div className="card p-4">
                  <p className="label mb-1">Analyst summary</p>
                  <p className="text-sm text-ledger-950 whitespace-pre-wrap">{result.summary}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
