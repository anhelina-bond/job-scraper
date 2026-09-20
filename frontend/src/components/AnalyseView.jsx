import  { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyseJob, getCVs } from '../api';
import { Loader2, Globe, FileText, CheckCircle2, AlertCircle, Zap } from 'lucide-react';

const STEPS = [
  { id: 'scraping', label: 'Scraping Job Posting' },
  { id: 'analysing', label: 'Extracting Requirements' },
  { id: 'matching', label: 'Matching with CV' },
  { id: 'generating', label: 'Writing Cover Letter' }
];

export default function AnalyseView({ onResult, setGlobalLoading }) {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [manualText, setManualText] = useState('');
  const [useManual, setUseManual] = useState(false);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState(null);
  const [cvs, setCvs] = useState([]);
  const [selectedCvId, setSelectedCvId] = useState("");

  useEffect(() => {
    getCVs().then(res => {
        setCvs(res.data);
        if (res.data.length > 0) setSelectedCvId(res.data[0].id);
    });
  }, []);


  const handleAnalyse = async () => {
    if (!useManual && !url) return setError("Please enter a job URL");
    if (useManual && !manualText) return setError("Please paste the job description");

    setLoading(true);
    // setGlobalLoading(true);
    setError(null);
    setStep(0);

    // Simulated progress tracker based on typical node timings
    const interval = setInterval(() => {
      setStep((prev) => (prev < 3 ? prev + 1 : prev));
    }, 3500);

    try {
      const payload = { 
        cv_id: selectedCvId, // Pass the CV ID to the backend
        ...(useManual ? { manual_text: manualText } : { url })
     };
      const { data } = await analyseJob(payload);
      navigate(`/applications/${data.id}`);
      
      // Success! Pass data back to App.jsx
      onResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "The agent encountered an error. Try pasting the text manually.");
      setStep(0);
    } finally {
      clearInterval(interval);
      setLoading(false);
      setGlobalLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-bold text-white mb-3">Create New Analysis</h2>
        <p className="text-slate-400">Upload a job link or paste the text to let the agent start matching.</p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl">
        {/* Toggle Header */}
        <div className="flex p-1 bg-slate-950 rounded-2xl mb-8 w-fit mx-auto border border-slate-800">
          <button 
            onClick={() => setUseManual(false)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl transition-all duration-200 ${!useManual ? 'bg-cyan-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <Globe size={18} /> <span className="text-sm font-semibold">URL Mode</span>
          </button>
          <button 
            onClick={() => setUseManual(true)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl transition-all duration-200 ${useManual ? 'bg-cyan-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <FileText size={18} /> <span className="text-sm font-semibold">Paste Text</span>
          </button>
        </div>

        {/* Input Fields */}
        <div className="space-y-4">
          {useManual ? (
            <textarea
              className="w-full h-64 bg-slate-950 border border-slate-800 rounded-2xl p-5 focus:ring-2 focus:ring-cyan-500 outline-none text-slate-200 transition-all placeholder:text-slate-700"
              placeholder="Paste the full job description here (Requirements, Responsibilities, etc...)"
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
            />
          ) : (
            <div className="relative">
              <input
                type="text"
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl py-5 pl-14 pr-5 focus:ring-2 focus:ring-cyan-500 outline-none text-slate-200 transition-all placeholder:text-slate-700"
                placeholder="https://linkedin.com/jobs/view/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <Globe className="absolute left-5 top-5 text-slate-600" size={24} />
            </div>
          )}
            {/* CV Selection */}
          <div className="mb-6 space-y-2">
            <label className="text-xs font-black text-slate-500 uppercase tracking-widest ml-1">Select Persona (CV)</label>
            <select 
                value={selectedCvId}
                onChange={(e) => setSelectedCvId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-4 text-slate-200 outline-none focus:ring-1 focus:ring-cyan-500"
            >
                {cvs.map(cv => (
                <option key={cv.id} value={cv.id}>{cv.label}</option>
                ))}
            </select>
            {cvs.length === 0 && (
                <p className="text-amber-500 text-xs mt-2 italic">You haven't uploaded any CVs yet. Please go to CV Library.</p>
            )}
         </div>
          <button
            onClick={handleAnalyse}
            disabled={loading}
            className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-5 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-xl shadow-cyan-900/20"
          >
            {loading ? <Loader2 className="animate-spin" /> : <Zap size={20} fill="currentColor" />}
            {loading ? "Agent is Working..." : "Generate Analysis"}
          </button>
        </div>

        {error && (
          <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl flex items-center gap-3 text-sm animate-shake">
            <AlertCircle size={18} /> {error}
          </div>
        )}
      </div>

      {/* Progress Tracker (Only visible when loading) */}
      {loading && (
        <div className="mt-12 max-w-sm mx-auto space-y-4">
          {STEPS.map((s, idx) => (
            <div 
              key={s.id} 
              className={`flex items-center gap-4 transition-all duration-500 ${step >= idx ? 'opacity-100 translate-x-0' : 'opacity-20 -translate-x-4'}`}
            >
              <div className="flex-shrink-0">
                {step > idx ? (
                  <div className="bg-green-500/20 p-1 rounded-full text-green-500">
                    <CheckCircle2 size={20} />
                  </div>
                ) : (
                  <div className={`p-1 rounded-full ${step === idx ? 'bg-cyan-500/20 text-cyan-500' : 'bg-slate-800 text-slate-600'}`}>
                    <Loader2 size={20} className={step === idx ? 'animate-spin' : ''} />
                  </div>
                )}
              </div>
              <span className={`text-sm font-medium ${step === idx ? 'text-cyan-400' : 'text-slate-500'}`}>
                {s.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}