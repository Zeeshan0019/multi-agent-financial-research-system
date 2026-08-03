import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const client = axios.create({
  baseURL,
  timeout: 15000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("ledger_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// The backend isn't always live (local dev before the FastAPI teammate has
// started their server, or this preview environment). Every function in
// src/api/*.js wraps its real axios call in this helper: try the network
// call, and if it fails for any reason, fall back to seed data so the UI
// still demonstrates the full agent pipeline end to end.
export async function withFallback(request, fallback) {
  try {
    // Every caller in src/api/*.js already does its own
    // `.then((r) => transform(r.data))` before this ever runs — so
    // `request()` resolves to the FINAL, already-unwrapped value, not a raw
    // axios response. Reaching for `.data` again here was grabbing a
    // property that doesn't exist on that final value, which meant a
    // successful real API call could still silently end up returning
    // `undefined` or (depending on timing) tripping the catch block below
    // and swapping in mock seed data even though the backend call worked.
    return await request();
  } catch (err) {
    console.warn("[ledger] backend call failed, using seed data:", err?.message);
    return typeof fallback === "function" ? fallback() : fallback;
  }
}

export const USING_MOCK_FLAG = "ledger_used_fallback";
