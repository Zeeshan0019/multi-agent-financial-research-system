import { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { getMe, logIn as apiLogIn, signUp as apiSignUp } from "../api/auth.js";

const AuthContext  = createContext(null);
const TOKEN_KEY    = "ledger_token";

export function AuthProvider({ children }) {
  const [user,  setUser]  = useState(null);
  const [ready, setReady] = useState(false);
  const booted = useRef(false);

  // Run once on mount — verify any stored token, then show the app
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;

    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      // No token — go straight to login
      setReady(true);
      return;
    }

    getMe()
      .then((profile) => setUser(profile))
      .catch(() => {
        // Token invalid / expired / backend down — clear it, show login
        localStorage.removeItem(TOKEN_KEY);
      })
      .finally(() => setReady(true)); // ALWAYS unblock the app
  }, []);

  const logIn = useCallback(async (username, password) => {
    const data    = await apiLogIn(username, password);
    localStorage.setItem(TOKEN_KEY, data.token);
    const profile = await getMe();
    setUser(profile);
    return profile;
  }, []);

  const signUp = useCallback(async (username, password) => {
    const data    = await apiSignUp(username, password);
    localStorage.setItem(TOKEN_KEY, data.token);
    const profile = await getMe();
    setUser(profile);
    return profile;
  }, []);

  const logOut = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading:         !ready,
        isAuthenticated: !!user,
        logIn,
        signUp,
        logOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
