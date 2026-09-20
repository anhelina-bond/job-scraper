import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Copy, Send, Sparkles, ArrowLeft, RefreshCw, ExternalLink, Eye, Zap } from 'lucide-react';
import { getApplicationById, reEvaluateJob } from '../api';

export default function ResultView() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  // State management
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState(""); // Missing in your snippet
  const [isUpdating, setIsUpdating] = useState(false); // Missing in your snippet

  useEffect(() => {
    console.log("Fetching ID:", id); // DEBUG LOG 1
    getApplicationById(id)
      .then(res => {
        console.log("Data received:", res.data); // DEBUG LOG 2
        setResult({
          ...res.data,
          // Handle the naming difference between DB column and UI state
          requirements_analysis: res.data.cv_matches || [] 
        });
        setLoading(false);
      })
      .catch((err) => {
        console.error("Fetch error:", err); // DEBUG LOG 3
        // navigate('/history'); // Comment this out temporarily to see the error
      });
  }, [id]);

  if (loading) return <div className="p-20 text-center text-cyan-500">Loading Application {id}...</div>;
  if (!result) return <div className="p-20 text-center text-red-500">Application not found.</div>;

  // Logic for HITL Refinement
  const handleRefine = async () => {
    if (!feedback.trim()) return;
    setIsUpdating(true);
    try {
      const { data } = await reEvaluateJob(id, feedback);
      
      // Update local state with the revised letter and new evaluation
      setResult(prev => ({
        ...prev,
        cover_letter: data.cover_letter,
        evaluation: data.evaluation
      }));
      setFeedback(""); // Clear input on success
    } catch (err) {
      alert("Refinement failed. Check backend logs. ", err);
    } finally {
      setIsUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <RefreshCw className="animate-spin text-cyan-500" size={40} />
        <p className="text-slate-400 animate-pulse">Loading Application Details...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header Actions */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-2">
        <button 
            onClick={() => navigate('/history')} 
            className="flex items-center gap-2 text-slate-400 hover:text-white transition group"
        >
            <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" /> 
            Back to History
        </button>
        
        <div className="flex flex-wrap gap-2">
            {/* Match Score Tag */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold border transition ${
            result.match_score >= 80 ? 'bg-green-500/10 text-green-400 border-green-500/20' : 
            result.match_score >= 50 ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' : 
            'bg-red-500/10 text-red-400 border-red-500/20'
            }`}>
            <Zap size={14} fill="currentColor" />
            Match Score: {Math.round(result.match_score)}%
            </div>

            {/* Job Posting Link */}
            <a 
            href={result.job_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg text-xs font-bold text-slate-300 border border-slate-700 transition"
            >
            <ExternalLink size={14} className="text-cyan-400" />
            {result.company} — {result.job_title}
            </a>

            {/* Used CV Link */}
            {result.cv_id && (
            <a 
                href={`http://127.0.0.1:8000/api/cvs/${result.cv_id}/view`} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-2 bg-cyan-500/10 hover:bg-cyan-500/20 px-3 py-1.5 rounded-lg text-xs font-bold text-cyan-400 border border-cyan-500/20 transition"
            >
                <Eye size={14} />
                Used CV: {result.cv_label || "View PDF"}
            </a>
            )}
        </div>
        </div>

      {/* Evaluation Bar */}
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1 text-amber-400">
            <Sparkles size={14} />
            <span className="text-xs font-bold uppercase tracking-tight">Gap Analysis</span>
        </div>
        <p className="text-slate-300 text-sm italic mb-2">
            "{result.evaluation?.critique}"
        </p>
        
        {/* NEW: Show specific missing points as tags */}
        {result.evaluation?.missing_points?.length > 0 && (
            <div className="flex flex-wrap gap-2">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Try adding:</span>
            {result.evaluation.missing_points.map((point, i) => (
                <span key={i} className="bg-slate-800 text-slate-300 text-[10px] px-2 py-0.5 rounded border border-slate-700">
                {point}
                </span>
            ))}
            </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Match Evidence (Left) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-fit">
            <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold flex items-center gap-2">
                <Sparkles size={18} className="text-cyan-400" />
                CV Matching Evidence
                </h3>
                {/* Large score display */}
                <div className="text-right">
                <div className="text-2xl font-black text-white">{Math.round(result.match_score)}%</div>
                <div className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Overall Match</div>
                </div>
            </div>

            <div className="space-y-4">
                {result.requirements_analysis?.map((req, i) => (
                <div key={i} className="border-l-2 border-slate-800 pl-4 py-1 hover:border-cyan-500 transition-colors group">
                    <div className="flex justify-between items-start">
                    <div className="text-sm font-semibold group-hover:text-cyan-100 transition-colors">{req.requirement}</div>
                    {/* Individual requirement score */}
                    <span className={`text-[10px] font-bold ${req.score >= 70 ? 'text-green-500' : 'text-yellow-500'}`}>
                        {req.score}%
                    </span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1 leading-relaxed">{req.reasoning}</div>
                </div>
                ))}
            </div>
        </div>
        {/* Letter & HITL (Right) */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 relative shadow-2xl">
             <button 
               onClick={() => {
                 navigator.clipboard.writeText(result.cover_letter);
                 alert("Copied!");
               }}
               className="absolute top-6 right-6 p-2 hover:bg-slate-800 rounded-lg text-slate-400 transition"
               title="Copy to clipboard"
             >
               <Copy size={20} />
             </button>
             {/* Optimized height class h-100 instead of h-[400px] for Tailwind v4 */}
             <div className="text-slate-300 whitespace-pre-wrap leading-relaxed text-sm h-100 overflow-y-auto pr-2 custom-scrollbar">
               {result.cover_letter}
             </div>
          </div>

          {/* Feedback Loop (Human-in-the-Loop) */}
          <div className="bg-cyan-500/5 border border-cyan-500/10 rounded-2xl p-6 shadow-inner">
            <h4 className="text-sm font-bold text-cyan-400 mb-3 uppercase tracking-tighter">Human-in-the-Loop Refinement</h4>
            <div className="flex gap-2">
              <input 
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:ring-1 focus:ring-cyan-500 outline-none transition-all"
                placeholder="Ex: Mention my project in React more..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleRefine()}
              />
              <button 
                onClick={handleRefine}
                disabled={isUpdating || !feedback.trim()}
                className="bg-cyan-600 hover:bg-cyan-500 px-6 rounded-xl transition-all disabled:opacity-50 disabled:bg-slate-800 flex items-center justify-center min-w-[60px]"
              >
                {isUpdating ? <RefreshCw className="animate-spin" size={18} /> : <Send size={18} />}
              </button>
            </div>
            <p className="text-[10px] text-slate-600 mt-2 text-center italic">The agent will rewrite the letter while preserving original matches.</p>
          </div>
        </div>
      </div>
    </div>
  );
}