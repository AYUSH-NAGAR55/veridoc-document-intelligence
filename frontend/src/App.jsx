import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import DashboardPage from "./pages/DashboardPage";
import DocumentsPage from "./pages/DocumentsPage";
import DocumentDetailPage from "./pages/DocumentDetailPage";
import { api } from "./lib/api";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api.listDocuments().then((docs) => {
      setDocuments(docs);
      setLoaded(true);
    }).catch(() => setLoaded(true));
  }, []);

  return (
    <div className="flex min-h-screen bg-paper font-body">
      <Sidebar documents={documents} />
      <main className="flex-1">
        {loaded && (
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage documents={documents} setDocuments={setDocuments} />} />
            <Route path="/documents/:id" element={<DocumentDetailPage />} />
          </Routes>
        )}
      </main>
    </div>
  );
}
