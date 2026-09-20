/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { getCVs, uploadCV, deleteCV } from '../api';
import { FileUp, Trash2, CheckCircle2, FileText, Loader2 } from 'lucide-react';

export default function CVManager() {
  const [cvs, setCvs] = useState([]);
  const [file, setFile] = useState(null);
  const [label, setLabel] = useState("");
  const [uploading, setUploading] = useState(false);

  const fetchCvs = async () => {
    const { data } = await getCVs();
    setCvs(data);
  };

  useEffect(() => {
    const timeoutId = setTimeout(fetchCvs, 0);
    return () => clearTimeout(timeoutId);
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !label) return;
    setUploading(true);
    try {
      await uploadCV(file, label);
      setFile(null); setLabel("");
      fetchCvs();
    } catch (err) { alert("Upload failed"); }
    finally { setUploading(false); }
  };

  const handleDelete = async (id) => {
    if (window.confirm("Delete this CV and all its indexed data?")) {
      await deleteCV(id);
      fetchCvs();
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <header>
        <h2 className="text-3xl font-bold">CV Library</h2>
        <p className="text-slate-400">Manage your different resumes and professional personas.</p>
      </header>

      {/* Upload Section */}
      <form onSubmit={handleUpload} className="bg-slate-900 border border-slate-800 p-6 rounded-3xl flex flex-col md:flex-row gap-4 items-end shadow-xl">
        <div className="flex-1 space-y-2">
          <label className="text-xs font-bold text-slate-500 uppercase ml-1">CV Label</label>
          <input 
            type="text" placeholder="e.g. Frontend Engineer 2024" 
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:ring-1 focus:ring-cyan-500"
            value={label} onChange={e => setLabel(e.target.value)}
          />
        </div>
        <div className="flex-1 space-y-2">
          <label className="text-xs font-bold text-slate-500 uppercase ml-1">PDF File</label>
          <input 
            type="file" accept=".pdf" 
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm"
            onChange={e => setFile(e.target.files[0])}
          />
        </div>
        <button 
          disabled={uploading || !file || !label}
          className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-3 rounded-xl font-bold transition disabled:opacity-50"
        >
          {uploading ? <Loader2 className="animate-spin" /> : <FileUp size={20} />}
        </button>
      </form>

      {/* CV List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {cvs.map(cv => (
          <div key={cv.id} className="bg-slate-900 border border-slate-800 p-5 rounded-2xl flex items-center justify-between group">
            <div className="flex items-center gap-4">
              <div className="bg-slate-800 p-3 rounded-xl text-cyan-400">
                <FileText size={24} />
              </div>
              <div>
                <h4 className="font-bold text-slate-100">{cv.label}</h4>
                <p className="text-xs text-slate-500">{cv.filename}</p>
              </div>
            </div>
            <button 
              onClick={() => handleDelete(cv.id)}
              className="p-2 text-slate-600 hover:text-red-400 transition"
            >
              <Trash2 size={18} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}