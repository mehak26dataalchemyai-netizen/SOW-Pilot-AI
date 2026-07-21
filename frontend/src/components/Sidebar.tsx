import React from 'react';
import { 
  LayoutDashboard, 
  FolderGit2, 
  Cpu, 
  FileText, 
  Settings, 
  Radio, 
  Users,
  Sun,
  Moon,
  Compass
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  backendConnected: boolean;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
}

export default function Sidebar({ currentTab, setCurrentTab, backendConnected, theme, toggleTheme }: SidebarProps) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'projects', label: 'Projects', icon: FolderGit2 },
    { id: 'processing', label: 'AI Processing', icon: Cpu },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'workers', label: 'Workers', icon: Users },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900/60 border-r border-slate-800/80 flex flex-col h-screen sticky top-0 backdrop-blur-xl">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800/50 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
          <Compass className="w-5 h-5 text-white animate-spin-slow" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white tracking-wider leading-tight">SOWPilot AI</h1>
          <span className="text-[10px] text-brand-400 font-semibold uppercase tracking-widest glow-text">Enterprise</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentTab(item.id)}
              className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                isActive 
                  ? 'bg-gradient-to-r from-brand-900/50 to-brand-800/10 text-white border-l-2 border-brand-400 shadow-inner' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40 hover:translate-x-1'
              }`}
            >
              <Icon className={`w-[18px] h-[18px] transition-transform duration-300 ${isActive ? 'text-brand-400 scale-110' : ''}`} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* System Status and Metadata Footer */}
      <div className="p-4 border-t border-slate-800/50 space-y-3">
        <div className="glass-panel p-3.5 rounded-xl border border-slate-800/40 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-slate-400 font-medium">Server API</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${backendConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></span>
              <span className={`font-semibold ${backendConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
                {backendConnected ? 'Connected' : 'Offline'}
              </span>
            </div>
          </div>
          <p className="text-[10px] text-slate-500 font-light">Localhost v1.0.0 (FastAPI)</p>
        </div>

        {/* Theme Toggle option */}
        <div className="flex items-center justify-between bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/40 text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1.5">
            {theme === 'dark' ? <Moon className="w-3.5 h-3.5 text-slate-400" /> : <Sun className="w-3.5 h-3.5 text-amber-500" />}
            <span>{theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>
          </span>
          <button
            type="button"
            onClick={toggleTheme}
            className="w-10 h-5 bg-slate-800 hover:bg-slate-700 rounded-full p-0.5 transition-colors relative flex items-center shrink-0"
          >
            <span className={`w-4 h-4 rounded-full bg-brand-400 transition-all shadow absolute ${
              theme === 'light' ? 'right-0.5' : 'left-0.5'
            }`} />
          </button>
        </div>

        <div className="text-[10px] text-slate-600 text-center font-light">
          Powered by Gemini 2.5 Flash
        </div>
      </div>
    </aside>
  );
}
