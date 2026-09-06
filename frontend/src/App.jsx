/* eslint-disable no-unused-vars */
import React, { useState } from 'react';
import { analyseJob, reEvaluateJob } from './api';
import {
  Loader2,
  Globe,
  FileText,
  CheckCircle2,
  AlertCircle,
  Copy,
  History,
  Sparkles,
  MessageSquare,
  RefreshCcw,
  Send,
} from 'lucide-react';

const STEPS = [
  { id: 'scraping', label: 'Scraping Job Posting' },
  { id: 'analysing', label: 'Extracting Requirements' },
  { id: 'matching', label: 'Matching with CV' },
  { id: 'generating', label: 'Writing Cover Letter' }
];

export default function App() {
  const [url, setUrl] = useState('');
  const [manualText, setManualText] = useState('');
  const [useManual, setUseManual] = useState(false);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState("");


  const handleFeedbackSubmit = async () => {
    if (!feedback.trim()) return;

    setLoading(true);
    try {
      // We pass only the raw data needed; the API helper handles the object structure
      const { data } = await reEvaluateJob(result.id, feedback);
      
      // Update the result state with the new letter and the new evaluation
      setResult(prev => ({
        ...prev, 
        cover_letter: data.cover_letter, 
        evaluation: data.evaluation 
      }));
      
      setFeedback(""); // Clear the input box
    } catch (err) {
      console.error(err);
      setError("Failed to refine the letter. Please check the backend logs.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyse = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setStep(0);

    // Simulate progress while waiting for the long API call
    const interval = setInterval(() => {
      setStep((prev) => (prev < 3 ? prev + 1 : prev));
    }, 3000);

    try {
      const payload = useManual ? { manual_text: manualText } : { url };
      const { data } = await analyseJob(payload);
      setResult(data);
      setStep(4); // All done
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Try pasting the text manually.");
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12 font-sans">
      <div className="max-w-5xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            AI Job Agent
          </h1>
          <p className="text-slate-400 mt-2">Tailor your application in seconds.</p>
        </header>

        {!result && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">
            <div className="flex gap-4 mb-6">
              <button 
                onClick={() => setUseManual(false)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${!useManual ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400'}`}
              >
                <Globe size={18} /> URL Mode
              </button>
              <button 
                onClick={() => setUseManual(true)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${useManual ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400'}`}
              >
                <FileText size={18} /> Paste Text
              </button>
            </div>

            {useManual ? (
              <textarea
                className="w-full h-48 bg-slate-950 border border-slate-800 rounded-xl p-4 focus:ring-2 focus:ring-cyan-500 outline-none"
                placeholder="Paste the job description here..."
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
              />
            ) : (
              <input
                type="text"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 focus:ring-2 focus:ring-cyan-500 outline-none"
                placeholder="https://linkedin.com/jobs/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            )}

            <button
              onClick={handleAnalyse}
              disabled={loading}
              className="w-full mt-6 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold py-4 rounded-xl transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="animate-spin" /> : "Start AI Analysis"}
            </button>

            {error && (
              <div className="mt-4 p-4 bg-red-900/20 border border-red-800 text-red-400 rounded-lg flex items-center gap-2">
                <AlertCircle size={20} /> {error}
              </div>
            )}
          </div>
        )}

        {loading && (
          <div className="mt-12 space-y-6 max-w-md mx-auto">
            {STEPS.map((s, idx) => (
              <div key={s.id} className={`flex items-center gap-4 transition-opacity ${step >= idx ? 'opacity-100' : 'opacity-30'}`}>
                {step > idx ? <CheckCircle2 className="text-green-500" /> : <Loader2 className={`animate-spin ${step === idx ? 'text-cyan-500' : 'text-slate-600'}`} />}
                <span className={step === idx ? 'text-cyan-400 font-medium' : ''}>{s.label}</span>
              </div>
            ))}
          </div>
        )}

        {result && (
          <div className="mt-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            
            {/* TOP BAR: AI CRITIC INSIGHTS */}
            <div className={`p-5 rounded-2xl border-2 flex flex-col md:flex-row md:items-center gap-6 ${
              result.evaluation?.score > 80 ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-amber-500/5 border-amber-500/20'
            }`}>
              <div className="flex items-center gap-4 border-r border-slate-800 pr-6">
                <div className="relative">
                  <svg className="w-16 h-16 transform -rotate-90">
                    <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-slate-800" />
                    <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="4" fill="transparent" 
                      className={result.evaluation?.score > 80 ? 'text-emerald-500' : 'text-amber-500'}
                      strokeDasharray={175.9}
                      strokeDashoffset={175.9 - (175.9 * (result.evaluation?.score || 0)) / 100}
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center font-bold text-sm">
                    {result.evaluation?.score}%
                  </span>
                </div>
                <div>
                  <h3 className="font-bold text-slate-100">AI Quality Score</h3>
                  <p className="text-xs text-slate-400 uppercase tracking-wider">Expert Evaluation</p>
                </div>
              </div>
              
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1 text-amber-400">
                  <Sparkles size={16} />
                  <span className="text-sm font-semibold uppercase tracking-tight">Critic's Review</span>
                </div>
                <p className="text-slate-300 text-sm italic leading-relaxed">
                  "{result.evaluation?.critique || "Reviewing the draft for specificity and impact..."}"
                </p>
              </div>
            </div>

            {/* MAIN WORKSPACE */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
              
              {/* LEFT COLUMN: EVIDENCE & ANALYSIS */}
              <div className="space-y-6">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <CheckCircle2 className="text-cyan-400" size={20} />
                    Skill Match Evidence
                  </h2>
                  <div className="space-y-4">
                    {result.requirements_analysis.map((req, i) => (
                      <div key={i} className="group bg-slate-950/50 border border-slate-800/50 p-4 rounded-xl hover:border-slate-700 transition">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-medium text-slate-200 text-sm leading-tight pr-4">{req.requirement}</span>
                          <div className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                            req.score > 70 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                          }`}>
                            {req.score}% Match
                          </div>
                        </div>
                        <p className="text-xs text-slate-500 leading-normal line-clamp-2 group-hover:line-clamp-none transition-all">
                          {req.reasoning}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* RIGHT COLUMN: THE DRAFT & FEEDBACK LOOP */}
              <div className="flex flex-col gap-6">
                
                {/* THE LETTER DRAFT */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[550px] shadow-2xl overflow-hidden">
                  <div className="bg-slate-800/50 px-6 py-3 border-b border-slate-800 flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Draft Version 1.0</span>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(result.cover_letter);
                        alert("Copied to clipboard!");
                      }}
                      className="flex items-center gap-2 text-xs font-bold text-cyan-400 hover:text-cyan-300 transition"
                    >
                      <Copy size={14} /> COPY DRAFT
                    </button>
                  </div>
                  <div className="p-8 text-slate-300 whitespace-pre-wrap leading-relaxed text-sm overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700">
                    {result.cover_letter}
                  </div>
                </div>

                {/* THE HITL FEEDBACK BOX */}
                <div className="bg-cyan-950/20 border border-cyan-500/20 rounded-2xl p-6 shadow-inner">
                  <div className="flex items-center gap-2 mb-4">
                    <MessageSquare size={18} className="text-cyan-400" />
                    <h3 className="font-bold text-slate-100">Refine with AI Instructions</h3>
                  </div>
                  
                  <div className="relative">
                    <textarea 
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 placeholder:text-slate-600 focus:ring-2 focus:ring-cyan-500 outline-none transition resize-none h-24"
                      placeholder="Example: 'Emphasize my experience with Manufacturing AI' or 'Make the tone more punchy and less formal'..."
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                    />
                    <button 
                      onClick={handleFeedbackSubmit}
                      disabled={loading || !feedback.trim()}
                      className="absolute bottom-3 right-3 p-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition disabled:opacity-50 disabled:bg-slate-800"
                    >
                      {loading ? <RefreshCcw className="animate-spin" size={18} /> : <Send size={18} />}
                    </button>
                  </div>
                  <p className="mt-3 text-[10px] text-slate-500 text-center uppercase tracking-widest">
                    The agent will keep all matches but rewrite based on your notes
                  </p>
                </div>

              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}