import { useEffect, useState } from 'react';
import { TrendingUp, AlertTriangle, Trophy, Clock, Users, Loader2 } from 'lucide-react';

interface PipelineProject {
  project_name: string;
  client: string;
  stage: string;
  bid_price: number;
  days_idle: number | null;
  is_stale: boolean;
  qualification_decision: string;
}

interface ResourceConflict {
  worker_id: string;
  worker_name: string;
  role: string;
  projects: string[];
}

interface PipelineData {
  projects: PipelineProject[];
  summary: {
    total_projects: number;
    total_pipeline_value: number;
    won: number;
    lost: number;
    win_rate_percent: number | null;
    stale_count: number;
  };
  resource_conflicts: ResourceConflict[];
}

function stageColor(stage: string): string {
  if (stage === 'Won') return 'text-emerald-400 bg-emerald-950/30 border-emerald-500/30';
  if (stage === 'Lost' || stage === 'No-Go' || stage.includes('Rejected')) return 'text-rose-400 bg-rose-950/30 border-rose-500/30';
  if (stage === 'Contract Signed') return 'text-brand-400 bg-brand-950/30 border-brand-500/30';
  if (stage === 'Pending Approvals') return 'text-amber-400 bg-amber-950/30 border-amber-500/30';
  return 'text-slate-300 bg-slate-800/40 border-slate-700/40';
}

export default function Pipeline({ onSelectProject }: { onSelectProject: (name: string) => void }) {
  const [data, setData] = useState<PipelineData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/pipeline')
      .then((r) => r.json())
      .then((d) => setData(d))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-64 text-slate-400 gap-2">
        <Loader2 className="w-5 h-5 animate-spin" /> Loading portfolio pipeline...
      </div>
    );
  }

  if (!data) {
    return <div className="p-8 text-slate-400">Could not load pipeline data.</div>;
  }

  const { summary, projects, resource_conflicts } = data;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Pipeline</h1>
        <p className="text-slate-400 text-sm mt-1">Every bid in one view — stage, how long it's been idle, and what's stuck.</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-5">
        <div className="glass-panel border-slate-800/40 p-5 rounded-2xl">
          <div className="flex items-center gap-2 text-slate-400 text-[10px] font-bold uppercase tracking-wider">
            <TrendingUp className="w-3.5 h-3.5" /> Pipeline Value
          </div>
          <div className="text-2xl font-extrabold text-white mt-2">
            ${summary.total_pipeline_value >= 1000000
              ? (summary.total_pipeline_value / 1000000).toFixed(1) + 'M'
              : (summary.total_pipeline_value / 1000).toFixed(0) + 'k'}
          </div>
        </div>
        <div className="glass-panel border-slate-800/40 p-5 rounded-2xl">
          <div className="flex items-center gap-2 text-slate-400 text-[10px] font-bold uppercase tracking-wider">
            <Trophy className="w-3.5 h-3.5" /> Win Rate
          </div>
          <div className="text-2xl font-extrabold text-white mt-2">
            {summary.win_rate_percent !== null ? `${summary.win_rate_percent}%` : '—'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">{summary.won} won / {summary.lost} lost</div>
        </div>
        <div className="glass-panel border-slate-800/40 p-5 rounded-2xl">
          <div className="flex items-center gap-2 text-slate-400 text-[10px] font-bold uppercase tracking-wider">
            <Clock className="w-3.5 h-3.5" /> Stale / Stuck
          </div>
          <div className={`text-2xl font-extrabold mt-2 ${summary.stale_count > 0 ? 'text-amber-400' : 'text-white'}`}>
            {summary.stale_count}
          </div>
        </div>
        <div className="glass-panel border-slate-800/40 p-5 rounded-2xl">
          <div className="flex items-center gap-2 text-slate-400 text-[10px] font-bold uppercase tracking-wider">
            <Users className="w-3.5 h-3.5" /> Resource Conflicts
          </div>
          <div className={`text-2xl font-extrabold mt-2 ${resource_conflicts.length > 0 ? 'text-rose-400' : 'text-white'}`}>
            {resource_conflicts.length}
          </div>
        </div>
      </div>

      {/* Resource conflicts panel */}
      {resource_conflicts.length > 0 && (
        <div className="glass-panel border-rose-500/20 bg-rose-950/10 p-6 rounded-2xl space-y-3">
          <h3 className="text-sm font-bold text-rose-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Workers committed to more than one active project
          </h3>
          <div className="space-y-2">
            {resource_conflicts.map((c) => (
              <div key={c.worker_id} className="flex items-center justify-between text-sm bg-slate-950/40 border border-slate-800/40 rounded-xl px-4 py-2.5">
                <div>
                  <span className="font-semibold text-white">{c.worker_name}</span>
                  <span className="text-slate-500 text-xs ml-2">{c.role}</span>
                </div>
                <div className="text-xs text-slate-400 text-right">{c.projects.join(' · ')}</div>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-slate-500">
            Flags a worker already assigned on another not-yet-closed project — not calendar-level week
            overlap, since projects don't share absolute dates yet. Treat this as "double check before relying on them here."
          </p>
        </div>
      )}

      {/* Projects table */}
      <div className="glass-panel border-slate-800/40 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-800/50">
              <th className="px-5 py-3">Project</th>
              <th className="px-5 py-3">Client</th>
              <th className="px-5 py-3">Stage</th>
              <th className="px-5 py-3">Value</th>
              <th className="px-5 py-3">Idle</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr
                key={p.project_name}
                onClick={() => onSelectProject(p.project_name)}
                className="border-b border-slate-800/30 hover:bg-slate-900/40 cursor-pointer transition-colors"
              >
                <td className="px-5 py-3 text-white font-medium max-w-[280px] truncate" title={p.project_name}>{p.project_name}</td>
                <td className="px-5 py-3 text-slate-400">{p.client}</td>
                <td className="px-5 py-3">
                  <span className={`text-[10px] font-bold px-2 py-1 rounded-md border ${stageColor(p.stage)}`}>
                    {p.stage}
                  </span>
                </td>
                <td className="px-5 py-3 text-brand-400 font-semibold">
                  {p.bid_price ? `$${Number(p.bid_price).toLocaleString()}` : '—'}
                </td>
                <td className="px-5 py-3">
                  {p.days_idle !== null ? (
                    <span className={`text-xs font-semibold flex items-center gap-1 ${p.is_stale ? 'text-amber-400' : 'text-slate-500'}`}>
                      {p.is_stale && <AlertTriangle className="w-3 h-3" />}
                      {p.days_idle}d
                    </span>
                  ) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
