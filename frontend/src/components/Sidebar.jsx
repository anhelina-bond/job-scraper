import { NavLink } from 'react-router-dom';
import { Search, History, Cpu } from 'lucide-react';

export default function Sidebar() {
  const menuItems = [
    { path: '/analyse', label: 'New Analysis', icon: Search },
    { path: '/history', label: 'History', icon: History },
    {path: '/cv-manager', label: 'CV Manager', icon: Cpu}
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
      <div className="p-6 flex items-center gap-3">
        <div className="bg-cyan-500 p-2 rounded-lg"><Cpu className="text-slate-900" size={20} /></div>
        <span className="font-bold text-xl">AgentFlow</span>
      </div>

      <nav className="flex-1 px-4 space-y-2 mt-4">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `
              w-full flex items-center gap-3 px-4 py-3 rounded-xl transition
              ${isActive 
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' 
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}
            `}
          >
            <item.icon size={20} />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}