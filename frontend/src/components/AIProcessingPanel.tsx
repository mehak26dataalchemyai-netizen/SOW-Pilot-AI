import React, { useState, useRef } from 'react';
import { 
  Cpu, 
  Upload, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight,
  Loader2,
  FileText,
  Mail,
  Users,
  Clock,
  DollarSign,
  ShieldAlert,
  Layers
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface AIProcessingPanelProps {
  onProcessingComplete: (projectData: any) => void;
}

interface AgentState {
  name: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  icon: any;
}

const INITIAL_AGENTS: Record<string, AgentState> = {
  "Requirement Extraction Agent": {
    name: "Requirement Extraction Agent",
    status: 'idle',
    progress: 0,
    message: "Awaiting PDF ingestion...",
    icon: FileText
  },
  "Resource Allocation Agent": {
    name: "Resource Allocation Agent",
    status: 'idle',
    progress: 0,
    message: "Queued...",
    icon: Users
  },
  "Timeline Planning Agent": {
    name: "Timeline Planning Agent",
    status: 'idle',
    progress: 0,
    message: "Queued...",
    icon: Clock
  },
  "Cost Estimation Agent": {
    name: "Cost Estimation Agent",
    status: 'idle',
    progress: 0,
    message: "Queued...",
    icon: DollarSign
  },
  "Risk Analysis Agent": {
    name: "Risk Analysis Agent",
    status: 'idle',
    progress: 0,
    message: "Queued...",
    icon: ShieldAlert
  },
  "Executive Report Agent": {
    name: "Executive Report Agent",
    status: 'idle',
    progress: 0,
    message: "Queued...",
    icon: Layers
  }
};

export default function AIProcessingPanel({ onProcessingComplete }: AIProcessingPanelProps) {
  const [agents, setAgents] = useState<Record<string, AgentState>>(INITIAL_AGENTS);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Simulated email hooks inputs
  const [emailSender, setEmailSender] = useState("apex-contracts@apexcorp.com");
  const [emailSubject, setEmailSubject] = useState("Project SOW Proposal - Apex Visual Dashboard Node Graph");
  const [useSimulatedFile, setUseSimulatedFile] = useState(true);
  const [emailBody, setEmailBody] = useState(
    "Project Name: Apex Analytics Dashboard\n" +
    "Client: Apex Corp\n" +
    "Duration: 8 Weeks\n" +
    "Budget: $85,000\n" +
    "Technologies: React, Tailwind CSS, FastAPI, PostgreSQL\n\n" +
    "Deliverables:\n" +
    "- Interactive dashboard UI with 4 main widgets\n" +
    "- Secure backend API with JWT login\n" +
    "- Automated daily email report generation pipeline"
  );

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUseSimulatedFile(false);
      setErrorMessage(null);
    }
  };

  const startOrchestration = async (fileToUse: File | null) => {
    setIsProcessing(true);
    setErrorMessage(null);
    
    // Proper reset that preserves non-serializable properties like React components (icons)
    const resetAgents: Record<string, AgentState> = {};
    for (const key in INITIAL_AGENTS) {
      resetAgents[key] = {
        ...INITIAL_AGENTS[key],
        status: 'idle',
        progress: 0,
        message: key === "Requirement Extraction Agent" ? "Awaiting PDF ingestion..." : "Queued..."
      };
    }
    setAgents(resetAgents);

    try {
      let fileId = "";
      let filename = "";

      if (fileToUse) {
        // Step 1: Upload the file to FastAPI to acquire file_id
        const uploadFormData = new FormData();
        uploadFormData.append("file", fileToUse);

        const uploadRes = await fetch("/api/upload", {
          method: "POST",
          body: uploadFormData
        });

        if (!uploadRes.ok) {
          const errData = await uploadRes.json();
          throw new Error(errData.detail || "PDF Upload failed.");
        }

        const uploadData = await uploadRes.json();
        fileId = uploadData.file_id;
        filename = uploadData.filename;
      } else {
        // Simulate uploading a file by calling upload with a generated mock PDF content
        // We will make a tiny PDF blob and upload it
        const mockPdfBlob = new Blob(["%PDF-1.4 Simulated SOW SOWPilot Project"], { type: "application/pdf" });
        const mockFile = new File([mockPdfBlob], "apex_dashboard_sow.pdf", { type: "application/pdf" });
        
        const uploadFormData = new FormData();
        uploadFormData.append("file", mockFile);

        const uploadRes = await fetch("/api/upload", {
          method: "POST",
          body: uploadFormData
        });

        if (!uploadRes.ok) {
          throw new Error("Failed to configure simulated PDF session.");
        }
        const uploadData = await uploadRes.json();
        fileId = uploadData.file_id;
        filename = "apex_dashboard_sow.pdf";
      }

      // Step 2: Establish SSE Connection to start LangGraph stream
      const queryParams = new URLSearchParams({
        file_id: fileId || '',
        email_body: useSimulatedFile ? emailBody : '',
        sender: emailSender,
        subject: emailSubject
      });

      const eventSource = new EventSource(`/api/process-project-stream?${queryParams.toString()}`);

      eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type === 'status') {
            const { agent, status, progress, message, data } = payload;
            
            setAgents((prev) => {
              const updated = { ...prev };
              if (updated[agent]) {
                updated[agent] = {
                  ...updated[agent],
                  status,
                  progress,
                  message
                };
              }
              return updated;
            });
          } else if (payload.type === 'final_result') {
            eventSource.close();
            setIsProcessing(false);
            onProcessingComplete(payload.data);
          } else if (payload.type === 'error') {
            eventSource.close();
            setIsProcessing(false);
            setErrorMessage(payload.message || "An AI orchestration error occurred.");
          }
        } catch (err) {
          console.error("Error parsing stream message: ", err);
        }
      };

      eventSource.onerror = (err) => {
        console.error("EventSource encountered an error:", err);
        eventSource.close();
        setIsProcessing(false);
        setErrorMessage("Lost stream connection to backend server.");
      };

    } catch (err: any) {
      console.error(err);
      setIsProcessing(false);
      setErrorMessage(err.message || "An unexpected setup error occurred.");
    }
  };

  const triggerIngestion = () => {
    if (!useSimulatedFile && !selectedFile) {
      setErrorMessage("Please select a SOW PDF file, or toggle simulation.");
      return;
    }
    startOrchestration(useSimulatedFile ? null : selectedFile);
  };

  const getAgentCardStyles = (status: string) => {
    switch (status) {
      case 'running':
        return 'border-brand-500/50 bg-brand-950/20 shadow-lg shadow-brand-500/10 scale-102 ring-1 ring-brand-400/20';
      case 'completed':
        return 'border-emerald-500/30 bg-emerald-950/5';
      case 'failed':
        return 'border-rose-500/30 bg-rose-950/10';
      default:
        return 'border-slate-800/40 bg-slate-900/20 opacity-60';
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <Cpu className="text-brand-400 animate-pulse" />
          AI Orchestration
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Monitor multi-agent LangGraph workflow execution in real-time.
        </p>
      </div>

      {/* Control panel & Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Simulator controls */}
        <div className="lg:col-span-4 space-y-5">
          <div className="glass-panel border-slate-800/40 p-5 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold text-white uppercase tracking-widest text-slate-300 flex items-center gap-2">
              <Mail className="w-4.5 h-4.5 text-brand-400" />
              Gmail Webhook Trigger
            </h2>
            <p className="text-slate-400 text-xs leading-relaxed">
              Simulate an incoming delivery SOW email from the configured Gmail API hook.
            </p>

            <div className="space-y-3 pt-2">
              <div>
                <label className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block mb-1">Email Sender</label>
                <input 
                  type="text" 
                  value={emailSender} 
                  onChange={(e) => setEmailSender(e.target.value)}
                  disabled={isProcessing}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500 disabled:opacity-50"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block mb-1">Email Subject</label>
                <input 
                  type="text" 
                  value={emailSubject} 
                  onChange={(e) => setEmailSubject(e.target.value)}
                  disabled={isProcessing}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500 disabled:opacity-50"
                />
              </div>

              {/* PDF Selector */}
              <div className="pt-2">
                <label className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block mb-2">SOW Attachment</label>
                
                <div className="flex gap-2 mb-2">
                  <button
                    type="button"
                    onClick={() => setUseSimulatedFile(true)}
                    disabled={isProcessing}
                    className={`flex-1 text-center py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                      useSimulatedFile 
                        ? 'bg-brand-900/30 text-brand-300 border-brand-500/40' 
                        : 'border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Simulated SOW
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setUseSimulatedFile(false);
                      fileInputRef.current?.click();
                    }}
                    disabled={isProcessing}
                    className={`flex-1 text-center py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                      !useSimulatedFile 
                        ? 'bg-brand-900/30 text-brand-300 border-brand-500/40' 
                        : 'border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Upload SOW
                  </button>
                </div>

                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange}
                  accept="application/pdf"
                  className="hidden"
                />

                {useSimulatedFile ? (
                  <div className="space-y-1">
                    <label className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block mb-1">Email SOW Content (Edit or Paste SOW)</label>
                    <textarea 
                      value={emailBody} 
                      onChange={(e) => setEmailBody(e.target.value)}
                      disabled={isProcessing}
                      rows={5}
                      className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-[11px] text-slate-200 focus:outline-none focus:border-brand-500 disabled:opacity-50 font-mono resize-y"
                      placeholder="Type a single line, full text SOW, or paste multiple SOW descriptions here..."
                    />
                  </div>
                ) : (
                  <div className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-3 flex items-center justify-between text-xs">
                    <span className="text-slate-300 truncate max-w-[180px] font-medium">
                      {selectedFile ? selectedFile.name : "No PDF selected..."}
                    </span>
                    {selectedFile && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    )}
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={triggerIngestion}
              disabled={isProcessing}
              className="w-full flex items-center justify-center gap-2 py-3 mt-3 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white rounded-xl text-xs font-bold transition-all shadow-md disabled:opacity-50 disabled:pointer-events-none transform active:scale-95"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4.5 h-4.5 animate-spin" />
                  Running AI Agents...
                </>
              ) : (
                <>
                  <Cpu className="w-4.5 h-4.5" />
                  Trigger Automated Ingest
                </>
              )}
            </button>
          </div>

          {errorMessage && (
            <div className="glass-panel border-rose-500/30 bg-rose-950/15 p-4 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-rose-300">Ingestion Error</h4>
                <p className="text-[11px] text-rose-400 mt-1 leading-relaxed">{errorMessage}</p>
              </div>
            </div>
          )}
        </div>

        {/* Live Orchestrator DAG Graph */}
        <div className="lg:col-span-8 glass-panel border-slate-800/40 p-6 rounded-2xl flex flex-col items-center">
          <div className="w-full border-b border-slate-800/50 pb-3 mb-8 flex justify-between items-center">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider text-slate-300">Live Agent Pipeline Map</h3>
            {isProcessing && (
              <span className="text-[10px] px-2.5 py-1 bg-brand-900/30 text-brand-300 border border-brand-500/30 rounded-full flex items-center gap-1.5 font-medium animate-pulse">
                <Loader2 className="w-3 h-3 animate-spin" />
                Active Execution
              </span>
            )}
          </div>

          <div className="w-full max-w-xl flex flex-col items-center relative py-4">
            
            {/* AGENT 1: Extraction */}
            <div className="w-full flex justify-center z-10">
              <AgentNode 
                agent={agents["Requirement Extraction Agent"]} 
                styles={getAgentCardStyles(agents["Requirement Extraction Agent"].status)}
              />
            </div>

            {/* Split connection line SVG */}
            <div className="w-full h-12 relative">
              <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#38a9f8" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#0e8ce2" stopOpacity="0.4" />
                  </linearGradient>
                </defs>
                {/* Center extraction node down split */}
                <path 
                  d="M 288 0 L 288 12 M 288 12 L 64 12 L 64 48 M 288 12 L 210 12 L 210 48 M 288 12 L 366 12 L 366 48 M 288 12 L 512 12 L 512 48" 
                  stroke="rgba(56, 169, 248, 0.2)" 
                  strokeWidth="2" 
                  fill="none" 
                />
                {isProcessing && (
                  <path 
                    d="M 288 0 L 288 12 M 288 12 L 64 12 L 64 48 M 288 12 L 210 12 L 210 48 M 288 12 L 366 12 L 366 48 M 288 12 L 512 12 L 512 48" 
                    stroke="url(#lineGrad)" 
                    strokeWidth="2.5" 
                    fill="none" 
                    className="shimmer-path"
                    style={{ strokeDasharray: '8 4' }}
                  />
                )}
              </svg>
            </div>

            {/* Parallel Layer: Agents 2, 3, 4, 5 */}
            <div className="grid grid-cols-4 gap-3 w-full z-10 relative">
              <AgentNode 
                agent={agents["Resource Allocation Agent"]} 
                styles={getAgentCardStyles(agents["Resource Allocation Agent"].status)}
                compact
              />
              <AgentNode 
                agent={agents["Timeline Planning Agent"]} 
                styles={getAgentCardStyles(agents["Timeline Planning Agent"].status)}
                compact
              />
              <AgentNode 
                agent={agents["Cost Estimation Agent"]} 
                styles={getAgentCardStyles(agents["Cost Estimation Agent"].status)}
                compact
              />
              <AgentNode 
                agent={agents["Risk Analysis Agent"]} 
                styles={getAgentCardStyles(agents["Risk Analysis Agent"].status)}
                compact
              />
            </div>

            {/* Converge connection line SVG */}
            <div className="w-full h-12 relative">
              <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
                <path 
                  d="M 64 0 L 64 36 L 288 36 L 288 48 M 210 0 L 210 36 L 288 36 M 366 0 L 366 36 L 288 36 M 512 0 L 512 36 L 288 36" 
                  stroke="rgba(56, 169, 248, 0.2)" 
                  strokeWidth="2" 
                  fill="none" 
                />
                {isProcessing && (
                  <path 
                    d="M 64 0 L 64 36 L 288 36 L 288 48 M 210 0 L 210 36 L 288 36 M 366 0 L 366 36 L 288 36 M 512 0 L 512 36 L 288 36" 
                    stroke="url(#lineGrad)" 
                    strokeWidth="2.5" 
                    fill="none" 
                    className="shimmer-path"
                    style={{ strokeDasharray: '8 4' }}
                  />
                )}
              </svg>
            </div>

            {/* AGENT 6: Executive Synthesis */}
            <div className="w-full flex justify-center z-10">
              <AgentNode 
                agent={agents["Executive Report Agent"]} 
                styles={getAgentCardStyles(agents["Executive Report Agent"].status)}
              />
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}

// Nodes Subcomponent
interface AgentNodeProps {
  agent: AgentState;
  styles: string;
  compact?: boolean;
}

function AgentNode({ agent, styles, compact = false }: AgentNodeProps) {
  const Icon = agent.icon;
  
  return (
    <div 
      className={`glass-panel border p-4.5 rounded-2xl flex flex-col justify-between transition-all duration-300 w-full text-left relative overflow-hidden ${styles} ${
        compact ? 'h-[140px]' : 'max-w-md h-[115px]'
      }`}
    >
      {/* Background execution glow shimmer */}
      {agent.status === 'running' && (
        <div className="absolute inset-0 shimmer-bg pointer-events-none opacity-20"></div>
      )}

      <div>
        <div className="flex items-center justify-between gap-1.5">
          <div className="flex items-center gap-2 truncate">
            <div className={`p-1.5 rounded-lg ${
              agent.status === 'completed' 
                ? 'bg-emerald-500/10 text-emerald-400' 
                : agent.status === 'running' 
                  ? 'bg-brand-500/10 text-brand-400 animate-pulse' 
                  : 'bg-slate-800/50 text-slate-500'
            }`}>
              <Icon className="w-4 h-4 shrink-0" />
            </div>
            <h4 className="text-[12px] font-bold text-slate-200 truncate tracking-tight uppercase">
              {compact ? agent.name.replace(" Agent", "") : agent.name}
            </h4>
          </div>
          
          <div className="shrink-0">
            {agent.status === 'completed' && <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400" />}
            {agent.status === 'running' && <Loader2 className="w-4.5 h-4.5 text-brand-400 animate-spin" />}
            {agent.status === 'failed' && <AlertCircle className="w-4.5 h-4.5 text-rose-400 animate-bounce" />}
          </div>
        </div>

        <p className="text-[10px] text-slate-400 mt-2 font-medium leading-relaxed overflow-hidden h-[36px] line-clamp-2">
          {agent.message}
        </p>
      </div>

      {/* Progress slider bar */}
      <div className="w-full mt-2.5">
        <div className="flex justify-between items-center mb-1 text-[9px] font-bold text-slate-500">
          <span>STATUS</span>
          <span className={agent.status === 'running' ? 'text-brand-400 glow-text' : ''}>
            {agent.status.toUpperCase()} ({agent.progress}%)
          </span>
        </div>
        <div className="w-full h-1 bg-slate-950 rounded-full overflow-hidden">
          <motion.div 
            className={`h-full ${
              agent.status === 'completed' 
                ? 'bg-emerald-400' 
                : agent.status === 'failed' 
                  ? 'bg-rose-400' 
                  : 'bg-gradient-to-r from-brand-500 to-brand-300'
            }`}
            initial={{ width: 0 }}
            animate={{ width: `${agent.progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>
    </div>
  );
}
