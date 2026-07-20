import React, { createContext, useContext, useState, useEffect } from "react";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [activeSessionId, setActiveSessionId] = useState(
    () => localStorage.getItem("ledger_active_session") || null
  );
  const [activeSessionName, setActiveSessionName] = useState(
    () => localStorage.getItem("ledger_active_session_name") || null
  );

  useEffect(() => {
    if (activeSessionId) {
      localStorage.setItem("ledger_active_session", activeSessionId);
    } else {
      localStorage.removeItem("ledger_active_session");
    }
  }, [activeSessionId]);

  useEffect(() => {
    if (activeSessionName) {
      localStorage.setItem("ledger_active_session_name", activeSessionName);
    }
  }, [activeSessionName]);

  const selectSession = (id, name) => {
    setActiveSessionId(id);
    setActiveSessionName(name);
  };

  const clearSession = () => {
    setActiveSessionId(null);
    setActiveSessionName(null);
  };

  return (
    <SessionContext.Provider
      value={{ activeSessionId, activeSessionName, selectSession, clearSession }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used inside SessionProvider");
  return ctx;
}
