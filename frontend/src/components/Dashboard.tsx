import React from 'react';
import { 
  FolderGit2, 
  Mail, 
  Cpu, 
  DollarSign, 
  Users, 
  Clock, 
  TrendingUp, 
  Award, 
  ArrowRight,
  Compass,
  Loader2
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';

interface DashboardStats {
  projects_processed: number;
  emails_received: number;
  ai_agents_executed: number;
  estimated_budget: number;
  total_resources: number;
  project_duration_weeks: number;
  recent_projects: Array<{
    project_name: string;
    client: string;
    budget: number | string;
    readiness_score: number;
    processed_at: string;
  }>;
}

interface DashboardProps {
  stats: DashboardStats;
  loading: boolean;
  onNavigateToProcessing: () => void;
  onSelectProject: (projectName: string) => void;
  onScanGmail: () => void;
  scanningGmail: boolean;
}

export default function Dashboard({ stats, loading, onNavigateToProcessing, onSelectProject, onScanGmail, scanningGmail }: DashboardProps) {
  
  const formatCurrency = (val: number) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
    return `$${val}`;
  };

  // Setup cards
  const cards = [
    {
      label: 'Projects Processed',
      value: stats.projects_processed,
      icon: FolderGit2,
      color: 'from-blue-600/20 to-blue-400/5',
      border: 'border-blue-500/20',
      iconColor: 'text-blue-400'
    },
    {
      label: 'Emails Ingested',
      value: stats.emails_received,
      icon: Mail,
      color: 'from-indigo-600/20 to-indigo-400/5',
      border: 'border-indigo-500/20',
      iconColor: 'text-indigo-400'
    },
    {
      label: 'AI Agents Run',
      value: stats.ai_agents_executed,
      icon: Cpu,
      color: 'from-brand-600/20 to-brand-400/5',
      border: 'border-brand-500/20',
      iconColor: 'text-brand-400'
    },
    {
      label: 'Estimated Budget',
      value: formatCurrency(stats.estimated_budget),
      icon: DollarSign,
      color: 'from-emerald-600/20 to-emerald-400/5',
      border: 'border-emerald-500/20',
      iconColor: 'text-emerald-400'
    },
    {
      label: 'Total Resources',
      value: stats.total_resources,
      icon: Users,
      color: 'from-violet-600/20 to-violet-400/5',
      border: 'border-violet-500/20',
      iconColor: 'text-violet-400'
    },
    {
      label: 'Avg SOW Duration',
      value: `${stats.project_duration_weeks} Weeks`,
      icon: Clock,
      color: 'from-sky-600/20 to-sky-400/5',
      border: 'border-sky-500/20',
      iconColor: 'text-sky-400'
    }
  ];

  // Map charts data
  const chartData = stats.recent_projects.slice(0, 6).map(p => {
    let rawVal = 0;
    if (typeof p.budget === 'number') {
      rawVal = p.budget;
    } else if (typeof p.budget === 'string') {
      rawVal = parseFloat(p.budget.replace(/[$,]/g, '')) || 0;
    }
    return {
      name: p.project_name.length > 12 ? `${p.project_name.slice(0, 10)}...` : p.project_name,
      fullName: p.project_name,
      Budget: rawVal,
      Score: p.readiness_score
    };
  }).reverse();

  if (loading) {
    return (
      <div className="p-8 space-y-8 animate-pulse">
        <div className="h-10 w-48 bg-slate-800/60 rounded-lg"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-28 bg-slate-800/40 border border-slate-800/60 rounded-2xl"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[350px] bg-slate-800/40 border border-slate-800/60 rounded-2xl"></div>
          <div className="h-[350px] bg-slate-800/40 border border-slate-800/60 rounded-2xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Delivery Planning Hub</h1>
          <p className="text-slate-400 text-sm mt-1">Real-time portfolio overview parsed from email SOW attachments.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button 
            onClick={onScanGmail}
            disabled={scanningGmail}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold border border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-white shadow transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none transform active:scale-95"
          >
            {scanningGmail ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
                Scanning Gmail...
              </>
            ) : (
              <>
                <Mail className="w-4 h-4 text-brand-400" />
                Sync Gmail Inbox
              </>
            )}
          </button>

          <button 
            onClick={onNavigateToProcessing}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white shadow-lg shadow-brand-600/15 hover:shadow-brand-500/25 transition-all duration-300 transform hover:-translate-y-0.5"
          >
            <Cpu className="w-4 h-4" />
            Ingest Project SOW
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div 
              key={idx}
              className={`glass-panel bg-gradient-to-br ${card.color} border ${card.border} p-5 rounded-2xl hover:scale-[1.03] transition-all duration-300 flex flex-col justify-between h-auto min-h-[116px] pb-4`}
            >
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">{card.label}</span>
                <Icon className={`w-5 h-5 ${card.iconColor}`} />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight mt-2">{card.value}</div>
            </div>
          );
        })}
      </div>

      {/* Main Sections */}
      {stats.projects_processed === 0 ? (
        <div className="glass-panel border-slate-800/40 p-12 text-center rounded-2xl max-w-2xl mx-auto space-y-6">
          <div className="w-16 h-16 rounded-full bg-brand-500/10 flex items-center justify-center mx-auto text-brand-400 animate-bounce">
            <Compass className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-white">No Projects Processed Yet</h2>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              SOWPilot is currently waiting for email inputs or document uploads. Add a project SOW to execute the AI orchestration graph.
            </p>
          </div>
          <button 
            onClick={onNavigateToProcessing}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition-all"
          >
            Go to Ingestion Panel
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Budget Trend Bar Chart */}
          <div className="lg:col-span-2 glass-panel border-slate-800/40 p-6 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-brand-400" />
                  Budget Distribution
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">Financial estimates mapped per processed project.</p>
              </div>
            </div>
            
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis 
                    stroke="#94a3b8" 
                    fontSize={11} 
                    tickLine={false}
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} 
                  />
                  <Tooltip 
                    contentStyle={{ background: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                    labelStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                    formatter={(v) => [`$${Number(v).toLocaleString()}`, 'Estimated Budget']}
                  />
                  <Bar dataKey="Budget" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill="url(#barGradient)" />
                    ))}
                  </Bar>
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#38a9f8" />
                      <stop offset="100%" stopColor="#03589c" />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Projects List */}
          <div className="glass-panel border-slate-800/40 p-6 rounded-2xl flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-1">
                <Award className="w-5 h-5 text-brand-400" />
                Recent Projects
              </h3>
              <p className="text-xs text-slate-400 mb-5">Click on a project to view full reports.</p>
            </div>

            <div className="space-y-3.5 overflow-y-auto max-h-[300px] pr-1">
              {stats.recent_projects.map((proj, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectProject(proj.project_name)}
                  className="w-full text-left glass-panel-hover bg-slate-900/40 border border-slate-800/40 p-3.5 rounded-xl flex items-center justify-between group"
                >
                  <div className="space-y-1 pr-2 truncate">
                    <h4 className="text-sm font-semibold text-slate-200 group-hover:text-white truncate">
                      {proj.project_name}
                    </h4>
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span className="truncate">{proj.client}</span>
                      <span>•</span>
                      <span className="text-brand-400 font-medium">
                        {typeof proj.budget === 'number' 
                          ? `$${proj.budget.toLocaleString()}` 
                          : proj.budget}
                      </span>
                    </div>
                  </div>
                  
                  {/* Score circle */}
                  <div className="flex items-center gap-2 shrink-0">
                    <div className="flex flex-col items-end">
                      <span className="text-[10px] text-slate-500 uppercase tracking-widest">Score</span>
                      <span className="text-sm font-bold text-slate-200">{proj.readiness_score}%</span>
                    </div>
                    <div className="w-8 h-8 rounded-full border border-slate-700/60 flex items-center justify-center bg-slate-950">
                      <span className={`w-2.5 h-2.5 rounded-full ${
                        proj.readiness_score >= 80 
                          ? 'bg-emerald-400' 
                          : proj.readiness_score >= 60 
                            ? 'bg-amber-400' 
                            : 'bg-rose-400'
                      }`}></span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
