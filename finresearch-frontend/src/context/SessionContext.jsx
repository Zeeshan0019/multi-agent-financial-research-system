import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { listSessions, createSession } from "../api/sessions.js";

const SessionContext = createContext(null);

const LAST_SESSION_KEY = "ledger_last_session_id";

export function SessionProvider({ children }) {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(
    () => localStorage.getItem(LAST_SESSION_KEY) || null
  );
  const [loading, setLoading] = useState(true);

  const refreshSessions = useCallback(async () => {
    setLoading(true);
    const data = await listSessions();
    setSessions(data);
    setLoading(false);
    return data;
  }, []);

  useEffect(() => {
    refreshSessions().then((data) => {
      if (!activeSessionId && data.length > 0) {
        setActiveSessionId(data[0].id);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeSessionId) localStorage.setItem(LAST_SESSION_KEY, activeSessionId);
  }, [activeSessionId]);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;

  const addSession = useCallback(async (name) => {
    const created = await createSession(name);
    setSessions((prev) => [created, ...prev]);
    setActiveSessionId(created.id);
    return created;
  }, []);

  return (
    <SessionContext.Provider
      value={{
        sessions,
        loading,
        activeSessionId,
        activeSession,
        setActiveSessionId,
        refreshSessions,
        addSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
