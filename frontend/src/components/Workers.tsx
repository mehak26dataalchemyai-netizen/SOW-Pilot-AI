import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  DollarSign,
  Award,
  Plus,
  Loader2,
  Sparkles,
  Target
} from 'lucide-react';

interface WorkerMatch {
  worker_id: string;
  score: number;
  reasons: string[];
}

export default function Workers() {
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [showAddForm, setShowAddForm] = useState<boolean>(false);
  const [newName, setNewName] = useState<string>('');
  const [newRole, setNewRole] = useState<string>('Developer');
  const [newRate, setNewRate] = useState<string>('100');
  const [newSkills, setNewSkills] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  // Assign-to-project flow state
  const [preselectedProject, setPreselectedProject] = useState<string | null>(null);
  const [taskInput, setTaskInput] = useState<string>('');
  const [matching, setMatching] = useState<boolean>(false);
  const [matchError, setMatchError] = useState<string | null>(null);
  const [matches, setMatches] = useState<WorkerMatch[] | null>(null);
  const [assigningId, setAssigningId] = useState<string | null>(null);
  const [assignedIds, setAssignedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchWorkers();
    const pending = localStorage.getItem('sowpilot_preselected_project');
    if (pending) {
      setPreselectedProject(pending);
    }
  }, []);

  const dismissAssignPanel = () => {
    localStorage.removeItem('sowpilot_preselected_project');
    setPreselectedProject(null);
    setTaskInput('');
    setMatches(null);
    setMatchError(null);
  };

  const handleFindMatches = async () => {
    if (!taskInput.trim()) return;
    setMatching(true);
    setMatchError(null);
    setMatches(null);
    try {
      const res = await fetch('/api/match-workers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: taskInput.trim(), workers })
      });
      if (!res.ok) throw new Error('Matching request failed.');
      const data = await res.json();
      const sorted = (data.matches || [])
        .filter((m: WorkerMatch) => m.score > 0)
        .sort((a: WorkerMatch, b: WorkerMatch) => b.score - a.score)
        .slice(0, 5);
      setMatches(sorted);
    } catch (err: any) {
      console.error(err);
      setMatchError(err.message || 'Failed to find matching workers.');
    } finally {
      setMatching(false);
    }
  };

  const handleAssign = async (workerId: string) => {
    if (!preselectedProject) return;
    setAssigningId(workerId);
    try {
      const res = await fetch('/api/assign-worker', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_name: preselectedProject, task: taskInput.trim(), worker_id: workerId })
      });
      if (!res.ok) throw new Error('Assignment failed.');
      setAssignedIds(prev => new Set(prev).add(workerId));
      fetchWorkers();
    } catch (err: any) {
      console.error(err);
      alert(err.message || 'Failed to assign worker.');
    } finally {
      setAssigningId(null);
    }
  };

  const fetchWorkers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/workers');
      if (res.ok) {
        const data = await res.json();
        setWorkers(data);
      } else {
        throw new Error("Failed to load worker profiles.");
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to retrieve worker profiles. Make sure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleAddWorker = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setActionLoading(true);
    
    const parsedSkills = newSkills
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    const newWorker = {
      id: `w_${Date.now()}`,
      name: newName.trim(),
      role: newRole,
      billing_rate: parseFloat(newRate) || 100.0,
      skills: parsedSkills,
      status: 'Available',
      assignments: []
    };

    try {
      const res = await fetch('/api/workers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newWorker)
      });
      if (res.ok) {
        setNewName('');
        setNewSkills('');
        setNewRate('100');
        setShowAddForm(false);
        fetchWorkers();
      } else {
        alert("Failed to insert worker record.");
      }
    } catch (err) {
      console.error(err);
      alert("Error adding worker.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteWorker = async (wId: string) => {
    if (!confirm("Are you sure you want to remove this employee profile from the directory?")) return;
    try {
      const res = await fetch(`/api/workers/${wId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchWorkers();
      } else {
        alert("Failed to remove worker.");
      }
    } catch (err) {
      console.error(err);
      alert("Error deleting worker.");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      
      {/* Header Row */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <Users className="w-8 h-8 text-brand-500" />
            Personnel Directory
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Enterprise database directory holding developer skills, availability, and billing rates.
          </p>
        </div>

        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-xs font-bold rounded-xl shadow-lg shadow-brand-500/10 active:scale-95 transition-all"
        >
          {showAddForm ? <XCircle className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
          {showAddForm ? 'Cancel' : 'Add Employee Profile'}
        </button>
      </div>

      {/* Assign Tasks to Workers Panel (RAG retrieval + LLM reranking) */}
      {preselectedProject && (
        <div className="glass-panel border-brand-500/20 p-6 rounded-2xl space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Target className="w-4.5 h-4.5 text-brand-400" />
                Assign Workers — {preselectedProject}
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Describe the task. We retrieve the closest-matching candidates by skill/role similarity, then an LLM reranks and explains the top fits.
              </p>
            </div>
            <button
              onClick={dismissAssignPanel}
              className="p-1.5 hover:bg-slate-800 text-slate-500 hover:text-white rounded-lg transition-colors shrink-0"
              title="Dismiss"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-col md:flex-row gap-3">
            <textarea
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              placeholder="e.g. Build the React dashboard with SSE-driven live progress updates"
              rows={2}
              className="flex-1 bg-slate-900 border border-slate-800 text-slate-200 outline-none focus:border-brand-500 p-3 rounded-xl transition-all text-xs resize-none"
            />
            <button
              onClick={handleFindMatches}
              disabled={matching || !taskInput.trim()}
              className="flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-xs font-bold rounded-xl transition-all active:scale-95 disabled:opacity-50 shrink-0"
            >
              {matching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Find Best Match
            </button>
          </div>

          {matchError && (
            <p className="text-xs text-rose-400 font-semibold">{matchError}</p>
          )}

          {matches && (
            <div className="space-y-2.5">
              {matches.length === 0 ? (
                <p className="text-xs text-slate-500">No candidates matched this task.</p>
              ) : (
                matches.map((m) => {
                  const w = workers.find((x) => x.id === m.worker_id);
                  if (!w) return null;
                  const isAssigned = assignedIds.has(m.worker_id);
                  return (
                    <div key={m.worker_id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/60">
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-extrabold text-slate-200 text-[13px]">{w.name}</span>
                          <span className="text-[10px] text-slate-500">{w.role}</span>
                          <span className="text-[9px] font-bold uppercase tracking-wider text-brand-400 bg-brand-950/20 border border-brand-500/25 px-2 py-0.5 rounded">
                            Match {m.score}%
                          </span>
                        </div>
                        {m.reasons?.length > 0 && (
                          <p className="text-[11px] text-slate-400 leading-relaxed">{m.reasons.join(' · ')}</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleAssign(m.worker_id)}
                        disabled={assigningId === m.worker_id || isAssigned}
                        className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all active:scale-95 disabled:opacity-60 shrink-0 bg-emerald-600 hover:bg-emerald-500 text-white"
                      >
                        {assigningId === m.worker_id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : isAssigned ? (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        ) : null}
                        {isAssigned ? 'Assigned' : 'Assign to Project'}
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      )}

      {/* Add Worker Form Slide Down */}
      {showAddForm && (
        <div className="glass-panel border-slate-800/40 p-6 rounded-2xl max-w-2xl animate-slideDown">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
            <UserPlus className="w-4.5 h-4.5 text-brand-400" />
            Create Worker Profile
          </h3>

          <form onSubmit={handleAddWorker} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-slate-400 font-semibold block">Full Name</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Sarah Connor"
                  className="w-full bg-slate-900 border border-slate-800 text-slate-200 outline-none focus:border-brand-500 p-2.5 rounded-xl transition-all"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold block">Role Category</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 text-slate-200 outline-none focus:border-brand-500 p-2.5 rounded-xl transition-all"
                >
                  <option value="Project Manager">Project Manager</option>
                  <option value="Lead Frontend Developer">Lead Frontend Developer</option>
                  <option value="Lead Backend / AI Engineer">Lead Backend / AI Engineer</option>
                  <option value="Full Stack Developer">Full Stack Developer</option>
                  <option value="DevOps Engineer">DevOps Engineer</option>
                  <option value="QA Automation Engineer">QA Automation Engineer</option>
                  <option value="UX/UI Designer">UX/UI Designer</option>
                  <option value="Security Analyst">Security Analyst</option>
                  <option value="Financial Analyst">Financial Analyst</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-slate-400 font-semibold block">Hourly Billing Rate (USD/hr)</label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-slate-500">$</span>
                  <input
                    type="number"
                    required
                    min="10"
                    max="500"
                    value={newRate}
                    onChange={(e) => setNewRate(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 text-slate-200 outline-none focus:border-brand-500 pl-7 pr-3 p-2.5 rounded-xl transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold block">Key Skillsets (Comma separated)</label>
                <input
                  type="text"
                  value={newSkills}
                  onChange={(e) => setNewSkills(e.target.value)}
                  placeholder="React 18, TypeScript, APIs..."
                  className="w-full bg-slate-900 border border-slate-800 text-slate-200 outline-none focus:border-brand-500 p-2.5 rounded-xl transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={actionLoading}
              className="px-5 py-2.5 bg-gradient-to-r from-brand-600 to-brand-500 text-white font-bold rounded-xl transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2"
            >
              {actionLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              Save Profile to DB
            </button>
          </form>
        </div>
      )}

      {/* Main Content Area */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-500">
          <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
          <span className="text-xs font-semibold animate-pulse">Loading employee database profiles...</span>
        </div>
      ) : error ? (
        <div className="glass-panel border-rose-500/20 bg-rose-950/5 p-6 rounded-2xl max-w-lg mx-auto text-center space-y-3">
          <AlertCircle className="w-12 h-12 text-rose-400 mx-auto" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Connection Failure</h3>
          <p className="text-xs text-slate-400 leading-relaxed font-light">{error}</p>
          <button 
            onClick={fetchWorkers}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-[10px] font-bold tracking-wider uppercase"
          >
            Retry Connection
          </button>
        </div>
      ) : workers.length === 0 ? (
        <div className="text-center py-20 glass-panel border-slate-800/40 rounded-2xl">
          <Users className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-400">Empty Directory</h3>
          <p className="text-xs text-slate-500 font-light mt-1">No employee records currently seeded in the database.</p>
        </div>
      ) : (
        <div className="glass-panel border-slate-800/40 rounded-3xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-900/50 border-b border-slate-850 text-slate-400 font-bold uppercase tracking-wider">
                  <th className="p-4 pl-6">Name</th>
                  <th className="p-4">Role</th>
                  <th className="p-4">Billing Rate</th>
                  <th className="p-4">Key Skills</th>
                  <th className="p-4">Availability</th>
                  <th className="p-4 pr-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850 text-slate-300 font-light">
                {workers.map((worker) => {
                  const isAvailable = worker.status === 'Available';
                  const isPremiumRate = worker.billing_rate > 130;
                  
                  return (
                    <tr key={worker.id} className="hover:bg-slate-900/20 transition-colors">
                      <td className="p-4 pl-6">
                        <span className="font-extrabold text-slate-200 block text-[13px]">{worker.name}</span>
                        <span className="text-[10px] text-slate-500 font-mono block mt-0.5">{worker.id}</span>
                      </td>
                      <td className="p-4">
                        <span className="font-medium text-slate-300">{worker.role}</span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-1">
                          <DollarSign className="w-3.5 h-3.5 text-slate-500" />
                          <span className={`font-bold ${isPremiumRate ? 'text-amber-400' : 'text-slate-200'}`}>
                            {worker.billing_rate}/hr
                          </span>
                          {isPremiumRate && (
                            <span className="text-[8px] font-bold uppercase tracking-widest text-amber-500 bg-amber-950/20 px-1.5 py-0.5 rounded border border-amber-500/25 scale-90 ml-1">
                              Premium
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1 max-w-sm">
                          {worker.skills?.map((skill: string, idx: number) => (
                            <span 
                              key={idx}
                              className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 scale-95 origin-left"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-4">
                        <span className={`px-2.5 py-1 rounded-full font-bold uppercase tracking-widest text-[9px] border inline-flex items-center gap-1 ${
                          isAvailable 
                            ? 'bg-emerald-950/20 text-emerald-400 border-emerald-500/20' 
                            : 'bg-indigo-950/20 text-indigo-400 border-indigo-500/20'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${isAvailable ? 'bg-emerald-400' : 'bg-indigo-400'}`} />
                          {worker.status}
                        </span>
                      </td>
                      <td className="p-4 pr-6 text-right">
                        <button
                          onClick={() => handleDeleteWorker(worker.id)}
                          className="p-2 hover:bg-rose-500/10 text-slate-500 hover:text-rose-400 rounded-xl transition-colors inline-block"
                          title="Delete Employee Profile"
                        >
                          <Trash2 className="w-4.5 h-4.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}
