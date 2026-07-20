import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader.jsx";
import { listSessions, createSession } from "../api/sessions.js";
import { useSession } from "../context/SessionContext.jsx";

export default function Dashboard() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const { selectSession } = useSession();
  const navigate = useNavigate();

  useEffect(() => {
    refresh();
  }, []);

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const data = await listSessions();
      setSessions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setError("");
    try {
      const session = await createSession(newName.trim());
      setNewName("");
      setSessions((prev) => [session, ...prev]);
      selectSession(session.id, session.name);
      navigate("/upload");
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  }

  function openSession(session) {
    selectSession(session.id, session.name);
    navigate("/upload");
  }

  return (
    <div>
      <PageHeader
        eyebrow="Dashboard"
        title="Research sessions"
        description="A session groups the reports you upload, the questions you ask, and the comparisons and PDFs you generate from them."
      />

      <div className="px-8 py-6 max-w-3xl">
        <form onSubmit={handleCreate} className="card p-4 flex items-end gap-3 mb-8">
          <div className="flex-1">
            <label className="label" htmlFor="session-name">
              New session name
            </label>
            <input
              id="session-name"
              className="input-field mt-1.5"
              placeholder="e.g. Q1 FY26 — Infosys vs TCS"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary" disabled={creating}>
            {creating ? "Creating…" : "Create session"}
          </button>
        </form>

        {error && (
          <p className="text-sm text-flag-high mb-4" role="alert">
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-sm text-ledger-950/50">Loading sessions…</p>
        ) : sessions.length === 0 ? (
          <div className="card p-8 text-center">
            <p className="text-ledger-950/60 text-sm">
              No sessions yet. Create one above to upload your first financial report.
            </p>
          </div>
        ) : (
          <ul className="space-y-2">
            {sessions.map((s) => (
              <li key={s.id}>
                <button
                  onClick={() => openSession(s)}
                  className="w-full text-left card p-4 hover:border-amber-500/40 transition-colors flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-ledger-950">{s.name}</p>
                    <p className="text-xs text-ledger-950/50 mt-0.5">
                      {s.document_count ?? 0} document{s.document_count === 1 ? "" : "s"}
                      {s.created_at ? ` · created ${new Date(s.created_at).toLocaleDateString()}` : ""}
                    </p>
                  </div>
                  <span className="text-amber-600 text-sm">Open →</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
