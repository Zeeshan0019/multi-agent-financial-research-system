import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

export const client = axios.create({
  baseURL,
  timeout: 120000, // 120s — covers embedding model load on first Research Agent call
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("ledger_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("ledger_token");
    }
    return Promise.reject(err);
  }
);

// Only fall back when backend is completely unreachable (no response at all).
// For timeouts and server errors, throw so callers can show real error messages.
export async function withFallback(request, fallback) {
  try {
    const res = await request();
    return res.data;
  } catch (err) {
    const networkDown = !err.response; // no HTTP response = server unreachable
    if (networkDown) {
      console.warn("[api] backend unreachable:", err?.message);
      return typeof fallback === "function" ? fallback() : fallback;
    }
    throw err; // real HTTP error — let callers handle it
  }
}
