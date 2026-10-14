import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import AIProcessingPanel from './components/AIProcessingPanel';
import ProjectDetails from './components/ProjectDetails';
import Workers from './components/Workers';
import Pipeline from './components/Pipeline';
import { 
  FolderGit2,
  Settings as SettingsIcon,
  FileText,
  AlertCircle,
  HelpCircle,
  Building,
  CheckCircle2,
  Compass,
  Mail,
  Trash2,
  Loader2
} from 'lucide-react';

interface ProjectListItem {
  project_name: string;
  client: string;
  budget: number | string;
  target_budget?: string;
  readiness_score: number;
  processed_at: string;
}

interface DashboardStats {
  projects_processed: number;
  emails_received: number;
  ai_agents_executed: number;
  estimated_budget: number;
  total_resources: number;
  project_duration_weeks: number;
  recent_projects: ProjectListItem[];
}

const DEFAULT_STATS: DashboardStats = {
  projects_processed: 0,
  emails_received: 5, // Default base
  ai_agents_executed: 0,
  estimated_budget: 0,
  total_resources: 0,
  project_duration_weeks: 0,
  recent_projects: []
};

export default function App() {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [stats, setStats] = useState<DashboardStats>(DEFAULT_STATS);
  const [statsLoading, setStatsLoading] = useState<boolean>(true);
  const [selectedProjectData, setSelectedProjectData] = useState<any | null>(null);
  const [scanningGmail, setScanningGmail] = useState<boolean>(false);

  const [contentLibrary, setContentLibrary] = useState<{ id: number; label: string; content: string }[]>([]);
  const [newEntryLabel, setNewEntryLabel] = useState<string>('');
  const [newEntryContent, setNewEntryContent] = useState<string>('');
  const [addingEntry, setAddingEntry] = useState<boolean>(false);

  const [approvalContacts, setApprovalContacts] = useState<{ department: string; email: string }[]>([]);
  const [newContactDept, setNewContactDept] = useState<string>('');
  const [newContactEmail, setNewContactEmail] = useState<string>('');
  const [addingContact, setAddingContact] = useState<boolean>(false);
  
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('sowpilot_theme') as 'dark' | 'light') || 'dark';
  });

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-mode');
    } else {
      document.body.classList.remove('light-mode');
    }
    localStorage.setItem('sowpilot_theme', theme);
  }, [theme]);
  
  const handleScanGmail = async () => {
    setScanningGmail(true);
    try {
      const res = await fetch('/api/scan-gmail', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success') {
          if (data.processed_sows > 0) {
            alert(`Sync complete! Ingested ${data.processed_sows} project SOW(s) from your Gmail inbox!`);
            fetchDashboardStats();
          } else {
            alert("Sync complete. No new unread SOW emails found.");
          }
        } else {
          alert(`Sync skipped: ${data.message}`);
        }
      } else {
        const err = await res.json();
        alert(`Failed to scan Gmail inbox: ${err.detail || 'check connection configuration'}`);
      }
    } catch (err) {
      console.error(err);
      alert("Error scanning Gmail inbox. Ensure backend server is running.");
    } finally {
      setScanningGmail(false);
    }
  };
  
  // Connect to backend and fetch dashboard statistics
  const fetchDashboardStats = async () => {
    try {
      const res = await fetch('/api/dashboard');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
        setBackendConnected(true);
      } else {
        setBackendConnected(false);
      }
    } catch (err) {
      console.error("Error fetching dashboard stats:", err);
      setBackendConnected(false);
    } finally {
      setStatsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardStats();
    // Poll stats every 8 seconds
    const interval = setInterval(fetchDashboardStats, 8000);
    return () => clearInterval(interval);
  }, []);

  const fetchContentLibrary = async () => {
    try {
      const res = await fetch('/api/content-library');
      if (res.ok) setContentLibrary(await res.json());
    } catch (err) {
      console.error("Error fetching content library:", err);
    }
  };

  const fetchApprovalContacts = async () => {
    try {
      const res = await fetch('/api/approval-contacts');
      if (res.ok) setApprovalContacts(await res.json());
    } catch (err) {
      console.error("Error fetching approval contacts:", err);
    }
  };

  useEffect(() => {
    if (currentTab === 'settings') {
      fetchContentLibrary();
      fetchApprovalContacts();
    }
  }, [currentTab]);

  const handleAddContentEntry = async () => {
    if (!newEntryLabel.trim() || !newEntryContent.trim()) return;
    setAddingEntry(true);
    try {
      const res = await fetch('/api/content-library', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: newEntryLabel.trim(), content: newEntryContent.trim() })
      });
      if (res.ok) {
        setContentLibrary(await res.json());
        setNewEntryLabel('');
        setNewEntryContent('');
      } else {
        alert('Failed to add content library entry.');
      }
    } catch (err) {
      console.error(err);
      alert('Failed to add content library entry.');
    } finally {
      setAddingEntry(false);
    }
  };

  const handleDeleteContentEntry = async (id: number) => {
    try {
      const res = await fetch(`/api/content-library/${id}`, { method: 'DELETE' });
      if (res.ok) setContentLibrary(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to delete content library entry.');
    }
  };

  const handleAddApprovalContact = async () => {
    if (!newContactDept.trim() || !newContactEmail.trim()) return;
    setAddingContact(true);
    try {
      const res = await fetch('/api/approval-contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ department: newContactDept.trim(), email: newContactEmail.trim() })
      });
      if (res.ok) {
        setApprovalContacts(await res.json());
        setNewContactDept('');
        setNewContactEmail('');
      } else {
        const err = await res.json();
        alert(err.detail || 'Failed to save contact.');
      }
    } catch (err) {
      console.error(err);
      alert('Failed to save contact.');
    } finally {
      setAddingContact(false);
    }
  };

  const handleDeleteApprovalContact = async (department: string) => {
    try {
      const res = await fetch(`/api/approval-contacts/${encodeURIComponent(department)}`, { method: 'DELETE' });
      if (res.ok) setApprovalContacts(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to delete contact.');
    }
  };

  // Fetch full details of a specific project when clicked from list
  const handleSelectProject = async (projectName: string) => {
    setStatsLoading(true);
    try {
      // Fetch all projects and search for a match
      const res = await fetch('/api/projects');
      if (res.ok) {
        const allProjects = await res.json();
        const found = allProjects.find((p: any) => 
          (p.project_overview?.project_name === projectName || p.project_name === projectName)
        );
        
        if (found) {
          setSelectedProjectData(found);
          setCurrentTab('project_details');
          return;
        }
      }
      
      // Fallback: get the latest project and adjust overview name
      const fallbackRes = await fetch('/api/project');
      if (fallbackRes.ok) {
        const fullProj = await fallbackRes.json();
        const simulatedMatch = {
          ...fullProj,
          project_overview: {
            ...fullProj.project_overview,
            project_name: projectName
          }
        };
        setSelectedProjectData(simulatedMatch);
        setCurrentTab('project_details');
      }
    } catch (err) {
      console.error("Failed to load project details:", err);
    } finally {
      setStatsLoading(false);
    }
  };

  // Called when AI Processing Panel yields final result
  const handleAIProcessingComplete = (completedProjectData: any) => {
    setSelectedProjectData(completedProjectData);
    fetchDashboardStats(); // Refresh stats immediately
    setCurrentTab('project_details'); // Automatically direct to details page
  };

  return (
    <div className="flex bg-slate-950 min-h-screen text-slate-100 font-sans">
      
      {/* Sidebar Nav */}
      <Sidebar 
        currentTab={currentTab === 'project_details' ? 'projects' : currentTab} 
        setCurrentTab={(tab) => {
          setSelectedProjectData(null);
          setCurrentTab(tab);
        }} 
        backendConnected={backendConnected}
        theme={theme}
        toggleTheme={toggleTheme}
      />

      {/* Main Panel Content */}
      <main className="flex-1 overflow-y-auto h-screen relative">

        <div className="pb-12">
          {currentTab === 'dashboard' && (
            <Dashboard
              stats={stats}
              loading={statsLoading}
              onNavigateToProcessing={() => setCurrentTab('processing')}
              onSelectProject={handleSelectProject}
              onAssignWorkers={(projectName) => {
                localStorage.setItem('sowpilot_preselected_project', projectName);
                setCurrentTab('workers');
              }}
              onScanGmail={handleScanGmail}
              scanningGmail={scanningGmail}
            />
          )}

          {currentTab === 'processing' && (
            <AIProcessingPanel onProcessingComplete={handleAIProcessingComplete} />
          )}

          {currentTab === 'pipeline' && (
            <Pipeline onSelectProject={handleSelectProject} />
          )}

          {currentTab === 'project_details' && (
            <ProjectDetails 
              project={selectedProjectData} 
              onBack={() => {
                setSelectedProjectData(null);
                setCurrentTab('dashboard');
              }} 
              onAssignTasks={(projectName) => {
                localStorage.setItem('sowpilot_preselected_project', projectName);
                setCurrentTab('workers');
              }}
            />
          )}

          {currentTab === 'projects' && (
            <div className="p-8 max-w-6xl mx-auto space-y-6">
              <div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
                  <FolderGit2 className="text-brand-400" />
                  Processed SOW Portfolio
                </h1>
                <p className="text-slate-400 text-sm mt-1">Manage and view AI project synthesis insights for all ingested projects.</p>
              </div>

              {stats.recent_projects.length === 0 ? (
                <div className="glass-panel border-slate-800/40 p-10 text-center rounded-2xl">
                  <AlertCircle className="w-10 h-10 text-slate-500 mx-auto mb-3" />
                  <h3 className="text-sm font-bold text-slate-300">No Projects</h3>
                  <p className="text-xs text-slate-500 mt-1">SOW documents that are processed will display here.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {stats.recent_projects.map((proj, idx) => (
                    <div key={idx} className="glass-panel border-slate-800/40 p-5 rounded-2xl flex flex-col justify-between group hover:border-brand-500/30 transition-all">
                      <div className="space-y-1.5">
                        <div className="flex justify-between items-center">
                          <span className="text-[9px] font-bold text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded uppercase">
                            Client Project
                          </span>
                          <span className="text-[10px] text-slate-500">{proj.processed_at}</span>
                        </div>
                        <h3 className="text-base font-bold text-slate-200 group-hover:text-white truncate">
                          {proj.project_name}
                        </h3>
                        <div className="flex gap-2 text-xs text-slate-400">
                          <span className="flex items-center gap-1"><Building className="w-3.5 h-3.5" /> {proj.client}</span>
                          <span>•</span>
                          <span className="font-semibold text-brand-400">
                            {typeof proj.budget === 'number' ? `$${proj.budget.toLocaleString()}` : proj.budget}
                          </span>
                        </div>
                      </div>

                      <div className="mt-5 pt-3.5 border-t border-slate-800/50 flex justify-end items-center">
                        <button
                          onClick={() => handleSelectProject(proj.project_name)}
                          className="flex items-center gap-1 text-xs font-bold text-brand-400 hover:text-brand-300 transition-colors"
                        >
                          View AI Synthesis
                          <Compass className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {currentTab === 'reports' && (
            <div className="p-8 max-w-5xl mx-auto space-y-6">
              <div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
                  <FileText className="text-brand-400" />
                  Portfolio AI Insights
                </h1>
                <p className="text-slate-400 text-sm mt-1">Aggregated SOW recommendations and budget parameters.</p>
              </div>

              {stats.recent_projects.length === 0 ? (
                <div className="glass-panel border-slate-800/40 p-10 text-center rounded-2xl">
                  <FileText className="w-10 h-10 text-slate-500 mx-auto mb-3" />
                  <h3 className="text-sm font-bold text-slate-300">No AI Insights Available</h3>
                  <p className="text-xs text-slate-500 mt-1">Processed recommendation sheets will appear once SOWs are ingested.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Total Portfolio Allocation</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                       <div className="bg-slate-900/30 border border-slate-800/40 p-4 rounded-xl">
                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Total Allocated Budget</span>
                        <div className="text-2xl font-bold text-emerald-400 mt-1">
                          ${stats.estimated_budget.toLocaleString()}
                        </div>
                      </div>
                      <div className="bg-slate-900/30 border border-slate-800/40 p-4 rounded-xl">
                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Engineering Staff</span>
                        <div className="text-2xl font-bold text-brand-400 mt-1">
                          {stats.total_resources} FTEs
                        </div>
                      </div>
                      <div className="bg-slate-900/30 border border-slate-800/40 p-4 rounded-xl">
                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Average Scope Duration</span>
                        <div className="text-2xl font-bold text-violet-400 mt-1">
                          {stats.project_duration_weeks} Weeks
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">Ingested SOW Files Logs</h3>
                    <div className="space-y-3.5">
                      {stats.recent_projects.map((proj, idx) => (
                        <div key={idx} className="bg-slate-900/30 border border-slate-800/50 p-4 rounded-xl flex items-center justify-between text-xs">
                          <div className="space-y-1">
                            <h4 className="font-bold text-slate-200">{proj.project_name}</h4>
                            <div className="text-slate-500 flex gap-2">
                              <span>Client: {proj.client}</span>
                              <span>•</span>
                              <span>Date: {proj.processed_at}</span>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-3">
                            <span className="text-[10px] font-bold px-2.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              Processed
                            </span>
                            <button
                              onClick={() => handleSelectProject(proj.project_name)}
                              className="text-brand-400 hover:underline font-semibold"
                            >
                              Explore AI Insights
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {currentTab === 'settings' && (
            <div className="p-8 max-w-4xl mx-auto space-y-6">
              <div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
                  <SettingsIcon className="text-brand-400" />
                  System Settings
                </h1>
                <p className="text-slate-400 text-sm mt-1">Configure and view SOWPilot API parameters.</p>
              </div>

              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">Model Configuration</h3>
                  <p className="text-xs text-slate-400 mb-4">Orchestration triggers standard inference endpoints.</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl text-xs space-y-1">
                      <span className="text-slate-500 font-bold">Selected LLM Engine</span>
                      <div className="text-sm font-bold text-slate-200">Claude Haiku 4.5 (AWS Bedrock)</div>
                    </div>
                    <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl text-xs space-y-1">
                      <span className="text-slate-500 font-bold">Orchestrator</span>
                      <div className="text-sm font-bold text-slate-200">SSE Pipeline (8 Agents)</div>
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-800/60 pt-6">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">Workspace & Credentials</h3>
                  <p className="text-xs text-slate-400 mb-4">API configuration variables loaded on server startup.</p>

                  <div className="space-y-3.5 text-xs text-slate-300">
                    <div className="flex justify-between items-center bg-slate-950/30 p-3 rounded-lg border border-slate-900">
                      <span>AWS Bedrock Credentials Status</span>
                      <span className="px-2.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold uppercase tracking-wider text-[9px]">
                        LOADED FROM .ENV
                      </span>
                    </div>
                    <div className="flex justify-between items-center bg-slate-950/30 p-3 rounded-lg border border-slate-900">
                      <span>Local Persistence Storage</span>
                      <span className="text-slate-400">backend/sowpilot.db (SQLite)</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">Content Library</h3>
                  <p className="text-xs text-slate-400">
                    Pre-approved company messaging (overview, certifications language, etc.) that the client
                    proposal agent draws on for consistent branding across proposals, instead of inventing
                    company claims fresh every time.
                  </p>
                </div>

                <div className="space-y-3">
                  {contentLibrary.length === 0 && (
                    <p className="text-xs text-slate-500 italic">No content library entries yet.</p>
                  )}
                  {contentLibrary.map((entry) => (
                    <div key={entry.id} className="bg-slate-950/30 border border-slate-900 p-3.5 rounded-lg">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-xs font-bold text-slate-200">{entry.label}</p>
                          <p className="text-xs text-slate-400 mt-1 leading-relaxed">{entry.content}</p>
                        </div>
                        <button
                          onClick={() => handleDeleteContentEntry(entry.id)}
                          className="text-slate-500 hover:text-rose-400 shrink-0"
                          title="Delete entry"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t border-slate-800/60 pt-4 space-y-2.5">
                  <input
                    type="text"
                    placeholder="Label (e.g. 'Company Overview')"
                    value={newEntryLabel}
                    onChange={(e) => setNewEntryLabel(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                  <textarea
                    placeholder="Content (the approved text itself)"
                    value={newEntryContent}
                    onChange={(e) => setNewEntryContent(e.target.value)}
                    rows={3}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                  <button
                    onClick={handleAddContentEntry}
                    disabled={addingEntry || !newEntryLabel.trim() || !newEntryContent.trim()}
                    className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white text-xs font-bold rounded-xl inline-flex items-center gap-2"
                  >
                    {addingEntry ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                    Add Entry
                  </button>
                </div>
              </div>

              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">Approval Routing Contacts</h3>
                  <p className="text-xs text-slate-400">
                    When a flagged concern is routed to a department (Finance, Legal, Security &amp; Compliance),
                    an email notification is sent here automatically. Departments with no contact configured are
                    skipped silently — nothing breaks, they just won't be notified.
                  </p>
                </div>

                <div className="space-y-3">
                  {approvalContacts.length === 0 && (
                    <p className="text-xs text-slate-500 italic">No routing contacts configured yet — flagged concerns will still appear in each project's Approvals tab, just without an email notification.</p>
                  )}
                  {approvalContacts.map((contact) => (
                    <div key={contact.department} className="bg-slate-950/30 border border-slate-900 p-3.5 rounded-lg flex items-center justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold text-slate-200">{contact.department}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{contact.email}</p>
                      </div>
                      <button
                        onClick={() => handleDeleteApprovalContact(contact.department)}
                        className="text-slate-500 hover:text-rose-400 shrink-0"
                        title="Remove contact"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>

                <div className="border-t border-slate-800/60 pt-4 space-y-2.5">
                  <input
                    type="text"
                    placeholder="Department (e.g. 'Finance', 'Legal', 'Security & Compliance')"
                    value={newContactDept}
                    onChange={(e) => setNewContactDept(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                  <input
                    type="email"
                    placeholder="Notification email"
                    value={newContactEmail}
                    onChange={(e) => setNewContactEmail(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                  <button
                    onClick={handleAddApprovalContact}
                    disabled={addingContact || !newContactDept.trim() || !newContactEmail.trim()}
                    className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white text-xs font-bold rounded-xl inline-flex items-center gap-2"
                  >
                    {addingContact ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                    Save Contact
                  </button>
                </div>
              </div>
            </div>
          )}

          {currentTab === 'workers' && (
            <Workers />
          )}
        </div>
      </main>

    </div>
  );
}
