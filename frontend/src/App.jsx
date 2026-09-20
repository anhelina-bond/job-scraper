import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import AnalyseView from './components/AnalyseView';
import ResultView from './components/ResultView';
import HistoryView from './components/HistoryView';
import CVManager from './components/CVManager';

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
        <Sidebar />
        <main className="flex-1 p-6 md:p-12 overflow-y-auto">
          <div className="max-w-6xl mx-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/analyse" />} />
              <Route path="/analyse" element={<AnalyseView />} />
              <Route path="/history" element={<HistoryView />} />
              <Route path="/cv-manager" element={<CVManager />} />
              <Route path="/applications/:id" element={<ResultView />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}