import axios from "axios";

// Set this in .env (local) and in your Vercel/Render project's environment
// variables. It must point at your deployed FastAPI backend, e.g.
// https://finresearch-backend.onrender.com
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

// Attach auth token automatically if one is stored (no-op until you wire up auth)
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("ledger_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalize errors so every page can rely on `error.message`
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Something went wrong. Please try again.";
    return Promise.reject(new Error(message));
  }
);

export default client;
