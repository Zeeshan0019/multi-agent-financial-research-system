import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import { DocumentsProvider } from "./context/DocumentsContext.jsx";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Upload from "./pages/Upload.jsx";
import Research from "./pages/Research.jsx";
import Comparison from "./pages/Comparison.jsx";
import Reports from "./pages/Reports.jsx";
import SignIn from "./pages/SignIn.jsx";
import SignUp from "./pages/SignUp.jsx";

// Unauthenticated routes — no DocumentsProvider needed
function PublicRoutes() {
  return (
    <Routes>
      <Route path="/login"  element={<SignIn />} />
      <Route path="/signup" element={<SignUp />} />
      <Route path="*"       element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

// Authenticated routes — DocumentsProvider lives here, after auth is confirmed
function PrivateRoutes() {
  return (
    <DocumentsProvider>
      <Layout>
        <Routes>
          <Route path="/"           element={<Dashboard />} />
          <Route path="/upload"     element={<Upload />} />
          <Route path="/research"   element={<Research />} />
          <Route path="/comparison" element={<Comparison />} />
          <Route path="/reports"    element={<Reports />} />
          <Route path="*"           element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </DocumentsProvider>
  );
}

export default function App() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-parchment-100">
        <div className="flex flex-col items-center gap-4">
          <span
            className="flex h-12 w-12 items-center justify-center rounded-2xl font-bold text-white text-lg shadow-lg"
            style={{ background: "linear-gradient(135deg,#8B5CF6,#14B8A6)" }}
          >
            M
          </span>
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
        </div>
      </div>
    );
  }

  return isAuthenticated ? <PrivateRoutes /> : <PublicRoutes />;
}
