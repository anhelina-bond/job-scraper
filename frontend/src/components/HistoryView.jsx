import { useEffect, useState } from 'react';
import {useNavigate} from 'react-router-dom';
import { getApplications } from '../api';
import { Calendar, Building2, ChevronRight, Star } from 'lucide-react'; 

export default function HistoryView() {
  const [apps, setApps] = useState([]);
    const navigate = useNavigate();
  useEffect(() => {
    getApplications().then(res => setApps(res.data));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold mb-6">Application History</h2>
      {apps.map(app => (
        <div 
          key={app.id} 
          onClick={() => navigate('/applications/' + app.id)}
          className="bg-slate-900 border border-slate-800 p-5 rounded-2xl hover:border-cyan-500/50 cursor-pointer transition flex items-center justify-between group"
        >
          <div className="flex items-start gap-4 text-start">
            <div className="bg-slate-800 p-3 rounded-xl group-hover:bg-cyan-900/30 transition">
              <Building2 className="text-slate-400 group-hover:text-cyan-400" />
            </div>
            <div>
              <h3 className="font-bold text-slate-100 ">{app.job_title}  —
                <span className="text-sm text-slate-400">  {app.company}</span>
              </h3>
              {app.cv_label && (
                    <>
                    <span className="text-slate-700 text-xs">•</span>
                    <span className="text-[10px] bg-slate-800/50 text-slate-500 px-2 py-0.5 rounded border border-slate-800 font-medium">
                        {app.cv_label}
                    </span>
                    </>
                )}
            </div>
          </div>
          
          <div className="flex items-center gap-8">
            <div className="text-right hidden md:block">
              <div className="flex items-center gap-1 text-cyan-400 font-bold">
                <Star size={14} /> {Math.round(app.match_score)}%
              </div>
              <div className="text-[10px] text-slate-500 flex items-center gap-1 uppercase">
                <Calendar size={10} /> {new Date(app.date_applied).toLocaleDateString()}
              </div>
            </div>
            <ChevronRight className="text-slate-600 group-hover:text-cyan-400" />
          </div>
        </div>
      ))}
    </div>
  );
}