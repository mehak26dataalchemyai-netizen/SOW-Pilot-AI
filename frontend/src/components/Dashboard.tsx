import React from 'react';
import { 
  FolderGit2, 
  Mail, 
  Cpu, 
  DollarSign, 
  Users, 
  Clock, 
  Award, 
  ArrowRight,
  Compass,
  Loader2,
  ChevronRight,
  Calendar,
  AlertCircle,
  UserPlus
} from 'lucide-react';

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
    budget: number | string | { total_cost?: number };
    target_budget?: string;
    readiness_score: number;
    processed_at: string;
  }>;
}

interface DashboardProps {
  stats: DashboardStats;
  loading: boolean;
  onNavigateToProcessing: () => void;
  onSelectProject: (projectName: string) => void;
  onAssignWorkers: (projectName: string) => void;
  onScanGmail: () => void;
  scanningGmail: boolean;
}



export default function Dashboard({ stats, loading, onNavigateToProcessing, onSelectProject, onAssignWorkers, onScanGmail, scanningGmail }: DashboardProps) {
  
  const formatCurrency = (val: number) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
    return `$${val}`;
  };

  const parseBudget = (val: string | number | undefined): number | null => {
    if (val === undefined || val === null) return null;
    if (typeof val === 'number') return val;
    const cleaned = val.replace(/[$,]/g, '').trim();
    if (!cleaned || ['n/a', 'not specified', 'unknown', 'none'].includes(cleaned.toLowerCase())) {
      return null;
    }
    const parsed = parseFloat(cleaned);
    return isNaN(parsed) ? null : parsed;
  };

  // Setup cards
  const cards = [
    {
      label: 'Projects Processed',
      value: stats.projects_processed,
      icon: FolderGit2,
      color: 'from-blue-600/15 to-blue-400/5',
      border: 'border-blue-500/20 hover:border-blue-500/40',
      iconColor: 'text-blue-400 bg-blue-500/10',
      tag: 'Active SOWs'
    },
    {
      label: 'Emails Ingested',
      value: stats.emails_received,
      icon: Mail,
      color: 'from-indigo-600/15 to-indigo-400/5',
      border: 'border-indigo-500/20 hover:border-indigo-500/40',
      iconColor: 'text-indigo-400 bg-indigo-500/10',
      tag: 'Sync Live'
    }
  ];

  if (loading) {
    return (
      <div className="p-8 space-y-8 animate-pulse max-w-7xl mx-auto">
        <div className="h-10 w-48 bg-slate-800/60 rounded-lg"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-32 bg-slate-800/40 border border-slate-800/60 rounded-2xl"></div>
          ))}
        </div>
        <div className="h-[400px] bg-slate-800/40 border border-slate-800/60 rounded-2xl animate-pulse"></div>
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
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div 
              key={idx}
              className={`relative glass-panel bg-gradient-to-br ${card.color} border ${card.border} p-6 rounded-2xl hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-950/20 transition-all duration-300 flex flex-col justify-between min-h-[128px] overflow-hidden group`}
            >
              {/* Subtle card-specific glow highlight inside */}
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-white/5 to-transparent rounded-full -mr-8 -mt-8 transition-transform duration-500 group-hover:scale-125" />
              
              <div className="flex items-start justify-between relative z-10">
                <div className="space-y-1">
                  <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider block">{card.label}</span>
                  <span className="text-[9px] font-semibold text-slate-500 bg-slate-950/40 px-2 py-0.5 rounded border border-slate-900 uppercase tracking-widest inline-block">{card.tag}</span>
                </div>
                <div className={`p-2 rounded-xl ${card.iconColor} border border-white/5 shadow-sm`}>
                  <Icon className="w-4.5 h-4.5" />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-white tracking-tight mt-4 relative z-10">{card.value}</div>
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
        <div className="glass-panel border-slate-800/40 p-6 md:p-8 rounded-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/20 pb-5">
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Award className="w-5.5 h-5.5 text-brand-400" />
                Recent Projects Portfolio
              </h3>
              <p className="text-xs text-slate-400 mt-1">Review the delivery health, budget, and readiness analysis for ingested SOW files.</p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/60 px-3.5 py-2 rounded-xl border border-slate-800/50 self-start sm:self-auto shadow-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-400 animate-pulse shadow-[0_0_8px_rgba(56,169,248,0.5)]"></span>
              <span className="font-medium text-slate-300">Portfolio View: {stats.recent_projects.length} Active {stats.recent_projects.length === 1 ? 'Project' : 'Projects'}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stats.recent_projects.map((proj, idx) => (
              <div
                key={idx}
                onClick={() => onSelectProject(proj.project_name)}
                className="group relative flex flex-col justify-between p-6 rounded-2xl glass-panel hover:border-brand-500/30 hover:bg-slate-900/40 transition-all duration-300 cursor-pointer overflow-hidden hover:shadow-xl hover:shadow-brand-500/5 hover:-translate-y-1"
              >
                {/* Accent line that lights up on hover */}
                <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-brand-500/0 via-brand-500/20 to-brand-500/0 group-hover:via-brand-500/60 transition-all duration-500" />
                
                <div className="space-y-4">
                  {/* Card Header metadata */}
                  <div className="flex justify-between items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-400 bg-slate-900/80 border border-slate-800/80 px-2.5 py-1 rounded-md uppercase tracking-wider truncate max-w-[120px]" title={proj.client}>
                      {proj.client}
                    </span>
                    <span className="text-[10px] text-slate-500 font-medium flex items-center gap-1 shrink-0">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {proj.processed_at || 'Recently'}
                    </span>
                  </div>

                  {/* Project Name */}
                  <div>
                    <h4 className="text-base font-bold text-slate-200 group-hover:text-white transition-colors line-clamp-2 min-h-[3rem] leading-snug">
                      {proj.project_name}
                    </h4>
                  </div>

                  {/* Budget Status */}
                  <div className="pt-3.5 border-t border-slate-800/40">
                    <div className="flex flex-col space-y-0.5">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Budget</span>
                        {(() => {
                          const estCost = typeof proj.budget === 'number' 
                            ? proj.budget 
                            : (typeof proj.budget === 'object' && proj.budget !== null)
                              ? (proj.budget.total_cost || 0)
                              : parseFloat(String(proj.budget).replace(/[$,]/g, '')) || 0;
                          const targetVal = parseBudget(proj.target_budget);
                          if (targetVal !== null && estCost > targetVal) {
                            return (
                              <span className="text-[9px] font-bold text-rose-400 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-500/20 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3 text-rose-400 shrink-0" />
                                Overrun: +${(estCost - targetVal).toLocaleString()}
                              </span>
                            );
                          }
                          if (targetVal === null) {
                            return (
                              <span className="text-[9px] font-bold text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-500/20 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3 text-amber-400 shrink-0" />
                                No Target
                              </span>
                            );
                          }
                          return null;
                        })()}
                      </div>
                      <span className="text-base font-extrabold text-brand-400">
                        {typeof proj.budget === 'number' 
                          ? `$${proj.budget.toLocaleString()}` 
                          : (typeof proj.budget === 'object' && proj.budget !== null)
                            ? `$${(proj.budget.total_cost || 0).toLocaleString()}`
                            : proj.budget}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Footer Action */}
                <div className="mt-5 pt-3.5 border-t border-slate-800/40 flex justify-between items-center text-xs text-slate-400 group-hover:text-white transition-colors">
                  <span className="font-semibold text-slate-400 group-hover:text-brand-400 transition-colors">
                    Explore AI Insights
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onAssignWorkers(proj.project_name);
                      }}
                      title="Assign Workers (RAG + LLM matching)"
                      className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider text-brand-400 bg-brand-950/20 border border-brand-500/25 hover:bg-brand-950/40 transition-colors"
                    >
                      <UserPlus className="w-3 h-3" />
                      Assign
                    </button>
                    <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1.5 transition-transform text-slate-500 group-hover:text-brand-400" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
