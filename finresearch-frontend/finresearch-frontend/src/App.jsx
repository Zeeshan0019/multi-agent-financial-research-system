import React from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Upload from "./pages/Upload.jsx";
import Research from "./pages/Research.jsx";
import Comparison from "./pages/Comparison.jsx";
import Reports from "./pages/Reports.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/research" element={<Research />} />
        <Route path="/comparison" element={<Comparison />} />
        <Route path="/reports" element={<Reports />} />
      </Route>
    </Routes>
  );
}
