import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  Trash2, 
  Plus, 
  Briefcase, 
  CheckCircle2, 
  FolderGit2, 
  Activity, 
  Check, 
  AlertCircle,
  FileText,
  X
} from 'lucide-react';

interface TaskAssignment {
  projectName: string;
  task: string;
}

interface Worker {
  id: string;
  name: string;
  role: string;
  skills: string[];
  status: 'Available' | 'Assigned';
  assignments: TaskAssignment[];
}

const DEFAULT_WORKERS: Worker[] = [
  {
    id: 'w1',
    name: 'Sarah Connor',
    role: 'Project Manager',
    skills: ['Timeline Planning', 'Risk Management', 'Stakeholder Communication'],
    status: 'Available',
    assignments: []
  },
  {
    id: 'w2',
    name: 'John Doe',
    role: 'Lead Frontend Developer',
    skills: ['React 18', 'TypeScript', 'Tailwind CSS', 'Recharts'],
    status: 'Available',
    assignments: []
  },
  {
    id: 'w3',
    name: 'Alice Smith',
    role: 'Lead Backend / AI Engineer',
    skills: ['Python 3.11', 'FastAPI', 'LangGraph', 'Gemini AI Integration'],
    status: 'Available',
    assignments: []
  },
  {
    id: 'w4',
    name: 'Bob Johnson',
    role: 'DevOps Engineer',
    skills: ['AWS ECS / Fargate', 'Docker', 'VPC Networking', 'GitHub Actions'],
    status: 'Available',
    assignments: []
  },
  {
    id: 'w5',
    name: 'Emma Watson',
    role: 'QA Automation Engineer',
    skills: ['Playwright', 'API Integration Testing', 'SOC 2 Auditing', 'Jest'],
    status: 'Available',
    assignments: []
  }
];

const STANDARD_ROLES = [
  'Project Manager',
  'Lead Frontend Developer',
  'Lead Backend / AI Engineer',
  'DevOps Engineer',
  'QA Automation Engineer',
  'UX/UI Designer',
  'Database Administrator',
  'Business Analyst'
];

interface WorkersProps {
  theme?: 'dark' | 'light';
}

export default function Workers({ theme = 'dark' }: WorkersProps) {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loadingProjects, setLoadingProjects] = useState<boolean>(true);
  
  // Add Worker Form state
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState(STANDARD_ROLES[0]);
  const [customRole, setCustomRole] = useState('');
  const [newSkills, setNewSkills] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);

  // Assign Task state
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [selectedTask, setSelectedTask] = useState('');
  const [selectedWorkerId, setSelectedWorkerId] = useState('');
  const [customTask, setCustomTask] = useState('');
  const [useCustomTask, setUseCustomTask] = useState(false);
  const [assignmentMessage, setAssignmentMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Load workers and projects
  useEffect(() => {
    // Load workers from localStorage or defaults
    const savedWorkers = localStorage.getItem('sowpilot_workers');
    if (savedWorkers) {
      try {
        setWorkers(JSON.parse(savedWorkers));
      } catch (e) {
        setWorkers(DEFAULT_WORKERS);
      }
    } else {
      setWorkers(DEFAULT_WORKERS);
    }

    // Fetch projects
    const fetchProjects = async () => {
      try {
        const res = await fetch('/api/projects');
        if (res.ok) {
          const data = await res.json();
          setProjects(data);
          if (data.length > 0) {
            setSelectedProjectId(data[0].project_overview?.project_name || data[0].project_name || '');
          }
        }
      } catch (err) {
        console.error('Error fetching projects for workers:', err);
      } finally {
        setLoadingProjects(false);
      }
    };
    fetchProjects();
  }, []);

  // Save workers helper
  const saveWorkers = (updatedWorkers: Worker[]) => {
    setWorkers(updatedWorkers);
    localStorage.setItem('sowpilot_workers', JSON.stringify(updatedWorkers));
  };

  // Add a new worker
  const handleAddWorker = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    const finalRole = newRole === 'Other' ? (customRole.trim() || 'Staff Consultant') : newRole;
    const skillsArray = newSkills
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    const newWorker: Worker = {
      id: 'w_' + Date.now(),
      name: newName.trim(),
      role: finalRole,
      skills: skillsArray.length > 0 ? skillsArray : ['General Consulting'],
      status: 'Available',
      assignments: []
    };

    const updated = [...workers, newWorker];
    saveWorkers(updated);

    // Reset Form
    setNewName('');
    setNewSkills('');
    setCustomRole('');
    setShowAddForm(false);
  };

  // Delete a worker
  const handleDeleteWorker = (id: string) => {
    const updated = workers.filter(w => w.id !== id);
    saveWorkers(updated);
  };

  // Assign task
  const handleAssignTask = (e: React.FormEvent) => {
    e.preventDefault();
    
    const worker = workers.find(w => w.id === selectedWorkerId);
    if (!worker) {
      setAssignmentMessage({ text: 'Please select a worker.', type: 'error' });
      return;
    }

    const taskToAssign = useCustomTask ? customTask.trim() : selectedTask;
    if (!taskToAssign) {
      setAssignmentMessage({ text: 'Please specify a task to assign.', type: 'error' });
      return;
    }

    if (!selectedProjectId) {
      setAssignmentMessage({ text: 'Please select a project.', type: 'error' });
      return;
    }

    // Check if task already assigned to this worker
    const alreadyAssigned = worker.assignments.some(
      a => a.projectName === selectedProjectId && a.task === taskToAssign
    );

    if (alreadyAssigned) {
      setAssignmentMessage({ text: `${worker.name} is already assigned to this task.`, type: 'error' });
      return;
    }

    const updated = workers.map(w => {
      if (w.id === selectedWorkerId) {
        const nextAssignments = [...w.assignments, { projectName: selectedProjectId, task: taskToAssign }];
        return {
          ...w,
          status: 'Assigned' as const,
          assignments: nextAssignments
        };
      }
      return w;
    });

    saveWorkers(updated);
    setAssignmentMessage({ text: `Successfully assigned "${taskToAssign}" to ${worker.name}!`, type: 'success' });
    setCustomTask('');
    
    // Clear message after 3 seconds
    setTimeout(() => {
      setAssignmentMessage(null);
    }, 3500);
  };

  // Remove assignment
  const handleRemoveAssignment = (workerId: string, idx: number) => {
    const updated = workers.map(w => {
      if (w.id === workerId) {
        const nextAssignments = w.assignments.filter((_, i) => i !== idx);
        return {
          ...w,
          status: (nextAssignments.length > 0 ? 'Assigned' : 'Available') as 'Available' | 'Assigned',
          assignments: nextAssignments
        };
      }
      return w;
    });
    saveWorkers(updated);
  };

  // Get project tasks dynamically based on selected project id
  const getTasksForSelectedProject = () => {
    const selectedProj = projects.find(
      p => (p.project_overview?.project_name || p.project_name) === selectedProjectId
    );
    if (!selectedProj) return [];

    const tasks: string[] = [];
    
    // 1. Get from technology_summary deliverables (which are direct SOW requirements!)
    if (selectedProj.technology_summary?.deliverables) {
      selectedProj.technology_summary.deliverables.forEach((d: string) => {
        if (!tasks.includes(d)) tasks.push(d);
      });
    }

    // 2. Get from technology_summary stack
    if (selectedProj.technology_summary?.stack) {
      selectedProj.technology_summary.stack.forEach((s: string) => {
        const taskText = `Implement and configure ${s}`;
        if (!tasks.includes(taskText)) tasks.push(taskText);
      });
    }

    // 3. Get from sprint planning
    if (selectedProj.timeline?.sprint_planning) {
      selectedProj.timeline.sprint_planning.forEach((sprint: any) => {
        if (sprint.tasks) {
          sprint.tasks.forEach((t: string) => {
            if (!tasks.includes(t)) tasks.push(t);
          });
        }
      });
    }

    // 4. Get from timeline phases
    if (selectedProj.timeline?.phases) {
      selectedProj.timeline.phases.forEach((phase: any) => {
        const taskText = `Deliver phase: ${phase.phase_name}`;
        if (!tasks.includes(taskText)) tasks.push(taskText);
      });
    }

    // 5. Fallback: milestones
    if (selectedProj.timeline?.milestones) {
      selectedProj.timeline.milestones.forEach((m: any) => {
        if (m.name && !tasks.includes(m.name)) tasks.push(m.name);
      });
    }

    return tasks;
  };

  // Update selected task when project changes
  useEffect(() => {
    const tasks = getTasksForSelectedProject();
    if (tasks.length > 0) {
      setSelectedTask(tasks[0]);
    } else {
      setSelectedTask('');
    }
  }, [selectedProjectId, projects]);

  const tasksAvailable = getTasksForSelectedProject();

  // Helper to calculate candidate match score
  const getSkillMatchScore = (worker: Worker, taskText: string): { score: number; reasons: string[] } => {
    const text = taskText.toLowerCase();
    let score = 0;
    const reasons: string[] = [];

    if (!text.trim()) return { score: 0, reasons: [] };

    // 1. Role-based matching
    const role = worker.role.toLowerCase();
    if (text.includes('frontend') || text.includes('ui') || text.includes('ux') || text.includes('dashboard') || text.includes('react') || text.includes('visual') || text.includes('chart') || text.includes('page') || text.includes('html') || text.includes('css')) {
      if (role.includes('frontend') || role.includes('designer') || role.includes('ux') || role.includes('ui')) {
        score += 50;
        reasons.push('Role matches frontend/design requirements');
      }
    }
    if (text.includes('backend') || text.includes('fastapi') || text.includes('python') || text.includes('langgraph') || text.includes('api') || text.includes('sse') || text.includes('server') || text.includes('database') || text.includes('sql') || text.includes('postgres')) {
      if (role.includes('backend') || role.includes('ai') || role.includes('engineer') || role.includes('database') || role.includes('administrator')) {
        score += 50;
        reasons.push('Role matches backend/AI engineering/DB requirements');
      }
    }
    if (text.includes('devops') || text.includes('deployment') || text.includes('aws') || text.includes('docker') || text.includes('vpc') || text.includes('cloud') || text.includes('hosting') || text.includes('scripts') || text.includes('launch')) {
      if (role.includes('devops') || role.includes('cloud')) {
        score += 50;
        reasons.push('Role matches DevOps/cloud hosting requirements');
      }
    }
    if (text.includes('test') || text.includes('qa') || text.includes('automation') || text.includes('audit') || text.includes('soc 2') || text.includes('compliance') || text.includes('verification')) {
      if (role.includes('qa') || role.includes('testing') || role.includes('security') || role.includes('compliance')) {
        score += 50;
        reasons.push('Role matches QA/security/compliance requirements');
      }
    }
    if (text.includes('project') || text.includes('manage') || text.includes('timeline') || text.includes('sprint') || text.includes('kickoff') || text.includes('plan') || text.includes('document') || text.includes('analyst') || text.includes('client')) {
      if (role.includes('manager') || role.includes('analyst') || role.includes('ba')) {
        score += 50;
        reasons.push('Role matches management/business analysis requirements');
      }
    }

    // 2. Skill-based matching
    worker.skills.forEach(skill => {
      const s = skill.toLowerCase();
      // Check direct word match or substring
      if (text.includes(s) || s.includes(text)) {
        score += 30;
        reasons.push(`Skill match: ${skill}`);
      } else {
        // Check partial matches
        const skillWords = s.split(/\s+/);
        const matchedWords = skillWords.filter(word => word.length > 2 && text.includes(word));
        if (matchedWords.length > 0) {
          score += 20 * matchedWords.length;
          reasons.push(`Skill match: ${skill}`);
        }
      }
    });

    return {
      score: Math.min(score, 100),
      reasons
    };
  };

  const currentTaskText = useCustomTask ? customTask : selectedTask;
  
  // Sort and filter workers based on score
  const suggestedCandidates = workers
    .map(w => {
      const { score, reasons } = getSkillMatchScore(w, currentTaskText);
      return { ...w, matchScore: score, matchReasons: reasons };
    })
    .filter(w => w.matchScore > 0)
    .sort((a, b) => b.matchScore - a.matchScore);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      
      {/* Header Section */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className={`text-3xl font-extrabold tracking-tight flex items-center gap-2.5 ${
            theme === 'light' ? 'text-slate-900' : 'text-white'
          }`}>
            <Users className="text-brand-400" />
            Worker & Resource Management
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage consultants, allocate roles, and assign SOW tasks.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAssignModal(true)}
            className={`flex items-center gap-2 px-4 py-2 bg-gradient-to-r transition-all shadow-md active:scale-95 hover:-translate-y-0.5 ${
              theme === 'light'
                ? 'from-slate-100 to-slate-50 border border-slate-200 text-slate-700 hover:from-slate-200 hover:to-slate-100'
                : 'from-slate-800 to-slate-700 border border-slate-700 text-white hover:from-slate-700 hover:to-slate-650'
            } rounded-xl text-xs font-bold`}
          >
            <Briefcase className="w-4 h-4 text-brand-400" />
            Assign Task
          </button>
          
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-brand-500/10 active:scale-95"
          >
            <UserPlus className="w-4 h-4" />
            {showAddForm ? 'Cancel Add' : 'Add Worker'}
          </button>
        </div>
      </div>

      {/* Forms Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Side Add Worker Profile Form */}
        {showAddForm && (
          <div className="lg:col-span-4 animate-fadeIn">
            <div className={`glass-panel border p-6 rounded-2xl space-y-4 ${
              theme === 'light' ? 'border-slate-200/80 shadow-sm bg-white' : 'border-brand-500/20'
            }`}>
              <h3 className={`text-sm font-bold uppercase tracking-wider flex items-center gap-2 ${
                theme === 'light' ? 'text-slate-800' : 'text-white'
              }`}>
                <UserPlus className="w-5 h-5 text-brand-400" />
                Add New Worker Profile
              </h3>
              
              <form onSubmit={handleAddWorker} className="space-y-4 text-xs text-slate-300">
                <div className="space-y-1">
                  <label className="text-slate-400 font-semibold">Full Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. John Doe"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className={`w-full border focus:border-brand-500 outline-none p-2.5 rounded-xl transition-all ${
                      theme === 'light' 
                        ? 'bg-white border-slate-200 text-slate-900 shadow-sm' 
                        : 'bg-slate-900 border-slate-800 text-slate-200'
                    }`}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400 font-semibold">Role</label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value)}
                    className={`w-full border focus:border-brand-500 outline-none p-2.5 rounded-xl transition-all ${
                      theme === 'light' 
                        ? 'bg-white border-slate-200 text-slate-900 shadow-sm' 
                        : 'bg-slate-900 border-slate-800 text-slate-200'
                    }`}
                  >
                    {STANDARD_ROLES.map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                    <option value="Other">Other...</option>
                  </select>
                </div>

                {newRole === 'Other' && (
                  <div className="space-y-1 animate-slideDown">
                    <label className="text-slate-400 font-semibold">Custom Role Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Cybersecurity Analyst"
                      value={customRole}
                      onChange={(e) => setCustomRole(e.target.value)}
                      className={`w-full border focus:border-brand-500 outline-none p-2.5 rounded-xl transition-all ${
                        theme === 'light' 
                          ? 'bg-white border-slate-200 text-slate-900 shadow-sm' 
                          : 'bg-slate-900 border-slate-800 text-slate-200'
                      }`}
                    />
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-slate-400 font-semibold">Skills (Comma-separated)</label>
                  <input
                    type="text"
                    placeholder="e.g. Python, SQL, Docker, FastAPI"
                    value={newSkills}
                    onChange={(e) => setNewSkills(e.target.value)}
                    className={`w-full border focus:border-brand-500 outline-none p-2.5 rounded-xl transition-all ${
                      theme === 'light' 
                        ? 'bg-white border-slate-200 text-slate-900 shadow-sm' 
                        : 'bg-slate-900 border-slate-800 text-slate-200'
                    }`}
                  />
                  <span className="text-[10px] text-slate-500 block mt-0.5">Separate multiple competencies with a comma.</span>
                </div>

                <button
                  type="submit"
                  className="w-full mt-2 py-2.5 bg-brand-500 hover:bg-brand-400 text-white font-bold rounded-xl transition-colors"
                >
                  Create Profile
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Right Side Workers Cards Grid */}
        <div className={`space-y-6 ${showAddForm ? 'lg:col-span-8' : 'lg:col-span-12'}`}>
          <div className="flex justify-between items-center">
            <h3 className={`text-sm font-bold uppercase tracking-widest flex items-center gap-2 ${
              theme === 'light' ? 'text-slate-700' : 'text-slate-300'
            }`}>
              <Activity className="w-4 h-4 text-brand-400 animate-pulse" />
              Resource Directory ({workers.length} registered)
            </h3>
          </div>

          <div className={`grid grid-cols-1 gap-6 ${
            showAddForm 
              ? 'md:grid-cols-2 xl:grid-cols-3' 
              : 'md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
          }`}>
            {workers.map((worker) => (
              <div 
                key={worker.id}
                className={`glass-panel p-6 rounded-2xl flex flex-col justify-between transition-all duration-300 hover:translate-y-[-2px] group relative overflow-hidden ${
                  theme === 'light'
                    ? 'border-slate-200/80 hover:border-brand-500/30 hover:shadow-lg hover:shadow-slate-200/50'
                    : 'border-slate-800/40 hover:border-brand-500/20'
                }`}
              >
                {/* Background accent */}
                <div className="absolute right-0 top-0 w-24 h-24 bg-gradient-to-bl from-brand-500/5 to-transparent rounded-full -mr-8 -mt-8 pointer-events-none" />

                <div className="space-y-4">
                  {/* Header: Name and Status */}
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className={`text-sm font-bold transition-colors ${
                        theme === 'light' ? 'text-slate-900 group-hover:text-black' : 'text-slate-100 group-hover:text-white'
                      }`}>
                        {worker.name}
                      </h4>
                      <p className={`text-[10px] font-bold mt-0.5 tracking-wide ${
                        theme === 'light' ? 'text-brand-600' : 'text-brand-400'
                      }`}>
                        {worker.role}
                      </p>
                    </div>

                    <span className={`text-[9px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                      worker.status === 'Available'
                        ? theme === 'light'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : theme === 'light'
                          ? 'bg-violet-50 text-violet-700 border-violet-200'
                          : 'bg-violet-500/10 text-violet-400 border-violet-500/20'
                    }`}>
                      {worker.status}
                    </span>
                  </div>

                  {/* Skills Section */}
                  <div className="flex flex-wrap gap-1.5 pt-1.5">
                    {worker.skills.map((s, idx) => (
                      <span 
                        key={idx} 
                        className={`text-[9px] font-semibold px-2 py-0.5 rounded-lg border ${
                          theme === 'light'
                            ? 'bg-slate-100 border-slate-200/80 text-slate-600'
                            : 'bg-slate-900 border-slate-800 text-slate-400'
                        }`}
                      >
                        {s}
                      </span>
                    ))}
                  </div>

                  {/* Assignments Section */}
                  <div className={`border-t pt-3.5 mt-2 space-y-2.5 ${
                    theme === 'light' ? 'border-slate-100' : 'border-slate-800/60'
                  }`}>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">
                      Allocated Tasks ({worker.assignments.length})
                    </span>
                    
                    {worker.assignments.length === 0 ? (
                      <span className="text-[10px] text-slate-500 italic block">
                        No tasks currently assigned.
                      </span>
                    ) : (
                      <div className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                        {worker.assignments.map((as, idx) => (
                          <div 
                            key={idx} 
                            className={`p-2.5 rounded-xl flex items-center justify-between text-[10px] gap-2 border ${
                              theme === 'light'
                                ? 'bg-slate-50 border-slate-200 text-slate-700'
                                : 'bg-slate-950/60 border-slate-900 text-slate-300'
                            }`}
                          >
                            <div className="truncate">
                              <span className={`font-semibold tracking-wide uppercase text-[8px] block ${
                                theme === 'light' ? 'text-slate-400' : 'text-slate-500'
                              }`}>
                                {as.projectName}
                              </span>
                              <span className={`font-medium block truncate ${
                                theme === 'light' ? 'text-slate-800' : 'text-slate-200'
                              }`}>
                                {as.task}
                              </span>
                            </div>

                            <button
                              type="button"
                              onClick={() => handleRemoveAssignment(worker.id, idx)}
                              className={`p-1 rounded transition-colors shrink-0 ${
                                theme === 'light'
                                  ? 'text-slate-400 hover:text-rose-600 hover:bg-rose-50'
                                  : 'text-slate-500 hover:text-rose-400 hover:bg-slate-900'
                              }`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer Action */}
                <div className="mt-4 pt-3 border-t border-slate-800/40 flex justify-end">
                  <button
                    type="button"
                    onClick={() => handleDeleteWorker(worker.id)}
                    className="text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 p-2 rounded-xl text-xs flex items-center gap-1.5 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    Remove Profile
                  </button>
                </div>

              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Assign Task Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
          <div className={`w-full max-w-3xl rounded-3xl p-6 md:p-8 border shadow-2xl animate-scaleUp relative ${
            theme === 'light' 
              ? 'bg-white border-slate-200 text-slate-900 shadow-slate-900/10' 
              : 'bg-slate-900 border-slate-800 text-slate-100'
          }`}>
            {/* Close button */}
            <button
              onClick={() => setShowAssignModal(false)}
              className={`absolute top-4 right-4 p-1.5 rounded-full transition-colors ${
                theme === 'light' 
                  ? 'text-slate-400 hover:bg-slate-100 hover:text-slate-700' 
                  : 'text-slate-500 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <X className="w-5 h-5" />
            </button>

            {/* Modal Header */}
            <div className="border-b pb-4 mb-6 border-slate-800/40">
              <h2 className="text-xl font-bold flex items-center gap-2.5">
                <Briefcase className="text-brand-400 w-5 h-5" />
                Assign SOW Task to Consultant
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Select an active SOW project and assign deliverables to registered team members.
              </p>
            </div>

            {projects.length === 0 ? (
              <div className="p-8 text-center rounded-2xl bg-slate-950/30 border border-slate-800/50">
                <AlertCircle className="w-8 h-8 text-slate-500 mx-auto mb-3" />
                <p className="text-sm font-semibold">No active projects found.</p>
                <p className="text-xs text-slate-500 mt-1">Please ingest an SOW first from the Dashboard.</p>
              </div>
            ) : (
              <form onSubmit={(e) => { handleAssignTask(e); setShowAssignModal(false); }} className="space-y-6">
                
                {assignmentMessage && (
                  <div className={`p-3 rounded-xl flex items-center gap-2 text-xs ${
                    assignmentMessage.type === 'success' 
                      ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' 
                      : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
                  }`}>
                    {assignmentMessage.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>{assignmentMessage.text}</span>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-xs">
                  {/* Left Column: Selection Form */}
                  <div className="space-y-4">
                    <div className="space-y-1">
                      <label className="text-slate-400 font-semibold">Select Project SOW</label>
                      <select
                        value={selectedProjectId}
                        onChange={(e) => setSelectedProjectId(e.target.value)}
                        className={`w-full border focus:border-brand-500 outline-none p-2.5 rounded-xl transition-all ${
                          theme === 'light' 
                            ? 'bg-white border-slate-200 text-slate-900 shadow-sm' 
                            : 'bg-slate-900 border-slate-800 text-slate-200'
                        }`}
                      >
                        {projects.map((p, i) => {
                          const name = p.project_overview?.project_name || p.project_name || 'Project ' + (i + 1);
                          return <option key={i} value={name}>{name}</option>;
                        })}
                      </select>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <label className="text-slate-400 font-semibold">Task / Deliverable</label>
                        <button
                          type="button"
                          onClick={() => setUseCustomTask(!useCustomTask)}
                          className="text-[10px] text-brand-400 hover:text-brand-300 font-bold"
                        >
                          {useCustomTask ? 'Select SOW tasks' : 'Input custom task'}
                        </button>
                      </div>

                      {useCustomTask ? (
                        <input
                          type="text"
                          required
                          placeholder="e.g. Conduct PCI-DSS security checks"
                          value={customTask}
                          onChange={(e) => setCustomTask(e.target.value)}
                          className={`w-full border focus:border-brand-500 outline-none p-2.5 rounded-xl transition-all ${
                            theme === 'light' 
                              ? 'bg-white border-slate-200 text-slate-900 shadow-sm' 
                              : 'bg-slate-900 border-slate-800 text-slate-200'
                          }`}
                        />
                      ) : (
                        <select
                          value={selectedTask}
                          onChange={(e) => setSelectedTask(e.target.value)}
                          className={`w-full border focus:border-brand-500 outline-none p-2.5 rounded-xl transition-all ${
                            theme === 'light' 
                              ? 'bg-white border-slate-200 text-slate-900 shadow-sm' 
                              : 'bg-slate-900 border-slate-800 text-slate-200'
                          }`}
                        >
                          {tasksAvailable.length > 0 ? (
                            tasksAvailable.map((t, idx) => (
                              <option key={idx} value={t}>{t}</option>
                            ))
                          ) : (
                            <option value="">No structured SOW tasks found</option>
                          )}
                        </select>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-slate-400 font-semibold">Assign To Consultant</label>
                      <select
                        value={selectedWorkerId}
                        onChange={(e) => setSelectedWorkerId(e.target.value)}
                        className={`w-full border focus:border-brand-500 outline-none p-2.5 rounded-xl transition-all ${
                          theme === 'light' 
                            ? 'bg-white border-slate-200 text-slate-900 shadow-sm' 
                            : 'bg-slate-900 border-slate-800 text-slate-200'
                        }`}
                      >
                        <option value="">-- Choose Consultant --</option>
                        {workers.map(w => (
                          <option key={w.id} value={w.id}>{w.name} ({w.role})</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Right Column: Skill Suggestions */}
                  <div className="space-y-3 flex flex-col h-full">
                    <label className="text-slate-400 font-semibold">Recommended Candidates (Skill Match)</label>
                    {currentTaskText ? (
                      <div className={`p-4 rounded-2xl border flex-1 space-y-3 max-h-[220px] overflow-y-auto ${
                        theme === 'light' ? 'bg-slate-50 border-slate-200/80' : 'bg-slate-950/40 border-slate-800/80'
                      }`}>
                        {suggestedCandidates.length === 0 ? (
                          <div className="h-full flex items-center justify-center text-center text-slate-500 italic text-[11px] py-8">
                            No specific skills match this task. Choose any consultant manually.
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {suggestedCandidates.map((c) => (
                              <button
                                key={c.id}
                                type="button"
                                onClick={() => setSelectedWorkerId(c.id)}
                                className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-all border ${
                                  selectedWorkerId === c.id 
                                    ? theme === 'light'
                                      ? 'bg-brand-50/80 border-brand-400 text-brand-700 font-medium'
                                      : 'bg-brand-950/40 border-brand-500/30 text-brand-300 font-medium'
                                    : theme === 'light'
                                      ? 'bg-white border-slate-200 hover:border-brand-500/20 text-slate-700 shadow-sm'
                                      : 'bg-slate-900 border-slate-800 hover:border-brand-500/20 text-slate-300'
                                }`}
                              >
                                <div>
                                  <div className="font-bold text-[11px] flex items-center gap-1.5">
                                    <span className={theme === 'light' ? 'text-slate-900' : 'text-slate-100'}>{c.name}</span>
                                    <span className="text-[9px] font-normal text-slate-500">({c.role})</span>
                                  </div>
                                  {c.matchReasons.length > 0 && (
                                    <div className="text-[9px] text-slate-500 truncate max-w-[220px] mt-0.5">
                                      {c.matchReasons.join(', ')}
                                    </div>
                                  )}
                                </div>
                                <span className={`text-[10px] font-bold shrink-0 ${theme === 'light' ? 'text-brand-600' : 'text-brand-400'}`}>
                                  {c.matchScore}% Match
                                </span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-center p-4 border border-dashed border-slate-800/40 rounded-2xl text-slate-500 italic text-[11px]">
                        Select or enter a task to see AI recommendations.
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer Buttons */}
                <div className="flex justify-end gap-3 border-t pt-4 border-slate-800/40">
                  <button
                    type="button"
                    onClick={() => setShowAssignModal(false)}
                    className={`px-4 py-2 rounded-xl font-bold transition-colors ${
                      theme === 'light'
                        ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                        : 'bg-slate-800 hover:bg-slate-700 text-white'
                    }`}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!selectedWorkerId}
                    className="px-5 py-2 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-bold rounded-xl transition-all shadow-lg shadow-brand-500/10 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Allocate Assignment
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
