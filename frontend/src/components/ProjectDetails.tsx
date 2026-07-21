import React, { useState } from 'react';
import { 
  Building, 
  Clock, 
  DollarSign, 
  CheckCircle2, 
  AlertCircle,
  FileText,
  Users,
  Compass,
  Layers,
  Wrench,
  HelpCircle,
  ArrowLeft,
  ChevronRight,
  PieChart as ChartIcon
} from 'lucide-react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';

interface ProjectDetailsProps {
  project: any;
  onBack: () => void;
}

export default function ProjectDetails({ project, onBack }: ProjectDetailsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'resources' | 'timeline' | 'risks'>('overview');

  if (!project) {
    return (
      <div className="p-8 text-center glass-panel max-w-md mx-auto my-12 rounded-2xl">
        <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
        <h2 className="text-lg font-bold text-white">No Project Data</h2>
        <p className="text-slate-400 text-sm mt-2">Select a project or ingest a new PDF first.</p>
        <button onClick={onBack} className="mt-4 px-4 py-2 bg-slate-800 rounded-xl text-xs font-bold text-white hover:bg-slate-700">
          Go Back
        </button>
      </div>
    );
  }

  // Formatting utils
  const formatCurrency = (val: number) => {
    return typeof val === 'number' ? `$${val.toLocaleString()}` : val;
  };

  // Budget formatting for PieChart
  const rawBreakdown = project.budget?.breakdown || project.budget || {};
  const budgetData = [
    { name: 'Development', value: rawBreakdown.development_cost || 0, color: '#38a9f8' },
    { name: 'Cloud Hosting', value: rawBreakdown.cloud_cost || 0, color: '#00c49f' },
    { name: 'Infrastructure', value: rawBreakdown.infrastructure_cost || 0, color: '#ffbb28' },
    { name: 'Testing', value: rawBreakdown.testing_cost || 0, color: '#ff8042' },
    { name: 'Support', value: rawBreakdown.support_cost || 0, color: '#a78bfa' },
    { name: 'Contingency Buffer', value: rawBreakdown.buffer_cost || 0, color: '#f43f5e' }
  ].filter(item => item.value > 0);

  // Total cost calculation
  const totalCost = project.budget?.total_cost || 
                    (typeof project.budget === 'number' ? project.budget : 0);

  // Score styling
  const score = project.overall_readiness_score || 0;
  const getScoreColor = (val: number) => {
    if (val >= 80) return 'text-emerald-400 stroke-emerald-500';
    if (val >= 60) return 'text-amber-400 stroke-amber-500';
    return 'text-rose-400 stroke-rose-500';
  };

  // Score circle calculations
  const radius = 50;
  const strokeWidth = 8;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      
      {/* Breadcrumbs & Actions */}
      <div className="flex items-center justify-between">
        <button 
          onClick={onBack}
          className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Hub
        </button>

        {project.email_metadata && (
          <div className="flex items-center gap-2 text-[10px] text-brand-400 font-semibold uppercase bg-brand-950/30 px-3.5 py-1.5 rounded-full border border-brand-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Ingested from Email: {project.email_metadata.subject}
          </div>
        )}
      </div>

      {/* Main Brand Summary Row */}
      <div className="glass-panel border-slate-800/40 p-6 rounded-3xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="space-y-2 truncate max-w-2xl">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-bold px-2.5 py-1 rounded bg-slate-800 text-slate-400 uppercase tracking-widest">
              SOW Analysis
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-brand-400 font-medium">Ready for Execution</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight truncate">
            {project.project_overview?.project_name || "Enterprise Development Plan"}
          </h1>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1.5"><Building className="w-4 h-4 text-slate-500" /> {project.project_overview?.client || "apex"}</span>
            <span>•</span>
            <span className="flex items-center gap-1.5"><Clock className="w-4 h-4 text-slate-500" /> {project.project_overview?.duration || "16 weeks"}</span>
            <span>•</span>
            <span className="flex items-center gap-1.5"><DollarSign className="w-4 h-4 text-slate-500" /> {formatCurrency(totalCost)}</span>
          </div>
        </div>

        {/* Readiness Score Gauge */}
        <div className="flex items-center gap-4 shrink-0 bg-slate-900/30 border border-slate-800/30 p-5 rounded-2xl">
          <div className="relative w-28 h-28 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90">
              {/* Back track */}
              <circle
                cx="56"
                cy="56"
                r={radius}
                className="stroke-slate-800 fill-none"
                strokeWidth={strokeWidth}
              />
              {/* Progress track */}
              <circle
                cx="56"
                cy="56"
                r={radius}
                className={`fill-none transition-all duration-1000 ${getScoreColor(score).split(' ')[1]}`}
                strokeWidth={strokeWidth}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className={`text-2xl font-extrabold tracking-tight ${getScoreColor(score).split(' ')[0]}`}>
                {score}%
              </span>
              <span className="text-[8px] text-slate-500 uppercase font-bold tracking-widest">Readiness</span>
            </div>
          </div>
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-slate-200">Confidence Score</h4>
            <p className="text-[10px] text-slate-400 leading-relaxed max-w-[150px]">
              Assessed from timeline viability, resource match, and risk mitigations.
            </p>
          </div>
        </div>
      </div>

      {/* Tabs Selection Bar */}
      <div className="flex border-b border-slate-800/80 gap-6">
        {(['overview', 'resources', 'timeline', 'risks'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3.5 text-xs font-bold uppercase tracking-wider transition-all relative ${
              activeTab === tab 
                ? 'text-brand-400' 
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {tab}
            {activeTab === tab && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-500 rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left Col: Exec Summary & Deliverables */}
            <div className="lg:col-span-8 space-y-6">
              
              {/* Summary */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <FileText className="w-5 h-5 text-brand-400" />
                  Executive Summary
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed font-light">
                  {project.executive_summary}
                </p>
              </div>

              {/* Deliverables */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-brand-400" />
                  Project Deliverables
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {project.technology_summary?.deliverables?.map((item: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/30 border border-slate-800/40 text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span className="text-slate-300 font-medium leading-normal">{item}</span>
                    </div>
                  )) || (
                    <div className="text-xs text-slate-500 italic p-2">None detected.</div>
                  )}
                </div>
              </div>

              {/* Recommendations */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Compass className="w-5 h-5 text-brand-400" />
                  Strategic Delivery Recommendations
                </h3>
                <ul className="space-y-2.5">
                  {project.recommendations?.map((rec: string, idx: number) => (
                    <li key={idx} className="flex gap-3 text-xs text-slate-300">
                      <span className="w-5 h-5 rounded bg-brand-500/10 text-brand-400 flex items-center justify-center shrink-0 text-[10px] font-bold">
                        {idx + 1}
                      </span>
                      <span className="leading-relaxed mt-0.5">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

            </div>

            {/* Right Col: Technical Stack, constraints, dependencies */}
            <div className="lg:col-span-4 space-y-6">
              
              {/* Tech Stack */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Wrench className="w-5 h-5 text-brand-400" />
                  Technology Stack
                </h3>
                <div className="flex flex-wrap gap-2">
                  {project.technology_summary?.stack?.map((tech: string, idx: number) => (
                    <span 
                      key={idx}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-950/20 text-brand-300 border border-brand-500/25"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
                <div className="border-t border-slate-800/60 pt-3 text-[11px] text-slate-400 leading-relaxed">
                  <span className="font-bold text-slate-300">Stack Strategy: </span>
                  {project.technology_summary?.recommendation}
                </div>
              </div>

              {/* Constraints & Dependencies */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-5 h-5 text-brand-400" />
                  Delivery Boundaries
                </h3>
                <div className="space-y-4.5">
                  <div>
                    <h4 className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">Technical Constraints</h4>
                    <div className="space-y-2">
                      {project.technology_summary?.constraints?.map((c: string, i: number) => (
                        <div key={i} className="text-xs text-slate-300 bg-slate-950/30 border border-slate-900 p-2.5 rounded-lg leading-relaxed">
                          • {c}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="border-t border-slate-800/50 pt-4">
                    <h4 className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">SOW Dependencies</h4>
                    <div className="space-y-2">
                      {project.technology_summary?.dependencies?.map((d: string, i: number) => (
                        <div key={i} className="text-xs text-slate-300 bg-slate-950/30 border border-slate-900 p-2.5 rounded-lg leading-relaxed">
                          • {d}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

            </div>

          </div>
        )}

        {/* Resources & Budget Tab */}
        {activeTab === 'resources' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left Col: Resource Allocation Table */}
            <div className="lg:col-span-7 space-y-6">
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
                <div className="mb-6">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Users className="w-5 h-5 text-brand-400" />
                    Recommended Team Roster
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">{project.resource_plan?.team_summary}</p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-500 font-bold">
                        <th className="pb-3 w-1/3">ROLE</th>
                        <th className="pb-3 text-center">HEADCOUNT</th>
                        <th className="pb-3 pl-4">KEY RESPONSIBILITY</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50 text-slate-300">
                      {project.resource_plan?.recommended_team?.map((member: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-900/10">
                          <td className="py-3.5 font-semibold text-slate-200">{member.role}</td>
                          <td className="py-3.5 text-center font-bold text-brand-400">{member.count}</td>
                          <td className="py-3.5 pl-4 text-slate-400 leading-normal">{member.key_responsibility}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-5 border-t border-slate-800 pt-4 flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">Core Dedicated Team Size</span>
                  <span className="px-3.5 py-1 rounded bg-brand-900/30 text-brand-300 font-extrabold border border-brand-500/20">
                    {project.resource_plan?.total_resources} Members
                  </span>
                </div>
              </div>
            </div>

            {/* Right Col: Budget PieChart breakdown */}
            <div className="lg:col-span-5 space-y-6">
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl flex flex-col justify-between h-full">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <ChartIcon className="w-5 h-5 text-brand-400" />
                    Budget Distribution
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">Cost items allocated to support complete delivery.</p>
                </div>

                <div className="h-[240px] w-full my-4">
                  {budgetData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={budgetData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {budgetData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ background: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                          formatter={(v) => [`$${Number(v).toLocaleString()}`, 'Allocated']}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-slate-500 text-xs italic">
                      No budget breakdown items available
                    </div>
                  )}
                </div>

                {/* Legend/list items */}
                <div className="grid grid-cols-2 gap-2 text-xs border-t border-slate-800 pt-4">
                  {budgetData.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2.5">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: item.color }}></span>
                      <span className="text-slate-400 truncate">{item.name}:</span>
                      <span className="font-bold text-slate-200 ml-auto shrink-0">${item.value.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

          </div>
        )}

        {/* Timeline Tab */}
        {activeTab === 'timeline' && (
          <div className="space-y-6">
            
            {/* Timeline Phases flow */}
            <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-6">
                <Clock className="w-5 h-5 text-brand-400" />
                Project Phases Schedule
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {project.timeline?.phases?.map((phase: any, idx: number) => (
                  <div 
                    key={idx} 
                    className="relative glass-panel bg-slate-900/20 border-slate-800/80 p-5 rounded-xl space-y-3 hover:border-brand-500/30 transition-all group"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-bold bg-brand-900/30 text-brand-400 border border-brand-500/20 px-2 py-0.5 rounded">
                        WEEK {phase.start_week} - {phase.end_week}
                      </span>
                      <span className="text-slate-600 font-extrabold group-hover:text-brand-500 transition-colors text-lg font-sans">
                        0{idx + 1}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-200">{phase.phase_name}</h4>
                      <p className="text-[10px] text-slate-400 mt-1.5 leading-relaxed">{phase.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Sprints list */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Sprint details */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-5">
                  <CheckCircle2 className="w-5 h-5 text-brand-400" />
                  Sprint Plan (2-Week Iterations)
                </h3>
                <div className="space-y-4 overflow-y-auto max-h-[350px] pr-2">
                  {project.timeline?.sprint_planning?.map((sprint: any, idx: number) => (
                    <div key={idx} className="bg-slate-900/30 border border-slate-800/50 p-4 rounded-xl space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-brand-300">Sprint {sprint.sprint_number}</span>
                        <span className="text-[10px] text-slate-500 font-semibold">{sprint.duration_weeks} Weeks</span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-200">{sprint.goal}</h4>
                      <div className="flex flex-wrap gap-1.5 pt-1.5">
                        {sprint.tasks?.map((task: string, i: number) => (
                          <span key={i} className="text-[9px] px-2 py-1 rounded bg-slate-950 text-slate-400 font-medium border border-slate-800">
                            {task}
                          </span>
                        ))}
                      </div>
                    </div>
                  )) || (
                    <div className="text-xs text-slate-500 italic">No sprint configurations found in timeline file.</div>
                  )}
                </div>
              </div>

              {/* Week-wise activities */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-5">
                  <Layers className="w-5 h-5 text-brand-400" />
                  Week-by-Week Breakdown
                </h3>
                <div className="space-y-3.5 overflow-y-auto max-h-[350px] pr-2">
                  {project.timeline?.week_wise_planning?.map((week: any, idx: number) => (
                    <div key={idx} className="flex gap-4 border-l border-slate-800/80 pl-6 pb-4 last:pb-0 relative">
                      {/* Timeline dot */}
                      <span className="absolute -left-1.5 top-1 w-3 h-3 rounded-full bg-brand-500 border border-slate-950"></span>
                      
                      <div className="space-y-1 text-xs">
                        <div className="font-extrabold text-brand-400">{week.week}</div>
                        <p className="text-slate-300 text-[11px] font-medium">Activities:</p>
                        <ul className="list-disc pl-4 text-[10px] text-slate-400 space-y-1">
                          {week.activities?.map((a: string, i: number) => (
                            <li key={i}>{a}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )) || (
                    <div className="text-xs text-slate-500 italic">No weekly planning items available.</div>
                  )}
                </div>
              </div>

            </div>
          </div>
        )}

        {/* Risks Tab */}
        {activeTab === 'risks' && (
          <div className="space-y-6">
            
            {/* Header info */}
            <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-2">
                <AlertCircle className="w-5 h-5 text-brand-400" />
                Delivery Risk Matrix
              </h3>
              <p className="text-xs text-slate-400">Predicted failure vectors and proposed mitigation procedures.</p>

              {/* Risks Cards list */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                {project.risks?.map((risk: any, idx: number) => {
                  
                  const isHigh = risk.severity?.toLowerCase() === 'high';
                  const isMed = risk.severity?.toLowerCase() === 'medium';
                  
                  return (
                    <div 
                      key={idx}
                      className={`glass-panel border p-5 rounded-xl space-y-4 flex flex-col justify-between transition-all ${
                        isHigh 
                          ? 'border-rose-500/25 bg-rose-950/5 hover:border-rose-500/40' 
                          : isMed 
                            ? 'border-amber-500/25 bg-amber-950/5 hover:border-amber-500/40' 
                            : 'border-slate-800/80 bg-slate-900/10 hover:border-slate-800'
                      }`}
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold text-slate-400 tracking-wider uppercase">
                            {risk.category}
                          </span>
                          
                          <div className="flex gap-2">
                            {/* Probability */}
                            <span className="text-[9px] px-2 py-0.5 rounded-full bg-slate-800 font-bold uppercase tracking-wider text-slate-400">
                              P: {risk.probability}
                            </span>
                            {/* Severity badge */}
                            <span className={`text-[9px] px-2 py-0.5 rounded-full font-extrabold uppercase tracking-wider ${
                              isHigh 
                                ? 'bg-rose-500/15 text-rose-400 border border-rose-500/20' 
                                : isMed 
                                  ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' 
                                  : 'bg-blue-500/15 text-blue-400 border border-blue-500/20'
                            }`}>
                              S: {risk.severity}
                            </span>
                          </div>
                        </div>

                        <h4 className="text-xs font-bold text-slate-200">{risk.risk_name}</h4>
                      </div>

                      {/* Mitigation */}
                      <div className="bg-slate-950/40 border border-slate-900 p-3 rounded-lg text-[10px] leading-relaxed">
                        <span className="font-bold text-brand-400 uppercase tracking-widest block mb-1">Proposed Mitigation</span>
                        <p className="text-slate-400 font-medium">{risk.mitigation}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}
      </div>

    </div>
  );
}
