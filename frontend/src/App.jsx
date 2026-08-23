import { useEffect, useRef } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import { DocumentsProvider, useDocuments } from "./context/DocumentsContext.jsx";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Upload from "./pages/Upload.jsx";
import Research from "./pages/Research.jsx";
import Comparison from "./pages/Comparison.jsx";
import Reports from "./pages/Reports.jsx";
import SignIn from "./pages/SignIn.jsx";
import SignUp from "./pages/SignUp.jsx";

// Watches every route change and refreshes the document list.
// This is the core fix: DocumentsProvider never unmounts so its
// initial useEffect only runs once. This component re-runs on
// every navigation so all pages always have fresh data.
function RouteRefresher() {
  const location  = useLocation();
  const { refresh } = useDocuments();
  const prevPath  = useRef(null);

  useEffect(() => {
    if (prevPath.current !== null && prevPath.current !== location.pathname) {
      refresh();
    }
    prevPath.current = location.pathname;
  }, [location.pathname]); // eslint-disable-line

  // Also refresh when window gains focus (user comes back after uploading)
  useEffect(() => {
    const fn = () => refresh();
    window.addEventListener("focus", fn);
    return () => window.removeEventListener("focus", fn);
  }, []); // eslint-disable-line

  return null;
}

function PublicRoutes() {
  return (
    <Routes>
      <Route path="/login"  element={<SignIn />} />
      <Route path="/signup" element={<SignUp />} />
      <Route path="*"       element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function PrivateRoutes() {
  return (
    <DocumentsProvider>
      <RouteRefresher />
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
