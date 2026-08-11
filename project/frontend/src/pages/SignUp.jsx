import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function SignUp() {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim() || !password || !confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }
    if (password.length < 4) {
      setError("Password must be at least 4 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await signUp(username.trim(), password);
      navigate("/");
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        "Failed to sign up. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-parchment-100 p-6">
      <div className="absolute -right-16 -top-16 h-80 w-80 rounded-full opacity-40 blur-3xl" style={{ background: "radial-gradient(circle, rgba(139,92,246,0.25) 0%, rgba(20,184,166,0.12) 100%)" }} />
      <div className="absolute -bottom-20 left-1/4 h-80 w-80 rounded-full opacity-35 blur-3xl" style={{ background: "radial-gradient(circle, rgba(251,113,133,0.15) 0%, transparent 100%)" }} />
      
      <div className="card w-full max-w-md p-8 border border-slate-200/80 shadow-xl shadow-slate-200/40 relative z-10 animate-fade-up">
        <div className="text-center mb-8">
          <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl text-white text-xl font-bold shadow-md shadow-violet-200 mb-4" style={{ background: "linear-gradient(135deg,#8B5CF6 0%,#14B8A6 100%)" }}>
            M
          </span>
          <h1 className="font-display text-2xl font-extrabold text-ledger-950">Create Account</h1>
          <p className="text-xs font-semibold text-slate-400 mt-1 uppercase tracking-wider">
            Multi-Agent Financial Research System
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-100 text-xs text-rose-700 font-semibold animate-scale-in">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-ledger-950/70 mb-2 uppercase tracking-wide">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Choose a username"
              className="field"
              autoComplete="username"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-ledger-950/70 mb-2 uppercase tracking-wide">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 4 characters"
              className="field"
              autoComplete="new-password"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-ledger-950/70 mb-2 uppercase tracking-wide">Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              className="field"
              autoComplete="new-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3.5 mt-2 rounded-xl text-sm font-semibold shadow-md cursor-pointer flex items-center justify-center"
          >
            {loading ? (
              <>
                <span className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Creating Account...
              </>
            ) : (
              "Sign Up"
            )}
          </button>
        </form>

        <div className="mt-8 border-t border-slate-100 pt-6 text-center">
          <p className="text-xs text-slate-400 font-semibold">
            Already have an account?{" "}
            <Link to="/login" className="text-violet-600 hover:text-violet-700 hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
