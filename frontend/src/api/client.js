import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

export const client = axios.create({
  baseURL,
  timeout: 15000,
});

// Attach stored token to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("ledger_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401: clear the token but DO NOT redirect — let React router handle it.
// Redirecting here causes a hard reload which re-runs the boot check which
// triggers another 401 → infinite blank-page loop.
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("ledger_token");
      // Don't redirect — AuthContext will see user=null and render /login
    }
    return Promise.reject(err);
  }
);

export async function withFallback(request, fallback) {
  try {
    const res = await request();
    return res.data;
  } catch (err) {
    console.warn("[ledger] backend unavailable, using fallback:", err?.message);
    return typeof fallback === "function" ? fallback() : fallback;
  }
}
