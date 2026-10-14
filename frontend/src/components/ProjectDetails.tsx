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
  PieChart as ChartIcon,
  Sparkles,
  Loader2,
  UserCheck,
  Mail
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
  onAssignTasks?: (projectName: string) => void;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl shadow-xl">
        <p className="font-bold text-slate-200">{payload[0].name}</p>
        <p className="text-slate-400 mt-1.5 text-xs">
          Allocated Cost: <span className="text-emerald-400 font-extrabold ml-1">${Number(payload[0].value).toLocaleString()}</span>
        </p>
      </div>
    );
  }
  return null;
};

export default function ProjectDetails({ project, onBack, onAssignTasks }: ProjectDetailsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'qualification' | 'prebid' | 'approvals' | 'proposal' | 'resources' | 'timeline' | 'risks' | 'policies' | 'outcomes'>('overview');
  const [qualification, setQualification] = useState<any>(null);
  const [qualLoading, setQualLoading] = useState<boolean>(false);
  const [qualDeciding, setQualDeciding] = useState<boolean>(false);
  const [deliveryOwnerInput, setDeliveryOwnerInput] = useState<string>('');
  const [assigningOwner, setAssigningOwner] = useState<boolean>(false);

  const [bidDocuments, setBidDocuments] = useState<any[]>([]);
  const [bidDocNotes, setBidDocNotes] = useState<Record<number, string>>({});
  const [bidDocUpdating, setBidDocUpdating] = useState<number | null>(null);

  const [deliveryReviews, setDeliveryReviews] = useState<Record<string, any>>({});
  const [deliveryReviewSubmitting, setDeliveryReviewSubmitting] = useState<string | null>(null);
  const [deliveryReviewNotes, setDeliveryReviewNotes] = useState<Record<string, string>>({});

  const [outcomes, setOutcomes] = useState<any>(null);
  const [outcomesLoading, setOutcomesLoading] = useState<boolean>(false);
  const [winLossReason, setWinLossReason] = useState<string>('');
  const [winLossSubmitting, setWinLossSubmitting] = useState<string | null>(null);
  const [actualsCostInput, setActualsCostInput] = useState<string>('');
  const [actualsWeeksInput, setActualsWeeksInput] = useState<string>('');
  const [actualsNotes, setActualsNotes] = useState<string>('');
  const [actualsSubmitting, setActualsSubmitting] = useState<boolean>(false);
  const [bidHoursInput, setBidHoursInput] = useState<string>('');
  const [bidRateInput, setBidRateInput] = useState<string>('150');
  const [bidCostNotes, setBidCostNotes] = useState<string>('');
  const [bidCostSubmitting, setBidCostSubmitting] = useState<boolean>(false);

  const [contractStatus, setContractStatus] = useState<any>(null);
  const [contractStatusNotes, setContractStatusNotes] = useState<string>('');
  const [contractStatusSubmitting, setContractStatusSubmitting] = useState<string | null>(null);

  const [timelineRevisions, setTimelineRevisions] = useState<any[]>([]);
  const [adjustTriggerType, setAdjustTriggerType] = useState<string>('');
  const [adjustAffectedPhase, setAdjustAffectedPhase] = useState<string>('');
  const [adjustDeltaWeeks, setAdjustDeltaWeeks] = useState<string>('');
  const [adjustReason, setAdjustReason] = useState<string>('');
  const [adjustSubmitting, setAdjustSubmitting] = useState<boolean>(false);
  const [adjustResult, setAdjustResult] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [preBidQuestions, setPreBidQuestions] = useState<any[]>([]);
  const [preBidLoading, setPreBidLoading] = useState<boolean>(false);
  const [preBidAnswers, setPreBidAnswers] = useState<Record<number, string>>({});
  const [preBidSubmitting, setPreBidSubmitting] = useState<number | null>(null);
  const [preBidFinalizing, setPreBidFinalizing] = useState<boolean>(false);
  const [requirementsV2, setRequirementsV2] = useState<any>(null);

  const [emailDraft, setEmailDraft] = useState<{ to_email: string; subject: string; body: string; is_threaded_reply: boolean; original_subject?: string } | null>(null);
  const [emailDraftLoading, setEmailDraftLoading] = useState<boolean>(false);
  const [emailSendingPreBid, setEmailSendingPreBid] = useState<boolean>(false);
  const [emailSentStatus, setEmailSentStatus] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [fetchAnswersLoading, setFetchAnswersLoading] = useState<boolean>(false);
  const [fetchAnswersResult, setFetchAnswersResult] = useState<any>(null);
  const [finalizeQualNotice, setFinalizeQualNotice] = useState<string | null>(null);

  const [proposalEmailDraft, setProposalEmailDraft] = useState<{ to_email: string; subject: string; body: string; is_threaded_reply: boolean; original_subject?: string } | null>(null);
  const [proposalDraftLoading, setProposalDraftLoading] = useState<boolean>(false);
  const [proposalSending, setProposalSending] = useState<boolean>(false);
  const [proposalSentStatus, setProposalSentStatus] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [proposalRevisions, setProposalRevisions] = useState<any[]>([]);
  const [clientFeedbackInput, setClientFeedbackInput] = useState<string>('');
  const [fetchResponseLoading, setFetchResponseLoading] = useState<boolean>(false);
  const [proposalResponseResult, setProposalResponseResult] = useState<any>(null);
  const [changeDecisions, setChangeDecisions] = useState<{ change: string; decision: string; note: string; price_adjustment_percent: string }[]>([]);
  const [draftingReply, setDraftingReply] = useState<boolean>(false);
  const [replyDraft, setReplyDraft] = useState<{ to_email: string; subject: string; body: string } | null>(null);
  const [replySending, setReplySending] = useState<boolean>(false);
  const [replySentStatus, setReplySentStatus] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [approvals, setApprovals] = useState<any[]>([]);
  const [approvalsLoading, setApprovalsLoading] = useState<boolean>(false);
  const [approvalResolving, setApprovalResolving] = useState<number | null>(null);
  const [approvalPriceAdjustments, setApprovalPriceAdjustments] = useState<Record<number, string>>({});
  const [signoff, setSignoff] = useState<any>(null);
  const [signoffSubmitting, setSignoffSubmitting] = useState<boolean>(false);
  const [signoffNotes, setSignoffNotes] = useState<string>('');
  const [isApproved, setIsApproved] = useState<boolean>(!!project?.budget_approved);
  const [showEmailForm, setShowEmailForm] = useState<boolean>(false);
  const [emailInput, setEmailInput] = useState<string>(project?.email_metadata?.sender || '');
  const [emailSending, setEmailSending] = useState<boolean>(false);
  const [emailStatus, setEmailStatus] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [policies, setPolicies] = useState<any[]>([]);
  const [loadingExtras, setLoadingExtras] = useState<boolean>(false);

  // Inline "Assign Worker" flow on each recommended role card (RAG retrieval + LLM reranking)
  const [allWorkers, setAllWorkers] = useState<any[] | null>(null);
  const [expandedRoleIdx, setExpandedRoleIdx] = useState<number | null>(null);
  const [roleMatches, setRoleMatches] = useState<Record<number, { worker_id: string; score: number; reasons: string[] }[]>>({});
  const [roleMatching, setRoleMatching] = useState<number | null>(null);
  const [roleAssigning, setRoleAssigning] = useState<string | null>(null);
  const [roleAssigned, setRoleAssigned] = useState<Record<number, { workerId: string; name: string }>>({});

  const toggleAssignForRole = async (idx: number, member: any) => {
    if (expandedRoleIdx === idx) {
      setExpandedRoleIdx(null);
      return;
    }
    setExpandedRoleIdx(idx);
    if (roleMatches[idx]) return; // already fetched

    setRoleMatching(idx);
    try {
      let workers = allWorkers;
      if (!workers) {
        const wRes = await fetch('/api/workers');
        workers = wRes.ok ? await wRes.json() : [];
        setAllWorkers(workers);
      }
      const task = `${member.role}: ${member.key_responsibility || ''}`;
      const res = await fetch('/api/match-workers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, workers })
      });
      if (!res.ok) throw new Error('Matching request failed.');
      const data = await res.json();
      const top5 = (data.matches || [])
        .filter((m: any) => m.score > 0)
        .sort((a: any, b: any) => b.score - a.score)
        .slice(0, 5);
      setRoleMatches(prev => ({ ...prev, [idx]: top5 }));
    } catch (err) {
      console.error(err);
      setRoleMatches(prev => ({ ...prev, [idx]: [] }));
    } finally {
      setRoleMatching(null);
    }
  };

  const handleAssignToRole = async (idx: number, member: any, workerId: string) => {
    const projectName = project.project_overview?.project_name || project.project_name;
    const worker = allWorkers?.find((w: any) => w.id === workerId);
    setRoleAssigning(workerId);
    try {
      const task = `${member.role}: ${member.key_responsibility || ''}`;
      const res = await fetch('/api/assign-worker', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_name: projectName, task, worker_id: workerId })
      });
      if (!res.ok) throw new Error('Assignment failed.');
      setRoleAssigned(prev => ({ ...prev, [idx]: { workerId, name: worker?.name || workerId } }));
    } catch (err) {
      console.error(err);
      alert('Failed to assign worker.');
    } finally {
      setRoleAssigning(null);
    }
  };

  React.useEffect(() => {
    const fetchExtras = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      setLoadingExtras(true);
      try {
        const encoded = encodeURIComponent(pName);
        const polRes = await fetch(`/api/project/${encoded}/policies`);
        if (polRes.ok) setPolicies(await polRes.json());
      } catch (err) {
        console.error("Error loading project extras:", err);
      } finally {
        setLoadingExtras(false);
      }
    };
    fetchExtras();

    const fetchQualification = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      try {
        const res = await fetch(`/api/qualify-bid/${encodeURIComponent(pName)}`);
        if (res.ok) setQualification(await res.json());
        else setQualification(null);
      } catch (err) {
        console.error("Error loading qualification record:", err);
      }
    };
    fetchQualification();

    const fetchPreBid = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      try {
        const [qRes, vRes] = await Promise.all([
          fetch(`/api/pre-bid-questions/${encodeURIComponent(pName)}`),
          fetch(`/api/requirements/${encodeURIComponent(pName)}/versions`)
        ]);
        if (qRes.ok) setPreBidQuestions(await qRes.json());
        if (vRes.ok) {
          const v = await vRes.json();
          setRequirementsV2(v.v2 || null);
        }
      } catch (err) {
        console.error("Error loading pre-bid questions:", err);
      }
    };
    fetchPreBid();

    const fetchApprovals = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      try {
        const [aRes, sRes] = await Promise.all([
          fetch(`/api/approvals/${encodeURIComponent(pName)}`),
          fetch(`/api/delivery-signoff/${encodeURIComponent(pName)}`)
        ]);
        if (aRes.ok) setApprovals(await aRes.json());
        if (sRes.ok) setSignoff(await sRes.json());
      } catch (err) {
        console.error("Error loading approvals/signoff:", err);
      }
    };
    fetchApprovals();

    const fetchBidDocuments = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      try {
        const res = await fetch(`/api/bid-documents/${encodeURIComponent(pName)}`);
        if (res.ok) setBidDocuments(await res.json());
      } catch (err) {
        console.error("Error loading bid documents:", err);
      }
    };
    fetchBidDocuments();

    const fetchDeliveryReviews = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      try {
        const res = await fetch(`/api/delivery-review/${encodeURIComponent(pName)}`);
        if (res.ok) setDeliveryReviews(await res.json());
      } catch (err) {
        console.error("Error loading delivery owner reviews:", err);
      }
    };
    fetchDeliveryReviews();

    const fetchOutcomes = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      setOutcomesLoading(true);
      try {
        const res = await fetch(`/api/outcomes/${encodeURIComponent(pName)}`);
        if (res.ok) {
          const data = await res.json();
          setOutcomes(data);
          if (data.actuals) {
            setActualsCostInput(String(data.actuals.actual_total_cost ?? ''));
            setActualsWeeksInput(String(data.actuals.actual_duration_weeks ?? ''));
          }
          if (data.bid_cost) {
            setBidHoursInput(String(data.bid_cost.internal_hours ?? ''));
            setBidRateInput(String(data.bid_cost.internal_hourly_rate ?? '150'));
          }
        }
      } catch (err) {
        console.error("Error loading project outcomes:", err);
      } finally {
        setOutcomesLoading(false);
      }
    };
    fetchOutcomes();

    const fetchProposalRevisions = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      try {
        const res = await fetch(`/api/proposal-revisions/${encodeURIComponent(pName)}`);
        if (res.ok) setProposalRevisions(await res.json());
      } catch (err) {
        console.error("Error loading proposal revisions:", err);
      }
    };
    fetchProposalRevisions();

    const fetchContractStatus = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      try {
        const res = await fetch(`/api/contract-status/${encodeURIComponent(pName)}`);
        if (res.ok) setContractStatus(await res.json());
      } catch (err) {
        console.error("Error loading contract status:", err);
      }
    };
    fetchContractStatus();

    const fetchTimelineRevisions = async () => {
      const pName = project.project_overview?.project_name || project.project_name;
      if (!pName) return;
      try {
        const res = await fetch(`/api/project/${encodeURIComponent(pName)}/timeline/revisions`);
        if (res.ok) setTimelineRevisions(await res.json());
      } catch (err) {
        console.error("Error loading timeline revisions:", err);
      }
    };
    fetchTimelineRevisions();
  }, [project]);

  const generateApprovals = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setApprovalsLoading(true);
    try {
      const res = await fetch(`/api/approvals/${encodeURIComponent(pName)}/generate`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to scan for approval concerns.');
      setApprovals(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to scan for approval concerns. Requirements v1 must exist first.');
    } finally {
      setApprovalsLoading(false);
    }
  };

  const resolveApproval = async (approvalId: number, status: 'Approved' | 'Rejected') => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setApprovalResolving(approvalId);
    try {
      const adjustmentRaw = approvalPriceAdjustments[approvalId];
      const adjustment = adjustmentRaw ? parseFloat(adjustmentRaw) : undefined;
      const res = await fetch(`/api/approvals/${encodeURIComponent(pName)}/${approvalId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status,
          resolved_by: 'Reviewer',
          ...(adjustment && !isNaN(adjustment) ? { price_adjustment_percent: adjustment } : {})
        })
      });
      if (!res.ok) throw new Error('Failed to resolve approval.');
      setApprovals(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to resolve approval.');
    } finally {
      setApprovalResolving(null);
    }
  };

  const submitSignoff = async (status: 'Approved' | 'Rejected') => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setSignoffSubmitting(true);
    try {
      const res = await fetch(`/api/delivery-signoff/${encodeURIComponent(pName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, signed_by: 'Delivery Owner', notes: signoffNotes })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to record sign-off.');
      }
      setSignoff(await res.json());
    } catch (err: any) {
      console.error(err);
      alert(err.message || 'Failed to record sign-off.');
    } finally {
      setSignoffSubmitting(false);
    }
  };

  const generatePreBidQuestions = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setPreBidLoading(true);
    try {
      const res = await fetch(`/api/pre-bid-questions/${encodeURIComponent(pName)}/generate`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to generate questions.');
      setPreBidQuestions(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to generate pre-bid questions. Requirements v1 must exist first (re-run analysis if this is an older project).');
    } finally {
      setPreBidLoading(false);
    }
  };

  const submitPreBidAnswer = async (questionId: number) => {
    const pName = project.project_overview?.project_name || project.project_name;
    const answer = preBidAnswers[questionId];
    if (!pName || !answer?.trim()) return;
    setPreBidSubmitting(questionId);
    try {
      const res = await fetch(`/api/pre-bid-questions/${encodeURIComponent(pName)}/${questionId}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_answer: answer.trim() })
      });
      if (!res.ok) throw new Error('Failed to save answer.');
      setPreBidQuestions(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to save the answer.');
    } finally {
      setPreBidSubmitting(null);
    }
  };

  const finalizePreBidAnswers = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setPreBidFinalizing(true);
    try {
      const res = await fetch(`/api/pre-bid-questions/${encodeURIComponent(pName)}/finalize`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to finalize requirements v2.');
      const data = await res.json();
      setRequirementsV2(data.requirements_v2);
      if (data.qualification) {
        setQualification(data.qualification);
        setFinalizeQualNotice(`Qualification re-checked: now ${data.qualification.recommendation}.`);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to finalize requirements v2.');
    } finally {
      setPreBidFinalizing(false);
    }
  };

  const composePreBidEmailDraft = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setEmailDraftLoading(true);
    setEmailSentStatus(null);
    try {
      const res = await fetch(`/api/pre-bid-questions/${encodeURIComponent(pName)}/draft-email`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to draft email.');
      }
      setEmailDraft(await res.json());
    } catch (err: any) {
      console.error(err);
      alert(err.message || 'Failed to draft email.');
    } finally {
      setEmailDraftLoading(false);
    }
  };

  const sendPreBidEmail = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName || !emailDraft) return;
    setEmailSendingPreBid(true);
    setEmailSentStatus(null);
    try {
      const res = await fetch(`/api/pre-bid-questions/${encodeURIComponent(pName)}/send-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_email: emailDraft.to_email, subject: emailDraft.subject, body: emailDraft.body })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to send email.');
      setEmailSentStatus({
        text: data.sent_in_thread ? 'Sent to client in the original email thread.' : 'Sent to client.',
        type: 'success'
      });
    } catch (err: any) {
      console.error(err);
      setEmailSentStatus({ text: err.message || 'Failed to send email.', type: 'error' });
    } finally {
      setEmailSendingPreBid(false);
    }
  };

  const fetchPreBidAnswersFromMail = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setFetchAnswersLoading(true);
    try {
      const res = await fetch(`/api/pre-bid-questions/${encodeURIComponent(pName)}/fetch-answers`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch answers from mail.');
      setFetchAnswersResult(data);
      if (data.questions) setPreBidQuestions(data.questions);
      if (data.qualification) setQualification(data.qualification);
      if (data.requirements_v2) setRequirementsV2(data.requirements_v2);
    } catch (err: any) {
      console.error(err);
      alert(err.message || 'Failed to fetch answers from mail.');
    } finally {
      setFetchAnswersLoading(false);
    }
  };

  const composeProposalEmailDraft = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setProposalDraftLoading(true);
    setProposalSentStatus(null);
    try {
      const res = await fetch(`/api/project/${encodeURIComponent(pName)}/proposal-email/draft`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to draft proposal email.');
      }
      setProposalEmailDraft(await res.json());
    } catch (err: any) {
      console.error(err);
      alert(err.message || 'Failed to draft proposal email.');
    } finally {
      setProposalDraftLoading(false);
    }
  };

  const sendProposalEmail = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName || !proposalEmailDraft) return;
    setProposalSending(true);
    setProposalSentStatus(null);
    try {
      const res = await fetch(`/api/project/${encodeURIComponent(pName)}/proposal-email/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_email: proposalEmailDraft.to_email, subject: proposalEmailDraft.subject, body: proposalEmailDraft.body,
          client_feedback: clientFeedbackInput
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to send proposal.');
      setProposalSentStatus({
        text: (data.sent_in_thread ? 'Proposal sent to client in the original email thread.' : 'Proposal sent to client.') + ` (version ${data.version})`,
        type: 'success'
      });
      setClientFeedbackInput('');
      const revRes = await fetch(`/api/proposal-revisions/${encodeURIComponent(pName)}`);
      if (revRes.ok) setProposalRevisions(await revRes.json());
    } catch (err: any) {
      console.error(err);
      setProposalSentStatus({ text: err.message || 'Failed to send proposal.', type: 'error' });
    } finally {
      setProposalSending(false);
    }
  };

  const fetchProposalResponseFromMail = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setFetchResponseLoading(true);
    try {
      const res = await fetch(`/api/project/${encodeURIComponent(pName)}/proposal-email/fetch-response`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch client response from mail.');
      setProposalResponseResult(data);
      // Initialize one undecided decision slot per requested change, and a combined note for history
      if (data.found && data.response_type === 'Revision Requested' && Array.isArray(data.requested_changes)) {
        setChangeDecisions(data.requested_changes.map((c: string) => ({ change: c, decision: '', note: '', price_adjustment_percent: '' })));
        setClientFeedbackInput(data.requested_changes.join('; '));
      }
    } catch (err: any) {
      console.error(err);
      alert(err.message || 'Failed to fetch client response from mail.');
    } finally {
      setFetchResponseLoading(false);
    }
  };

  const draftReplyWithDecisions = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    const undecided = changeDecisions.filter(d => !d.decision);
    if (undecided.length > 0) {
      alert('Please decide Accept, Decline, or Partial on every requested change before drafting a reply.');
      return;
    }
    setDraftingReply(true);
    setReplySentStatus(null);
    try {
      const decisionsPayload = changeDecisions.map(d => ({
        change: d.change,
        decision: d.decision,
        note: d.note,
        price_adjustment_percent: d.price_adjustment_percent.trim() ? parseFloat(d.price_adjustment_percent) : null
      }));
      const res = await fetch(`/api/project/${encodeURIComponent(pName)}/proposal-email/draft-reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decisions: decisionsPayload })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to draft reply.');
      setReplyDraft(data);
    } catch (err: any) {
      console.error(err);
      alert(err.message || 'Failed to draft reply.');
    } finally {
      setDraftingReply(false);
    }
  };

  const sendClientReply = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName || !replyDraft) return;
    setReplySending(true);
    setReplySentStatus(null);
    try {
      const res = await fetch(`/api/project/${encodeURIComponent(pName)}/proposal-email/send-reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(replyDraft)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to send reply.');
      setReplySentStatus({
        text: data.sent_in_thread ? 'Reply sent to client in the original thread.' : 'Reply sent to client.',
        type: 'success'
      });
      setProposalResponseResult(null);
      setChangeDecisions([]);
      const revRes = await fetch(`/api/proposal-revisions/${encodeURIComponent(pName)}`);
      if (revRes.ok) setProposalRevisions(await revRes.json());
    } catch (err: any) {
      console.error(err);
      setReplySentStatus({ text: err.message || 'Failed to send reply.', type: 'error' });
    } finally {
      setReplySending(false);
    }
  };

  const runQualificationCheck = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setQualLoading(true);
    try {
      const res = await fetch(`/api/qualify-bid/${encodeURIComponent(pName)}`, { method: 'POST' });
      if (!res.ok) throw new Error('Qualification check failed.');
      setQualification(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to run qualification check.');
    } finally {
      setQualLoading(false);
    }
  };

  const submitBidDecision = async (decision: 'Go' | 'No-Go') => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setQualDeciding(true);
    try {
      const res = await fetch(`/api/qualify-bid/${encodeURIComponent(pName)}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, decided_by: 'Delivery Owner' })
      });
      if (!res.ok) throw new Error('Failed to record decision.');
      setQualification(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to record bid decision.');
    } finally {
      setQualDeciding(false);
    }
  };

  const assignDeliveryOwner = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName || !deliveryOwnerInput.trim()) return;
    setAssigningOwner(true);
    try {
      const res = await fetch(`/api/qualify-bid/${encodeURIComponent(pName)}/assign-owner`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ owner_name: deliveryOwnerInput.trim() })
      });
      if (!res.ok) throw new Error('Failed to assign delivery owner.');
      setQualification(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to assign delivery owner.');
    } finally {
      setAssigningOwner(false);
    }
  };

  const updateBidDocumentStatus = async (docId: number, status: 'Pending' | 'Ready' | 'Not Applicable') => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setBidDocUpdating(docId);
    try {
      const res = await fetch(`/api/bid-documents/${encodeURIComponent(pName)}/${docId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, notes: bidDocNotes[docId] || '' })
      });
      if (!res.ok) throw new Error('Failed to update bid document status.');
      setBidDocuments(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to update bid document status.');
    } finally {
      setBidDocUpdating(null);
    }
  };

  const submitDeliveryReview = async (stage: 'solutioning' | 'pricing') => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setDeliveryReviewSubmitting(stage);
    try {
      const res = await fetch(`/api/delivery-review/${encodeURIComponent(pName)}/${stage}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewed_by: qualification?.assigned_delivery_owner || 'Delivery Owner',
          notes: deliveryReviewNotes[stage] || ''
        })
      });
      if (!res.ok) throw new Error('Failed to record review.');
      setDeliveryReviews(await res.json());
    } catch (err) {
      console.error(err);
      alert('Failed to record delivery owner review.');
    } finally {
      setDeliveryReviewSubmitting(null);
    }
  };

  const submitWinLoss = async (status: 'Won' | 'Lost', reasonOverride?: string) => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setWinLossSubmitting(status);
    try {
      const res = await fetch(`/api/win-loss/${encodeURIComponent(pName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, reason: reasonOverride ?? winLossReason, decided_by: 'Delivery Owner' })
      });
      if (!res.ok) throw new Error('Failed to record win/loss decision.');
      const wl = await res.json();
      setOutcomes((prev: any) => ({ ...prev, win_loss: wl }));
    } catch (err) {
      console.error(err);
      alert('Failed to record win/loss decision.');
    } finally {
      setWinLossSubmitting(null);
    }
  };

  const submitActuals = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName || !actualsCostInput || !actualsWeeksInput) return;
    setActualsSubmitting(true);
    try {
      const res = await fetch(`/api/project-actuals/${encodeURIComponent(pName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          actual_total_cost: parseFloat(actualsCostInput),
          actual_duration_weeks: parseFloat(actualsWeeksInput),
          notes: actualsNotes,
          logged_by: 'Delivery Owner'
        })
      });
      if (!res.ok) throw new Error('Failed to log actuals.');
      const actuals = await res.json();
      setOutcomes((prev: any) => ({ ...prev, actuals }));
    } catch (err) {
      console.error(err);
      alert('Failed to log actuals.');
    } finally {
      setActualsSubmitting(false);
    }
  };

  const submitBidCost = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName || !bidHoursInput) return;
    setBidCostSubmitting(true);
    try {
      const res = await fetch(`/api/bid-cost/${encodeURIComponent(pName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          internal_hours: parseFloat(bidHoursInput),
          internal_hourly_rate: parseFloat(bidRateInput) || 150,
          notes: bidCostNotes,
          logged_by: 'BD Team'
        })
      });
      if (!res.ok) throw new Error('Failed to log cost of bidding.');
      const bidCost = await res.json();
      setOutcomes((prev: any) => ({ ...prev, bid_cost: bidCost }));
    } catch (err) {
      console.error(err);
      alert('Failed to log cost of bidding.');
    } finally {
      setBidCostSubmitting(false);
    }
  };

  const submitContractStatus = async (status: 'Sent for Signature' | 'Signed' | 'Rejected') => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName) return;
    setContractStatusSubmitting(status);
    try {
      const res = await fetch(`/api/contract-status/${encodeURIComponent(pName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, notes: contractStatusNotes, updated_by: 'Delivery Owner' })
      });
      if (!res.ok) throw new Error('Failed to update contract status.');
      setContractStatus(await res.json());
      setContractStatusNotes('');
    } catch (err) {
      console.error(err);
      alert('Failed to update contract status.');
    } finally {
      setContractStatusSubmitting(null);
    }
  };

  const submitTimelineAdjustment = async () => {
    const pName = project.project_overview?.project_name || project.project_name;
    if (!pName || !adjustTriggerType || !adjustAffectedPhase || !adjustDeltaWeeks.trim() || !adjustReason.trim()) return;
    setAdjustSubmitting(true);
    setAdjustResult(null);
    try {
      const res = await fetch(`/api/project/${encodeURIComponent(pName)}/timeline/adjust`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trigger_type: adjustTriggerType,
          affected_phase: adjustAffectedPhase,
          delta_weeks: parseFloat(adjustDeltaWeeks),
          reason: adjustReason,
          applied_by: 'Delivery Owner'
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to apply timeline adjustment.');
      const impact = data.cost_impact;
      setAdjustResult({
        text: impact
          ? `Timeline updated. Cost impact: ${impact > 0 ? '+' : ''}$${impact.toLocaleString()}`
          : 'Timeline updated. No cost impact from this change.',
        type: 'success'
      });
      setAdjustTriggerType(''); setAdjustAffectedPhase(''); setAdjustDeltaWeeks(''); setAdjustReason('');
      // Refresh the project's own in-memory timeline/budget so the phase cards re-render immediately
      if (project.timeline) project.timeline = data.timeline;
      if (data.budget && project.budget) project.budget = data.budget;
      const revRes = await fetch(`/api/project/${encodeURIComponent(pName)}/timeline/revisions`);
      if (revRes.ok) setTimelineRevisions(await revRes.json());
    } catch (err: any) {
      console.error(err);
      setAdjustResult({ text: err.message || 'Failed to apply timeline adjustment.', type: 'error' });
    } finally {
      setAdjustSubmitting(false);
    }
  };

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

  const formatCurrency = (val: number) => {
    return typeof val === 'number' ? `$${val.toLocaleString()}` : val;
  };

  const getResourceSchedule = (role: string): any => {
    const schedule = project.timeline?.resource_schedule || [];
    return schedule.find((s: any) => s.role?.toLowerCase().trim() === role?.toLowerCase().trim());
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

  const getOwnerEmail = (): string => {
    const rawSender = project.email_metadata?.sender || '';
    const emailMatch = rawSender.match(/<([^>]+)>/);
    if (emailMatch && emailMatch[1]) {
      return emailMatch[1].trim();
    }
    return rawSender.trim() || 'client@company.com';
  };

  const rawBreakdown = project.budget?.breakdown || project.budget || {};
  const budgetData = [
    { name: 'Labor & Execution', value: rawBreakdown.development_cost || 0, color: '#38a9f8' },
    { name: 'Operational & Software', value: rawBreakdown.cloud_cost || 0, color: '#00c49f' },
    { name: 'Equipment & Facilities', value: rawBreakdown.infrastructure_cost || 0, color: '#ffbb28' },
    { name: 'Quality Control & QA', value: rawBreakdown.testing_cost || 0, color: '#ff8042' },
    { name: 'Admin & Operations', value: rawBreakdown.support_cost || 0, color: '#a78bfa' },
    { name: 'Contingency Buffer', value: rawBreakdown.buffer_cost || 0, color: '#f43f5e' }
  ].filter(item => item.value > 0);

  const totalCost = project.budget?.total_cost || 
                    (typeof project.budget === 'number' ? project.budget : 0);

  const targetBudget = parseBudget(project.project_overview?.budget);
  const budgetDeficit = targetBudget !== null && totalCost > targetBudget ? totalCost - targetBudget : 0;
  const isBudgetExceeded = budgetDeficit > 0;
  const isTargetBudgetMissing = targetBudget === null;

  const handleApprove = async () => {
    try {
      const res = await fetch('/api/project/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.project_overview?.project_name || project.project_name,
          approved: true
        })
      });
      if (res.ok) {
        setIsApproved(true);
        project.budget_approved = true;
      } else {
        alert("Failed to approve budget breakdown.");
      }
    } catch (err) {
      console.error(err);
      alert("Error approving budget.");
    }
  };

  const handleSendProposal = async (e: React.FormEvent) => {
    e.preventDefault();
    const recipient = project.email_metadata?.sender ? getOwnerEmail() : emailInput;
    if (!recipient.trim()) return;
    setEmailSending(true);
    setEmailStatus(null);
    try {
      const res = await fetch('/api/project/send-proposal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_email: recipient.trim(),
          project_name: project.project_overview?.project_name || project.project_name,
          client_name: project.project_overview?.client || "Client",
          budget_data: project.budget,
          timeline_weeks: project.project_overview?.duration || "16 Weeks"
        })
      });
      if (res.ok) {
        const data = await res.json();
        setEmailStatus({ text: data.message || "Proposal sent successfully!", type: 'success' });
        setTimeout(() => {
          setShowEmailForm(false);
          setEmailStatus(null);
        }, 4000);
      } else {
        const err = await res.json();
        setEmailStatus({ text: err.detail || "Failed to send proposal.", type: 'error' });
      }
    } catch (err) {
      console.error(err);
      setEmailStatus({ text: "Error dispatching proposal email. Check connection.", type: 'error' });
    } finally {
      setEmailSending(false);
    }
  };

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
            <span className="text-xs font-bold px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800/80 text-slate-400 uppercase tracking-widest">
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
      </div>

      {/* Tabs Selection Bar */}
      <div className="flex border-b border-slate-800/80 gap-6 overflow-x-auto scrollbar-none pb-1">
        {(['overview', 'qualification', 'prebid', 'resources', 'approvals', 'proposal', 'timeline', 'outcomes', 'risks', 'policies'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3.5 text-xs font-bold uppercase tracking-wider transition-all relative ${
              activeTab === tab
                ? 'text-brand-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {tab === 'prebid' ? 'Pre-Bid Q&A' : tab}
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
                  {project.technology_summary?.deliverables && project.technology_summary.deliverables.length > 0 ? (
                    project.technology_summary.deliverables.map((item: string, idx: number) => (
                      <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/30 border border-slate-800/40 text-xs">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span className="text-slate-300 font-medium leading-normal">{item}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-500 italic p-2 col-span-2">No deliverables specified in the SOW.</div>
                  )}
                </div>
              </div>

              {/* Architecture Proposal */}
              {project.architecture_proposal && (
                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Layers className="w-5 h-5 text-brand-400" />
                    Solution Architecture
                  </h3>
                  <p className="text-xs text-brand-300 font-semibold">{project.architecture_proposal.architecture_style}</p>

                  {project.architecture_proposal.components?.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {project.architecture_proposal.components.map((c: any, i: number) => (
                        <div key={i} className="text-xs bg-slate-900/30 border border-slate-800/40 p-3 rounded-xl">
                          <p className="text-white font-bold">{c.name}</p>
                          <p className="text-slate-400 mt-0.5">{c.responsibility}</p>
                          <p className="text-brand-400 text-[10px] font-semibold mt-1">{c.technology}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {project.architecture_proposal.data_flow && (
                    <p className="text-xs text-slate-400 leading-relaxed">
                      <span className="font-bold text-slate-300">Data Flow: </span>
                      {project.architecture_proposal.data_flow}
                    </p>
                  )}

                  {project.architecture_proposal.key_design_decisions?.length > 0 && (
                    <ul className="space-y-1.5">
                      {project.architecture_proposal.key_design_decisions.map((d: string, i: number) => (
                        <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                          <ChevronRight className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-500" />
                          {d}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {/* Recommendations */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Compass className="w-5 h-5 text-brand-400" />
                  Strategic Delivery Recommendations
                </h3>
                <ul className="space-y-2.5">
                  {project.recommendations && project.recommendations.length > 0 ? (
                    project.recommendations.map((rec: string, idx: number) => (
                      <li key={idx} className="flex gap-3 text-xs text-slate-300">
                        <span className="w-5 h-5 rounded bg-brand-500/10 text-brand-400 flex items-center justify-center shrink-0 text-[10px] font-bold">
                          {idx + 1}
                        </span>
                        <span className="leading-relaxed mt-0.5">{rec}</span>
                      </li>
                    ))
                  ) : (
                    <div className="text-xs text-slate-500 italic p-2">No strategic recommendations generated.</div>
                  )}
                </ul>
              </div>

            </div>

            {/* Right Col: Technical Stack, constraints, dependencies */}
            <div className="lg:col-span-4 space-y-6">
              
              {/* Tech Stack */}
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Wrench className="w-5 h-5 text-brand-400" />
                  Core Stack & Competencies
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
                  <span className="font-bold text-slate-300">Delivery Strategy: </span>
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
                      {project.technology_summary?.constraints && project.technology_summary.constraints.length > 0 ? (
                        project.technology_summary.constraints.map((c: string, i: number) => (
                          <div key={i} className="text-xs text-slate-300 bg-slate-950/30 border border-slate-900 p-2.5 rounded-lg leading-relaxed">
                            • {c}
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-slate-500 italic p-2">No technical constraints identified.</div>
                      )}
                    </div>
                  </div>
                  <div className="border-t border-slate-800/50 pt-4">
                    <h4 className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">SOW Dependencies</h4>
                    <div className="space-y-2">
                      {project.technology_summary?.dependencies && project.technology_summary.dependencies.length > 0 ? (
                        project.technology_summary.dependencies.map((d: string, i: number) => (
                          <div key={i} className="text-xs text-slate-300 bg-slate-950/30 border border-slate-900 p-2.5 rounded-lg leading-relaxed">
                            • {d}
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-slate-500 italic p-2">No external dependencies specified.</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

            </div>

          </div>
        )}

        {/* Bid Qualification Tab */}
        {activeTab === 'qualification' && (
          <div className="space-y-6 max-w-3xl">
            {!qualification && (
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl text-center space-y-3">
                <HelpCircle className="w-8 h-8 text-slate-500 mx-auto" />
                <p className="text-sm text-slate-400">
                  No qualification check has been run for this bid yet. This deterministic check reviews the
                  submission deadline and mandatory certifications extracted from the SOW against your org's
                  actual capabilities — it does not use the LLM, so the same inputs always produce the same result.
                </p>
                <button
                  onClick={runQualificationCheck}
                  disabled={qualLoading}
                  className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-colors inline-flex items-center gap-2"
                >
                  {qualLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  Run Qualification Check
                </button>
              </div>
            )}

            {qualification && (
              <>
                <div className={`glass-panel p-6 rounded-2xl border ${
                  qualification.recommendation === 'Go' ? 'border-emerald-500/30 bg-emerald-950/10' :
                  qualification.recommendation === 'No-Go' ? 'border-rose-500/30 bg-rose-950/10' :
                  'border-amber-500/30 bg-amber-950/10'
                }`}>
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                      <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-1">System Recommendation</p>
                      <h3 className={`text-2xl font-extrabold ${
                        qualification.recommendation === 'Go' ? 'text-emerald-400' :
                        qualification.recommendation === 'No-Go' ? 'text-rose-400' : 'text-amber-400'
                      }`}>{qualification.recommendation}</h3>
                    </div>
                    <button
                      onClick={runQualificationCheck}
                      disabled={qualLoading}
                      className="text-[11px] font-bold text-slate-400 hover:text-white underline underline-offset-2"
                    >
                      {qualLoading ? 'Re-checking...' : 'Re-run check'}
                    </button>
                  </div>

                  {qualification.blocking_issues?.length > 0 && (
                    <div className="mt-4 space-y-1.5">
                      {qualification.blocking_issues.map((b: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-xs text-rose-200">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-400" />
                          {b}
                        </div>
                      ))}
                    </div>
                  )}
                  {qualification.reasoning?.length > 0 && (
                    <div className="mt-3 space-y-1.5">
                      {qualification.reasoning.map((r: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-xs text-slate-400">
                          <ChevronRight className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-500" />
                          {r}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4 mt-5 pt-5 border-t border-slate-800/60 text-xs">
                    <div>
                      <p className="text-slate-500 font-bold uppercase tracking-wide text-[10px] mb-1">Required Certifications</p>
                      <p className="text-slate-300">{qualification.required_certifications?.length ? qualification.required_certifications.join(', ') : 'None stated'}</p>
                    </div>
                    <div>
                      <p className="text-slate-500 font-bold uppercase tracking-wide text-[10px] mb-1">Missing Certifications</p>
                      <p className={qualification.missing_certifications?.length ? 'text-rose-400 font-semibold' : 'text-slate-300'}>
                        {qualification.missing_certifications?.length ? qualification.missing_certifications.join(', ') : 'None'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
                  <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-3">Human Decision</p>
                  {qualification.decision && qualification.decision !== 'Pending' ? (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className={`w-5 h-5 ${qualification.decision === 'Go' ? 'text-emerald-400' : 'text-rose-400'}`} />
                      <span className="text-white font-bold">{qualification.decision}</span>
                      <span className="text-slate-500 text-xs">
                        — decided by {qualification.decided_by} on {qualification.decided_at ? new Date(qualification.decided_at).toLocaleString() : ''}
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => submitBidDecision('Go')}
                        disabled={qualDeciding}
                        className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-colors"
                      >
                        Approve — Go
                      </button>
                      <button
                        onClick={() => submitBidDecision('No-Go')}
                        disabled={qualDeciding}
                        className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-colors"
                      >
                        Reject — No-Go
                      </button>
                    </div>
                  )}
                </div>

                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
                  <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-1">Delivery Owner</p>
                  <p className="text-[11px] text-slate-500 mb-3">
                    Assigned as soon as a bid qualifies — not just at final sign-off — so the person who'll actually
                    deliver this project tracks solutioning and pricing as it develops.
                  </p>
                  {qualification.assigned_delivery_owner ? (
                    <div className="flex items-center gap-2 text-sm">
                      <UserCheck className="w-4 h-4 text-brand-400" />
                      <span className="text-white font-bold">{qualification.assigned_delivery_owner}</span>
                      <span className="text-slate-500 text-xs">
                        — assigned {qualification.assigned_at ? new Date(qualification.assigned_at).toLocaleString() : ''}
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        placeholder="Delivery owner's name"
                        value={deliveryOwnerInput}
                        onChange={(e) => setDeliveryOwnerInput(e.target.value)}
                        className="flex-1 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                      />
                      <button
                        onClick={assignDeliveryOwner}
                        disabled={assigningOwner || !deliveryOwnerInput.trim()}
                        className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white text-xs font-bold rounded-lg shrink-0"
                      >
                        {assigningOwner ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Assign'}
                      </button>
                    </div>
                  )}
                </div>

              </>
            )}
          </div>
        )}

        {/* Pre-Bid Q&A Tab */}
        {activeTab === 'prebid' && (
          <div className="space-y-6 max-w-3xl">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Clarifying questions drafted from the raw SOW, to send back to the client before committing to a full plan.
              </p>
              <button
                onClick={generatePreBidQuestions}
                disabled={preBidLoading}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-colors inline-flex items-center gap-2 shrink-0"
              >
                {preBidLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {preBidQuestions.length > 0 ? 'Re-generate Questions' : 'Generate Questions'}
              </button>
            </div>

            {preBidQuestions.length === 0 && !preBidLoading && (
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl text-center text-sm text-slate-400">
                No pre-bid questions drafted yet.
              </div>
            )}

            {preBidQuestions.map((q) => (
              <div key={q.id} className="glass-panel border-slate-800/40 p-5 rounded-2xl space-y-3">
                <div className="flex items-start gap-2.5">
                  <HelpCircle className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                  <p className="text-sm text-white font-medium">{q.question}</p>
                </div>
                {q.status === 'Answered' ? (
                  <div className="ml-6 pl-4 border-l-2 border-emerald-500/30 text-xs text-slate-300 space-y-1">
                    <p className="text-emerald-400 font-bold uppercase tracking-wide text-[10px]">Client Answer</p>
                    <p>{q.client_answer}</p>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 ml-6">
                    <input
                      type="text"
                      placeholder="Paste the client's answer here..."
                      value={preBidAnswers[q.id] || ''}
                      onChange={(e) => setPreBidAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
                      className="flex-1 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                    />
                    <button
                      onClick={() => submitPreBidAnswer(q.id)}
                      disabled={preBidSubmitting === q.id || !preBidAnswers[q.id]?.trim()}
                      className="px-3 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-white text-xs font-bold rounded-lg shrink-0"
                    >
                      {preBidSubmitting === q.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Save'}
                    </button>
                  </div>
                )}
              </div>
            ))}

            {preBidQuestions.length > 0 && (
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-1">Requirements v2</p>
                    <p className="text-xs text-slate-400">
                      {requirementsV2
                        ? `Finalized with ${requirementsV2.clarifications?.length || 0} answered clarification(s). Re-finalize any time to pick up newly answered questions.`
                        : `${preBidQuestions.filter(q => q.status === 'Answered').length} of ${preBidQuestions.length} questions answered. v1 stays untouched either way.`}
                    </p>
                  </div>
                  <button
                    onClick={finalizePreBidAnswers}
                    disabled={preBidFinalizing || preBidQuestions.filter(q => q.status === 'Answered').length === 0}
                    className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-bold rounded-xl shrink-0"
                  >
                    {preBidFinalizing ? 'Finalizing...' : requirementsV2 ? 'Re-finalize v2' : 'Finalize as v2'}
                  </button>
                </div>
                {finalizeQualNotice && (
                  <p className="text-xs text-emerald-400 font-semibold mt-3 pt-3 border-t border-slate-800/50 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {finalizeQualNotice}
                  </p>
                )}
              </div>
            )}

            {/* Compile the still-pending pre-bid questions into a reviewable client email */}
            {preBidQuestions.filter(q => q.status === 'Pending').length > 0 && (
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-1">Send Questions to Client</p>
                    <p className="text-xs text-slate-400">
                      {preBidQuestions.filter(q => q.status === 'Pending').length} pending question(s) can be compiled into an email.
                    </p>
                  </div>
                  <div className="flex items-center gap-2.5 shrink-0">
                    <button
                      onClick={composePreBidEmailDraft}
                      disabled={emailDraftLoading}
                      className="px-4 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl inline-flex items-center gap-2"
                    >
                      {emailDraftLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                      {emailDraft ? 'Re-compose Draft' : 'Compose Email to Client'}
                    </button>
                    <button
                      onClick={fetchPreBidAnswersFromMail}
                      disabled={fetchAnswersLoading}
                      className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white text-xs font-bold rounded-xl inline-flex items-center gap-2"
                      title="Check the email thread for a client reply and match it to pending questions"
                    >
                      {fetchAnswersLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                      Fetch Answers from Mail
                    </button>
                  </div>
                </div>

                {fetchAnswersResult && (
                  <div className={`text-xs rounded-xl p-3.5 border ${
                    fetchAnswersResult.found
                      ? 'bg-emerald-950/20 border-emerald-500/20 text-emerald-200'
                      : 'bg-amber-950/20 border-amber-500/20 text-amber-200'
                  }`}>
                    {fetchAnswersResult.found ? (
                      <>
                        <p className="font-semibold">
                          {fetchAnswersResult.matched_count > 0
                            ? `Matched ${fetchAnswersResult.matched_count} answer(s) from the client's reply.`
                            : 'Found a reply, but could not confidently match it to any pending question.'}
                        </p>
                        {fetchAnswersResult.qualification && (
                          <p className="mt-1 text-slate-300">
                            Qualification re-checked: now <span className="font-bold">{fetchAnswersResult.qualification.recommendation}</span>.
                          </p>
                        )}
                      </>
                    ) : (
                      <p className="font-semibold">{fetchAnswersResult.message || 'No reply found in the thread yet.'}</p>
                    )}
                  </div>
                )}

                {emailDraft && (
                  <div className="space-y-3 pt-2 border-t border-slate-800/50">
                    {emailDraft.is_threaded_reply ? (
                      <p className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Will send as a reply in the original email thread ("{emailDraft.original_subject}")
                      </p>
                    ) : (
                      <p className="text-[10px] text-amber-400 font-semibold">
                        This project wasn't ingested from an email thread — this will send as a new, standalone email.
                      </p>
                    )}

                    <div>
                      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">To</label>
                      <input
                        type="email"
                        value={emailDraft.to_email}
                        onChange={(e) => setEmailDraft({ ...emailDraft, to_email: e.target.value })}
                        placeholder="client@company.com"
                        className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">Subject</label>
                      <input
                        type="text"
                        value={emailDraft.subject}
                        onChange={(e) => setEmailDraft({ ...emailDraft, subject: e.target.value })}
                        className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">Body</label>
                      <textarea
                        value={emailDraft.body}
                        onChange={(e) => setEmailDraft({ ...emailDraft, body: e.target.value })}
                        rows={10}
                        className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white leading-relaxed focus:outline-none focus:border-brand-500 font-mono"
                      />
                    </div>

                    {emailSentStatus?.type === 'error' && (
                      <p className="text-xs font-semibold text-rose-400">{emailSentStatus.text}</p>
                    )}

                    {emailSentStatus?.type === 'success' ? (
                      <div className="flex items-center justify-between gap-3 pt-1">
                        <p className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4" />
                          {emailSentStatus.text}
                        </p>
                        <button
                          onClick={() => { setEmailDraft(null); setEmailSentStatus(null); }}
                          className="px-4 py-2 text-slate-400 hover:text-white text-xs font-bold shrink-0"
                        >
                          Compose Another Email
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3">
                        <button
                          onClick={sendPreBidEmail}
                          disabled={emailSendingPreBid || !emailDraft.to_email.trim()}
                          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-bold rounded-xl inline-flex items-center gap-2"
                        >
                          {emailSendingPreBid ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                          {emailSendingPreBid ? 'Sending...' : 'Send to Client'}
                        </button>
                        <button
                          onClick={() => { setEmailDraft(null); setEmailSentStatus(null); }}
                          disabled={emailSendingPreBid}
                          className="px-4 py-2.5 text-slate-400 hover:text-white text-xs font-bold"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Approvals & Delivery Owner Sign-Off Tab */}
        {activeTab === 'approvals' && (
          <div className="space-y-6 max-w-3xl">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Concerns flagged from the SOW text (payment terms, security/compliance asks, legal clauses,
                certification gaps) and routed to the right internal stakeholder.
              </p>
              <button
                onClick={generateApprovals}
                disabled={approvalsLoading}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-colors inline-flex items-center gap-2 shrink-0"
              >
                {approvalsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {approvals.length > 0 ? 'Re-scan' : 'Scan for Concerns'}
              </button>
            </div>

            {approvals.length === 0 && !approvalsLoading && (
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl text-center text-sm text-slate-400">
                No approval concerns scanned yet.
              </div>
            )}

            {approvals.map((a) => (
              <div key={a.id} className="glass-panel border-slate-800/40 p-5 rounded-2xl space-y-2.5">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded bg-slate-900/80 border border-slate-800 text-slate-300">
                      {a.concern_type}
                    </span>
                    <span className="text-[10px] text-brand-400 font-semibold">→ {a.routed_to}</span>
                  </div>
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                    a.status === 'Approved' ? 'bg-emerald-950/40 text-emerald-400' :
                    a.status === 'Rejected' ? 'bg-rose-950/40 text-rose-400' : 'bg-amber-950/40 text-amber-400'
                  }`}>{a.status}</span>
                </div>
                <p className="text-xs text-slate-400">{a.description}</p>
                {a.status === 'Pending' ? (
                  <div className="space-y-2 pt-1">
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        step="0.5"
                        placeholder="Price adj. % (optional)"
                        value={approvalPriceAdjustments[a.id] || ''}
                        onChange={(e) => setApprovalPriceAdjustments(prev => ({ ...prev, [a.id]: e.target.value }))}
                        className="w-40 bg-slate-900/60 border border-slate-800 rounded-lg px-2.5 py-1.5 text-[11px] text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                        title="e.g. +3 to add 3% to the bid price when approving (Finance covering Net-90 cost-of-money, etc.)"
                      />
                      <span className="text-[10px] text-slate-500">e.g. "+3" adds 3% to the bid price on Approve</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => resolveApproval(a.id, 'Approved')}
                        disabled={approvalResolving === a.id}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-[11px] font-bold rounded-lg"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => resolveApproval(a.id, 'Rejected')}
                        disabled={approvalResolving === a.id}
                        className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-40 text-white text-[11px] font-bold rounded-lg"
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-0.5">
                    <p className="text-[10px] text-slate-500">Resolved by {a.resolved_by} on {a.resolved_at ? new Date(a.resolved_at).toLocaleString() : ''}</p>
                    {a.price_adjustment_percent ? (
                      <p className="text-[10px] text-amber-400 font-semibold">Price adjustment applied: +{a.price_adjustment_percent}%</p>
                    ) : null}
                  </div>
                )}
              </div>
            ))}

            {/* Delivery Owner Review Checkpoint — Pricing */}
            <div className="glass-panel border-slate-800/40 p-5 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-1">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Delivery Owner Review — Pricing</span>
                {deliveryReviews.pricing ? (
                  <p className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Reviewed by {deliveryReviews.pricing.reviewed_by} on {new Date(deliveryReviews.pricing.reviewed_at).toLocaleString()}
                    {deliveryReviews.pricing.notes && <span className="text-slate-400 font-normal">· "{deliveryReviews.pricing.notes}"</span>}
                  </p>
                ) : (
                  <p className="text-xs text-slate-400">Not yet reviewed — the delivery owner should check the cost/margin breakdown before final sign-off below.</p>
                )}
              </div>
              {!deliveryReviews.pricing && (
                <div className="flex items-center gap-2 w-full md:w-auto">
                  <input
                    type="text"
                    placeholder="Optional notes"
                    value={deliveryReviewNotes.pricing || ''}
                    onChange={(e) => setDeliveryReviewNotes(prev => ({ ...prev, pricing: e.target.value }))}
                    className="flex-1 md:w-56 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                  <button
                    onClick={() => submitDeliveryReview('pricing')}
                    disabled={deliveryReviewSubmitting === 'pricing'}
                    className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg shrink-0"
                  >
                    {deliveryReviewSubmitting === 'pricing' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Mark Reviewed'}
                  </button>
                </div>
              )}
            </div>

            {/* Delivery Owner Sign-Off */}
            <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
              <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">Delivery Owner Sign-Off</p>
              {signoff?.status && signoff.status !== 'Pending' ? (
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className={`w-5 h-5 ${signoff.status === 'Approved' ? 'text-emerald-400' : 'text-rose-400'}`} />
                  <span className="text-white font-bold">{signoff.status}</span>
                  <span className="text-slate-500 text-xs">
                    — {signoff.signed_by} on {signoff.signed_at ? new Date(signoff.signed_at).toLocaleString() : ''}
                  </span>
                  {signoff.notes && <span className="text-slate-400 text-xs">· "{signoff.notes}"</span>}
                </div>
              ) : (
                <>
                  {qualification?.decision !== 'Go' && (
                    <p className="text-xs text-amber-400 font-semibold flex items-start gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                      Bid qualification must be approved as "Go" first (currently: {qualification?.decision || 'not yet run'})
                      — check the Qualification tab. Sign-off cannot be Approved until that's done.
                    </p>
                  )}
                  <p className="text-xs text-slate-400">
                    {approvals.filter(a => a.status === 'Pending').length > 0
                      ? `${approvals.filter(a => a.status === 'Pending').length} approval(s) still pending — resolve them before signing off as Approved.`
                      : 'All approvals resolved. This project can be marked submission-ready.'}
                  </p>
                  <textarea
                    placeholder="Optional notes (required detail if rejecting, e.g. what needs to change before resubmission)"
                    value={signoffNotes}
                    onChange={(e) => setSignoffNotes(e.target.value)}
                    rows={2}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => submitSignoff('Approved')}
                      disabled={signoffSubmitting || qualification?.decision !== 'Go'}
                      title={qualification?.decision !== 'Go' ? 'Bid qualification must be approved as Go first' : undefined}
                      className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-bold rounded-xl"
                    >
                      Approve — Ready to Submit
                    </button>
                    <button
                      onClick={() => submitSignoff('Rejected')}
                      disabled={signoffSubmitting}
                      className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl"
                    >
                      Reject — Send Back
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Client-Facing Proposal Tab — a separate, persuasive document, not a copy of the RFP */}
        {activeTab === 'proposal' && (
          <div className="max-w-3xl space-y-5">
            {!project.client_proposal && (
              <div className="glass-panel border-slate-800/40 p-6 rounded-2xl text-center text-sm text-slate-400">
                No client-facing proposal was generated for this project yet. Re-run the analysis to generate one.
              </div>
            )}
            {project.client_proposal && (
              <>
                <div className="flex items-center gap-2 text-[10px] text-brand-400 font-semibold uppercase bg-brand-950/30 px-3.5 py-1.5 rounded-full border border-brand-500/20 w-fit">
                  <FileText className="w-3.5 h-3.5" />
                  Client-Facing Document — separate from the internal bid analysis
                </div>

                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-5 text-sm text-slate-300 leading-relaxed">
                  <p className="text-white font-semibold">{project.client_proposal.client_greeting}</p>

                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1.5">Why Us</p>
                    <p className="whitespace-pre-line">{project.client_proposal.why_us_summary}</p>
                  </div>

                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1.5">Proposed Solution</p>
                    <p className="whitespace-pre-line">{project.client_proposal.proposed_solution_narrative}</p>
                  </div>

                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1.5">Our Team</p>
                    <p className="whitespace-pre-line">{project.client_proposal.team_and_experience_narrative}</p>
                  </div>

                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1.5">Investment</p>
                    <p className="whitespace-pre-line">{project.client_proposal.investment_summary}</p>
                  </div>

                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1.5">Timeline Commitment</p>
                    <p className="whitespace-pre-line">{project.client_proposal.timeline_commitment}</p>
                  </div>

                  {project.client_proposal.differentiators?.length > 0 && (
                    <div>
                      <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1.5">Why This Bid Stands Out</p>
                      <ul className="space-y-1.5">
                        {project.client_proposal.differentiators.map((d: string, i: number) => (
                          <li key={i} className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                            {d}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1.5">Next Steps</p>
                    <p className="whitespace-pre-line">{project.client_proposal.next_steps}</p>
                  </div>
                </div>

                {/* Send this exact document to the client — compose, review/edit, then send */}
                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                  <div className="flex items-center justify-end">
                    <button
                      onClick={composeProposalEmailDraft}
                      disabled={proposalDraftLoading}
                      className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl inline-flex items-center gap-2 shrink-0"
                    >
                      {proposalDraftLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                      {proposalEmailDraft
                        ? 'Re-compose Draft'
                        : proposalRevisions.length > 0 ? 'Revise Proposal' : 'Send Proposal to Client'}
                    </button>
                  </div>

                  {proposalEmailDraft && (
                    <div className="space-y-3 pt-2 border-t border-slate-800/50">
                      {proposalEmailDraft.is_threaded_reply ? (
                        <p className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Will send as a reply in the original email thread ("{proposalEmailDraft.original_subject}")
                        </p>
                      ) : (
                        <p className="text-[10px] text-amber-400 font-semibold">
                          This project wasn't ingested from an email thread — this will send as a new, standalone email.
                        </p>
                      )}

                      <div className="flex items-center justify-between gap-3 bg-slate-900/40 border border-slate-800/50 rounded-lg px-3 py-2.5">
                        <p className="text-[11px] text-slate-400">
                          A formatted proposal <span className="text-slate-200 font-semibold">PDF</span> (investment table, delivery schedule, key points) will be attached — the body below is just the cover note.
                        </p>
                        <a
                          href={`/api/project/${encodeURIComponent(project.project_overview?.project_name || project.project_name)}/proposal-email/pdf-preview`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white text-[10px] font-bold rounded-lg inline-flex items-center gap-1.5 shrink-0"
                        >
                          <FileText className="w-3.5 h-3.5" />
                          Preview PDF
                        </a>
                      </div>

                      <div>
                        <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">To</label>
                        <input
                          type="email"
                          value={proposalEmailDraft.to_email}
                          onChange={(e) => setProposalEmailDraft({ ...proposalEmailDraft, to_email: e.target.value })}
                          placeholder="client@company.com"
                          className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">Subject</label>
                        <input
                          type="text"
                          value={proposalEmailDraft.subject}
                          onChange={(e) => setProposalEmailDraft({ ...proposalEmailDraft, subject: e.target.value })}
                          className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">Body</label>
                        <textarea
                          value={proposalEmailDraft.body}
                          onChange={(e) => setProposalEmailDraft({ ...proposalEmailDraft, body: e.target.value })}
                          rows={14}
                          className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white leading-relaxed focus:outline-none focus:border-brand-500 font-mono"
                        />
                      </div>

                      {proposalRevisions.length > 0 && (
                        <div>
                          <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">
                            What prompted this round? (optional)
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. Client asked for a 10% reduction on infrastructure costs"
                            value={clientFeedbackInput}
                            onChange={(e) => setClientFeedbackInput(e.target.value)}
                            className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                          />
                        </div>
                      )}

                      {proposalRevisions.length > 0 && (
                        <div className="bg-slate-900/30 border border-slate-800/40 rounded-lg p-3 space-y-2">
                          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wide">Revision History</p>
                          {proposalRevisions.map((rev) => (
                            <div key={rev.id} className="text-[11px] text-slate-400 flex items-start gap-2">
                              <span className="text-slate-200 font-bold shrink-0">v{rev.version}</span>
                              <div>
                                <span>{new Date(rev.sent_at).toLocaleString()} — {rev.subject}</span>
                                {rev.client_feedback && (
                                  <p className="text-amber-400/80 italic">Prompted by: "{rev.client_feedback}"</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {proposalSentStatus?.type === 'error' && (
                        <p className="text-xs font-semibold text-rose-400">{proposalSentStatus.text}</p>
                      )}

                      {proposalSentStatus?.type === 'success' ? (
                        <div className="flex items-center justify-between gap-3 pt-1">
                          <p className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                            <CheckCircle2 className="w-4 h-4" />
                            {proposalSentStatus.text}
                          </p>
                          <div className="flex items-center gap-3 shrink-0">
                            <button
                              onClick={() => setProposalSentStatus(null)}
                              className="px-4 py-2 text-brand-400 hover:text-brand-300 text-xs font-bold"
                            >
                              Edit &amp; Send Another Revision
                            </button>
                            <button
                              onClick={() => { setProposalEmailDraft(null); setProposalSentStatus(null); }}
                              className="px-4 py-2 text-slate-400 hover:text-white text-xs font-bold"
                            >
                              Close
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-end gap-3">
                          <button
                            onClick={() => { setProposalEmailDraft(null); setProposalSentStatus(null); }}
                            disabled={proposalSending}
                            className="px-4 py-2.5 text-slate-400 hover:text-white text-xs font-bold"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={sendProposalEmail}
                            disabled={proposalSending || !proposalEmailDraft.to_email.trim()}
                            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-bold rounded-xl inline-flex items-center gap-2"
                          >
                            {proposalSending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                            {proposalSending ? 'Sending...' : 'Send to Client'}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {proposalRevisions.length > 0 && (
                  <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-1">Client Response</p>
                        <p className="text-[11px] text-slate-500">
                          Checks the email thread for the client's reply to the proposal and classifies it — Accepted,
                          Rejected, or Revision Requested.
                        </p>
                      </div>
                      <button
                        onClick={fetchProposalResponseFromMail}
                        disabled={fetchResponseLoading}
                        className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center gap-2 shrink-0"
                      >
                        {fetchResponseLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                        Fetch Client Response from Mail
                      </button>
                    </div>

                    {proposalResponseResult && (
                      proposalResponseResult.found ? (
                        <div className="bg-slate-900/30 border border-slate-800/40 p-4 rounded-xl space-y-2">
                          <span className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded inline-block ${
                            proposalResponseResult.response_type === 'Accepted' ? 'bg-emerald-950/40 text-emerald-400' :
                            proposalResponseResult.response_type === 'Rejected' ? 'bg-rose-950/40 text-rose-400' :
                            proposalResponseResult.response_type === 'Revision Requested' ? 'bg-amber-950/40 text-amber-400' :
                            'bg-slate-800 text-slate-400'
                          }`}>{proposalResponseResult.response_type}</span>
                          <p className="text-xs text-slate-300">{proposalResponseResult.summary}</p>

                          {proposalResponseResult.response_type === 'Revision Requested' && changeDecisions.length > 0 && (
                            <div className="space-y-3 pt-2">
                              <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Decide on Each Request</p>
                              {changeDecisions.map((d, idx) => (
                                <div key={idx} className="bg-slate-950/30 border border-slate-800/40 p-3.5 rounded-xl space-y-2">
                                  <p className="text-xs text-slate-200">{d.change}</p>
                                  <div className="flex items-center gap-2">
                                    <select
                                      value={d.decision}
                                      onChange={(e) => setChangeDecisions(prev => prev.map((p, i) => i === idx ? { ...p, decision: e.target.value } : p))}
                                      className="bg-slate-900/60 border border-slate-800 rounded-lg px-2 py-1.5 text-[11px] text-white focus:outline-none focus:border-brand-500 shrink-0"
                                    >
                                      <option value="">Decide...</option>
                                      <option value="Accept">Accept</option>
                                      <option value="Decline">Decline</option>
                                      <option value="Partial">Partial</option>
                                    </select>
                                    <input
                                      type="text"
                                      placeholder="Note (e.g. 'confirmed with finance, 8% is feasible')"
                                      value={d.note}
                                      onChange={(e) => setChangeDecisions(prev => prev.map((p, i) => i === idx ? { ...p, note: e.target.value } : p))}
                                      className="flex-1 bg-slate-900/60 border border-slate-800 rounded-lg px-2.5 py-1.5 text-[11px] text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                                    />
                                  </div>
                                  {d.decision === 'Accept' && (
                                    <div className="flex items-center gap-2">
                                      <input
                                        type="number"
                                        placeholder="Price adj. % (optional)"
                                        value={d.price_adjustment_percent}
                                        onChange={(e) => setChangeDecisions(prev => prev.map((p, i) => i === idx ? { ...p, price_adjustment_percent: e.target.value } : p))}
                                        className="w-44 bg-slate-900/60 border border-slate-800 rounded-lg px-2.5 py-1.5 text-[11px] text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                                      />
                                      <p className="text-[10px] text-slate-500">
                                        e.g. "-10" cuts the real bid price 10% — this updates the actual budget everywhere (PDF, Resources, Dashboard), not just this email's wording.
                                      </p>
                                    </div>
                                  )}
                                </div>
                              ))}
                              <button
                                onClick={draftReplyWithDecisions}
                                disabled={draftingReply}
                                className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center gap-2"
                              >
                                {draftingReply ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                                {draftingReply ? 'Drafting...' : 'Draft Reply with AI'}
                              </button>
                              <p className="text-[10px] text-slate-500">
                                Drafts a short reply addressing each decision above — not a full proposal re-send — for your review before sending.
                              </p>
                            </div>
                          )}

                          {replyDraft && (
                            <div className="space-y-3 pt-3 border-t border-slate-800/50">
                              <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Reply Draft</p>
                              <div>
                                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">To</label>
                                <input
                                  type="email"
                                  value={replyDraft.to_email}
                                  onChange={(e) => setReplyDraft({ ...replyDraft, to_email: e.target.value })}
                                  className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                                />
                              </div>
                              <div>
                                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">Subject</label>
                                <input
                                  type="text"
                                  value={replyDraft.subject}
                                  onChange={(e) => setReplyDraft({ ...replyDraft, subject: e.target.value })}
                                  className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                                />
                              </div>
                              <div>
                                <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wide block mb-1">Body</label>
                                <textarea
                                  value={replyDraft.body}
                                  onChange={(e) => setReplyDraft({ ...replyDraft, body: e.target.value })}
                                  rows={10}
                                  className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white leading-relaxed focus:outline-none focus:border-brand-500 font-mono"
                                />
                              </div>

                              {replySentStatus?.type === 'error' && (
                                <p className="text-xs font-semibold text-rose-400">{replySentStatus.text}</p>
                              )}

                              {replySentStatus?.type === 'success' ? (
                                <div className="flex items-center justify-between gap-3">
                                  <p className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                                    <CheckCircle2 className="w-4 h-4" />
                                    {replySentStatus.text}
                                  </p>
                                  <button
                                    onClick={() => { setReplyDraft(null); setReplySentStatus(null); }}
                                    className="px-4 py-2 text-slate-400 hover:text-white text-xs font-bold shrink-0"
                                  >
                                    Close
                                  </button>
                                </div>
                              ) : (
                                <div className="flex items-center justify-end gap-3">
                                  <button
                                    onClick={() => { setReplyDraft(null); setReplySentStatus(null); }}
                                    disabled={replySending}
                                    className="px-4 py-2.5 text-slate-400 hover:text-white text-xs font-bold"
                                  >
                                    Cancel
                                  </button>
                                  <button
                                    onClick={sendClientReply}
                                    disabled={replySending || !replyDraft.to_email.trim()}
                                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-bold rounded-xl inline-flex items-center gap-2"
                                  >
                                    {replySending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                                    {replySending ? 'Sending...' : 'Send Reply'}
                                  </button>
                                </div>
                              )}
                            </div>
                          )}

                          {proposalResponseResult.response_type === 'Accepted' && (
                            outcomes?.win_loss?.status === 'Won' ? (
                              <p className="text-[10px] text-emerald-400 pt-1 flex items-center gap-1.5">
                                <CheckCircle2 className="w-3.5 h-3.5" /> Already recorded as Won on the Outcomes tab.
                              </p>
                            ) : (
                              <div className="pt-1 flex items-center gap-3">
                                <button
                                  onClick={() => submitWinLoss('Won', proposalResponseResult.summary)}
                                  disabled={!!winLossSubmitting}
                                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center gap-2 shrink-0"
                                >
                                  {winLossSubmitting === 'Won' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                                  Mark Won
                                </button>
                                <p className="text-[10px] text-slate-500">Records this on the Outcomes tab using the summary above as the reason.</p>
                              </div>
                            )
                          )}
                          {proposalResponseResult.response_type === 'Rejected' && (
                            outcomes?.win_loss?.status === 'Lost' ? (
                              <p className="text-[10px] text-rose-400 pt-1 flex items-center gap-1.5">
                                <CheckCircle2 className="w-3.5 h-3.5" /> Already recorded as Lost on the Outcomes tab.
                              </p>
                            ) : (
                              <div className="pt-1 flex items-center gap-3">
                                <button
                                  onClick={() => submitWinLoss('Lost', proposalResponseResult.summary)}
                                  disabled={!!winLossSubmitting}
                                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center gap-2 shrink-0"
                                >
                                  {winLossSubmitting === 'Lost' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                                  Mark Lost
                                </button>
                                <p className="text-[10px] text-slate-500">Records this on the Outcomes tab using the summary above as the reason.</p>
                              </div>
                            )
                          )}
                          {proposalResponseResult.response_type === 'Unclear' && (
                            <p className="text-[10px] text-slate-500 pt-1">The reply didn't clearly indicate accept/reject/revise — read it directly above.</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500 italic">No reply found in the thread yet.</p>
                      )
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Resources & Budget Tab */}
        {activeTab === 'resources' && (
          <div className="space-y-6">
            {isBudgetExceeded && (
              <div className="flex items-start gap-3.5 p-5 rounded-2xl bg-rose-950/20 border border-rose-500/20 text-xs text-rose-200 shadow-lg shadow-rose-950/10">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="font-extrabold text-sm text-white">Target Budget Overrun</h4>
                  <p className="text-slate-300 leading-relaxed">
                    The estimated delivery cost of <strong className="text-white">${totalCost.toLocaleString()}</strong> exceeds the SOW target budget of <strong className="text-white">{project.project_overview?.budget || 'N/A'}</strong> by <strong className="text-rose-400 font-bold">${budgetDeficit.toLocaleString()}</strong>. Consider adjusting scope or resource allocation parameters.
                  </p>
                </div>
              </div>
            )}
            {isTargetBudgetMissing && (
              <div className="flex items-start gap-3.5 p-5 rounded-2xl bg-amber-950/20 border border-amber-500/20 text-xs text-amber-200 shadow-lg shadow-amber-950/10">
                <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="font-extrabold text-sm text-white">No Target Budget Constraint</h4>
                  <p className="text-slate-300 leading-relaxed">
                    This project statement of work does not specify a target budget constraint. A bottom-up cost estimate of <strong className="text-white">${totalCost.toLocaleString()}</strong> was calculated based on the generated resource requirements and delivery timeline.
                  </p>
                </div>
              </div>
            )}

            {/* Budget Action & Status Dashboard */}
            <div className="glass-panel border-slate-800/40 p-5 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-1">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Budget Approval Control</span>
                <div className="flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${isApproved ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
                  <h4 className="text-xs font-bold text-slate-200">
                    Status: {isApproved ? 'Approved by Delivery Team' : 'Awaiting Review & Approval'}
                  </h4>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
                {!isApproved ? (
                  <button
                    onClick={handleApprove}
                    className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-emerald-600/10 active:scale-95 w-full md:w-auto justify-center"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Approve Budget Plan
                  </button>
                ) : (
                  <>
                    <span className="px-3.5 py-2 rounded-xl bg-emerald-950/20 text-emerald-400 font-bold border border-emerald-500/20 text-xs flex items-center gap-1.5 w-full md:w-auto justify-center">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      Budget Approved
                    </span>

                    <button
                      onClick={() => setShowEmailForm(!showEmailForm)}
                      className="flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold border border-slate-700 transition-all active:scale-95 w-full md:w-auto justify-center"
                    >
                      <FileText className="w-4 h-4 text-brand-400" />
                      {showEmailForm ? 'Cancel Proposal' : 'Propose to Client via Email'}
                    </button>

                    {onAssignTasks && (
                      <button
                        onClick={() => onAssignTasks(project.project_overview?.project_name || project.project_name)}
                        className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white rounded-xl text-xs font-bold transition-all active:scale-95 w-full md:w-auto justify-center"
                      >
                        <Users className="w-4 h-4" />
                        Assign Tasks to Workers
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Delivery Owner Review Checkpoint — Solutioning */}
            <div className="glass-panel border-slate-800/40 p-5 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-1">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Delivery Owner Review — Solutioning</span>
                {deliveryReviews.solutioning ? (
                  <p className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Reviewed by {deliveryReviews.solutioning.reviewed_by} on {new Date(deliveryReviews.solutioning.reviewed_at).toLocaleString()}
                    {deliveryReviews.solutioning.notes && <span className="text-slate-400 font-normal">· "{deliveryReviews.solutioning.notes}"</span>}
                  </p>
                ) : (
                  <p className="text-xs text-slate-400">Not yet reviewed by the delivery owner — team structure and timeline shown above should be checked before pricing is finalized.</p>
                )}
              </div>
              {!deliveryReviews.solutioning && (
                <div className="flex items-center gap-2 w-full md:w-auto">
                  <input
                    type="text"
                    placeholder="Optional notes"
                    value={deliveryReviewNotes.solutioning || ''}
                    onChange={(e) => setDeliveryReviewNotes(prev => ({ ...prev, solutioning: e.target.value }))}
                    className="flex-1 md:w-56 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                  <button
                    onClick={() => submitDeliveryReview('solutioning')}
                    disabled={deliveryReviewSubmitting === 'solutioning'}
                    className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg shrink-0"
                  >
                    {deliveryReviewSubmitting === 'solutioning' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Mark Reviewed'}
                  </button>
                </div>
              )}
            </div>

            {/* Email Proposal Slide-down Form */}
            {showEmailForm && (
              <div className="glass-panel border-slate-800/40 p-5 rounded-2xl space-y-4 animate-slideDown">
                <div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <FileText className="w-4 h-4 text-brand-400" />
                    Send Budget Proposal Email
                  </h4>
                  <p className="text-[10px] text-slate-400 mt-1">
                    Send the full breakdown of estimated development, SaaS, and contingency buffer costs to the client.
                  </p>
                </div>

                <form onSubmit={handleSendProposal} className="space-y-4 text-xs">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-slate-400 font-semibold block">Client Recipient Email</label>
                      {project.email_metadata?.sender ? (
                        <div className="w-full bg-slate-950 border border-slate-900 text-slate-400 p-2.5 rounded-xl cursor-not-allowed font-medium select-all">
                          {getOwnerEmail()} <span className="text-[9px] font-bold text-brand-500 bg-brand-950/20 px-2 py-0.5 rounded border border-brand-500/25 ml-2">PROJECT OWNER</span>
                        </div>
                      ) : (
                        <input
                          type="email"
                          required
                          value={emailInput}
                          onChange={(e) => setEmailInput(e.target.value)}
                          placeholder="client@company.com"
                          className="w-full bg-slate-900 border border-slate-800 text-slate-200 outline-none focus:border-brand-500 p-2.5 rounded-xl transition-all"
                        />
                      )}
                    </div>
                    
                    <div className="space-y-1">
                      <label className="text-slate-400 font-semibold block">Subject line</label>
                      <input
                        type="text"
                        disabled
                        value={`Project Budget Proposal: ${project.project_overview?.project_name || project.project_name}`}
                        className="w-full bg-slate-950 border border-slate-900 text-slate-500 p-2.5 rounded-xl cursor-not-allowed"
                      />
                    </div>
                  </div>

                  {emailStatus && (
                    <div className={`p-3 rounded-xl flex items-center gap-2 text-xs ${
                      emailStatus.type === 'success' 
                        ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' 
                        : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
                    }`}>
                      {emailStatus.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                      <span>{emailStatus.text}</span>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={emailSending}
                    className="px-5 py-2.5 bg-gradient-to-r from-brand-600 to-brand-500 text-white rounded-xl font-bold transition-all active:scale-95 disabled:opacity-50"
                  >
                    {emailSending ? 'Sending Proposal...' : 'Send Proposal Email'}
                  </button>
                </form>
              </div>
            )}

            {/* Budget charts & Recommended team columns */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Recommended Team Roles */}
              <div className="lg:col-span-7 glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Users className="w-5 h-5 text-brand-400" />
                  Recommended Delivery Team
                </h3>

                <div className="space-y-3">
                  {project.resource_plan?.recommended_team?.map((member: any, idx: number) => {
                    const assigned = roleAssigned[idx];
                    const isExpanded = expandedRoleIdx === idx;
                    const matches = roleMatches[idx];
                    const schedule = getResourceSchedule(member.role);
                    return (
                      <div key={idx} className="rounded-xl bg-slate-900/30 border border-slate-800/40 overflow-hidden">
                        <div className="flex justify-between items-center p-3.5 gap-3">
                          <div className="space-y-1 min-w-0">
                            <span className="text-xs font-bold text-slate-200 block">{member.role}</span>
                            <span className="text-[10px] text-slate-500 block leading-normal">{member.key_responsibility}</span>
                            {schedule && (
                              <span
                                className="text-[10px] text-amber-400/90 flex items-center gap-1 mt-1"
                                title={schedule.engagement_notes || ''}
                              >
                                <Clock className="w-3 h-3 shrink-0" />
                                Weeks {schedule.start_week}&ndash;{schedule.end_week}
                                {schedule.engagement_notes ? ` — ${schedule.engagement_notes}` : ''}
                              </span>
                            )}
                            {assigned && (
                              <span className="text-[10px] font-bold text-emerald-400 flex items-center gap-1 mt-1">
                                <UserCheck className="w-3 h-3" /> Assigned: {assigned.name}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="px-2.5 py-1 text-[10px] font-bold rounded-lg bg-brand-950/20 text-brand-400 border border-brand-500/25">
                              Qty: {member.count || 1}
                            </span>
                            <button
                              onClick={() => toggleAssignForRole(idx, member)}
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white transition-all active:scale-95"
                            >
                              <Sparkles className="w-3.5 h-3.5" />
                              {isExpanded ? 'Hide' : 'Assign'}
                            </button>
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="border-t border-slate-800/40 p-3.5 space-y-2 bg-slate-950/20">
                            {roleMatching === idx ? (
                              <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
                                <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
                                Retrieving and reranking top candidates...
                              </div>
                            ) : matches && matches.length > 0 ? (
                              matches.map((m) => {
                                const w = allWorkers?.find((x: any) => x.id === m.worker_id);
                                if (!w) return null;
                                const isAssignedHere = assigned?.workerId === m.worker_id;
                                return (
                                  <div key={m.worker_id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/50">
                                    <div className="min-w-0 space-y-0.5">
                                      <div className="flex items-center gap-2 flex-wrap">
                                        <span className="text-xs font-bold text-slate-200">{w.name}</span>
                                        <span className="text-[9px] text-slate-500">{w.role}</span>
                                        <span className="text-[9px] font-bold uppercase text-brand-400 bg-brand-950/20 border border-brand-500/25 px-1.5 py-0.5 rounded">
                                          {m.score}% match
                                        </span>
                                      </div>
                                      {m.reasons?.length > 0 && (
                                        <p className="text-[10px] text-slate-500 leading-relaxed">{m.reasons.join(' · ')}</p>
                                      )}
                                    </div>
                                    <button
                                      onClick={() => handleAssignToRole(idx, member, m.worker_id)}
                                      disabled={roleAssigning === m.worker_id || isAssignedHere}
                                      className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-[9px] font-bold uppercase tracking-wider bg-emerald-600 hover:bg-emerald-500 text-white transition-all active:scale-95 disabled:opacity-60 shrink-0"
                                    >
                                      {roleAssigning === m.worker_id ? (
                                        <Loader2 className="w-3 h-3 animate-spin" />
                                      ) : isAssignedHere ? (
                                        <CheckCircle2 className="w-3 h-3" />
                                      ) : null}
                                      {isAssignedHere ? 'Assigned' : 'Assign'}
                                    </button>
                                  </div>
                                );
                              })
                            ) : (
                              <p className="text-xs text-slate-500 py-1">No matching candidates found in the worker directory.</p>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Budget charts */}
              <div className="lg:col-span-5 glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <ChartIcon className="w-5 h-5 text-brand-400" />
                  Cost Allocation
                </h3>
                <div className="h-56">
                  {budgetData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={budgetData}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={75}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {budgetData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-xs text-slate-500 italic">No budget values to plot.</div>
                  )}
                </div>
                {/* Legend list */}
                <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 border-t border-slate-800/50 pt-3">
                  {budgetData.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: item.color }} />
                      <span className="truncate">{item.name}</span>
                    </div>
                  ))}
                </div>

                {/* Contingency basis + margin + final bid price — kept as separate, explicit lines
                    so contingency (risk we might absorb) is never confused with margin (profit we keep) */}
                {(rawBreakdown.buffer_basis || rawBreakdown.margin_percent !== undefined) && (
                  <div className="border-t border-slate-800/50 pt-3 space-y-2.5">
                    {rawBreakdown.buffer_basis && (
                      <p className="text-[10px] text-slate-500 leading-relaxed">
                        <span className="font-bold text-slate-400">Contingency basis: </span>
                        {rawBreakdown.buffer_basis}
                      </p>
                    )}
                    {rawBreakdown.margin_percent !== undefined && (
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Margin ({rawBreakdown.margin_percent}%)</span>
                        <span className="text-emerald-400 font-semibold">+${Number(rawBreakdown.margin_amount || 0).toLocaleString()}</span>
                      </div>
                    )}
                    {rawBreakdown.bid_price !== undefined && (
                      <div className="flex items-center justify-between text-sm border-t border-slate-800/50 pt-2.5">
                        <span className="text-white font-bold">Final Bid Price</span>
                        <span className="text-brand-400 font-extrabold">${Number(rawBreakdown.bid_price).toLocaleString()}</span>
                      </div>
                    )}
                    {rawBreakdown.price_adjustments?.length > 0 && (
                      <div className="pt-2 space-y-1.5">
                        <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Price Adjustments</p>
                        {rawBreakdown.price_adjustments.map((adj: any, i: number) => (
                          <div key={i} className="text-[10px] text-slate-400 flex items-start gap-1.5">
                            <span className={adj.adjustment_percent >= 0 ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>
                              {adj.adjustment_percent >= 0 ? '+' : ''}{adj.adjustment_percent}%
                            </span>
                            <span className="truncate">{adj.reason}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

            </div>

          </div>
        )}

        {/* Timeline Tab */}
        {activeTab === 'timeline' && (
          <div className="space-y-6">
            <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-2">
                <Clock className="w-5 h-5 text-brand-400" />
                Delivery Timeline Phases
              </h3>
              <p className="text-xs text-slate-400">Phased rollout of deliverables grouped into sprint boundaries.</p>

              <div className="space-y-4 mt-6">
                {(project.timeline?.project_phases || project.timeline?.phases || []).map((phase: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-900/30 border border-slate-800/40 space-y-2">
                    <div className="flex justify-between items-center">
                      <h4 className="text-xs font-extrabold text-slate-200">{phase.phase_name}</h4>
                      <span className="text-[10px] font-bold px-2 py-0.5 bg-brand-950/20 text-brand-400 border border-brand-500/25 rounded">
                        Weeks {phase.start_week} - {phase.end_week}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-light leading-normal">{phase.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">Log a Schedule Disruption</h3>
                <p className="text-xs text-slate-400">
                  A real delay, scope change, or resource conflict — not a re-estimate. The affected phase and
                  everything scheduled after it shifts deterministically, and the resulting cost impact is applied
                  automatically to the real bid price (same traceable log as negotiated price changes).
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <select
                  value={adjustTriggerType}
                  onChange={(e) => setAdjustTriggerType(e.target.value)}
                  className="bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="">Trigger type...</option>
                  <option value="Dependency Delay">Dependency Delay</option>
                  <option value="Scope Change">Scope Change</option>
                  <option value="Resource Conflict">Resource Conflict</option>
                  <option value="Velocity Variance">Velocity Variance</option>
                  <option value="Other">Other</option>
                </select>
                <select
                  value={adjustAffectedPhase}
                  onChange={(e) => setAdjustAffectedPhase(e.target.value)}
                  className="bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="">Affected phase...</option>
                  {(project.timeline?.project_phases || project.timeline?.phases || []).map((phase: any, idx: number) => (
                    <option key={idx} value={phase.phase_name}>{phase.phase_name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="number"
                  placeholder="Delta weeks (e.g. 2, or -1 to accelerate)"
                  value={adjustDeltaWeeks}
                  onChange={(e) => setAdjustDeltaWeeks(e.target.value)}
                  className="bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                />
                <button
                  onClick={submitTimelineAdjustment}
                  disabled={adjustSubmitting || !adjustTriggerType || !adjustAffectedPhase || !adjustDeltaWeeks.trim() || !adjustReason.trim()}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center justify-center gap-2"
                >
                  {adjustSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                  Apply Adjustment
                </button>
              </div>
              <textarea
                placeholder="Reason (e.g. 'Client delayed providing Epic sandbox API credentials by 2 weeks')"
                value={adjustReason}
                onChange={(e) => setAdjustReason(e.target.value)}
                rows={2}
                className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
              />

              {adjustResult && (
                <p className={`text-xs font-semibold flex items-center gap-1.5 ${adjustResult.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {adjustResult.type === 'success' ? <CheckCircle2 className="w-3.5 h-3.5" /> : null}
                  {adjustResult.text}
                </p>
              )}

              {timelineRevisions.length > 0 && (
                <div className="pt-3 border-t border-slate-800/50 space-y-2">
                  <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Schedule Revision History</p>
                  {timelineRevisions.map((rev) => (
                    <div key={rev.id} className="bg-slate-900/30 border border-slate-800/40 p-3 rounded-lg text-[11px] text-slate-400">
                      <span className="text-slate-200 font-semibold">{rev.trigger_type}</span> on <span className="text-slate-300">{rev.affected_phase}</span>
                      {' '}({rev.delta_weeks > 0 ? '+' : ''}{rev.delta_weeks} weeks)
                      {rev.cost_impact ? (
                        <span className={rev.cost_impact > 0 ? 'text-rose-400' : 'text-emerald-400'}>
                          {' '}— {rev.cost_impact > 0 ? '+' : ''}${rev.cost_impact.toLocaleString()}
                        </span>
                      ) : null}
                      <p className="text-slate-500 italic mt-0.5">"{rev.reason}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Risks Tab */}
        {activeTab === 'risks' && (
          <div className="space-y-6">
            <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-2">
                <AlertCircle className="w-5 h-5 text-brand-400" />
                Delivery Risk Matrix
              </h3>
              <p className="text-xs text-slate-400">Predicted failure vectors and proposed mitigation procedures.</p>

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
                            <span className="text-[9px] px-2 py-0.5 rounded-full bg-slate-900/80 border border-slate-800/80 font-bold uppercase tracking-wider text-slate-400">
                              P: {risk.probability}
                            </span>
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

        {/* Policies & Compliance Tab */}
        {activeTab === 'policies' && (
          <div className="space-y-6">
            <div className="glass-panel border-slate-800/40 p-6 rounded-2xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-5 h-5 text-brand-400" />
                Policy & Guardrails Compliance Engine
              </h3>
              <p className="text-xs text-slate-400 mb-6">Validation of billing rates, resource allocations, and budget ceilings.</p>

              {loadingExtras ? (
                <div className="text-center py-12 text-xs text-slate-500 animate-pulse">Loading compliance data...</div>
              ) : policies.length === 0 ? (
                <div className="text-center py-12 text-xs text-slate-500 italic">No policy evaluations found for this project.</div>
              ) : (
                <div className="space-y-4">
                  {policies.map((p: any, idx: number) => (
                    <div 
                      key={idx}
                      className={`p-4 rounded-xl border flex items-start gap-4 transition-all ${
                        p.passed 
                          ? 'border-emerald-500/20 bg-emerald-950/5' 
                          : 'border-rose-500/20 bg-rose-950/5'
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                        p.passed ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {p.passed ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-slate-200">{p.policy_name}</h4>
                          <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                            p.passed ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
                          }`}>
                            {p.passed ? 'Passed' : 'Alert'}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed font-light">{p.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Outcomes Tab — the post-award lifecycle: what happened after the proposal went out */}
        {activeTab === 'outcomes' && (
          <div className="space-y-6 max-w-3xl">
            <p className="text-sm text-slate-400">
              What happened after the proposal was sent — logged manually, since there's no CRM or
              timesheet integration feeding this automatically yet.
            </p>

            {outcomesLoading && !outcomes ? (
              <div className="text-center py-12 text-xs text-slate-500 animate-pulse">Loading outcomes...</div>
            ) : (
              <>
                {/* Contract & Signature Status */}
                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                  <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">Contract &amp; Signature Status</p>
                  <p className="text-[11px] text-slate-500">
                    Tracks where the actual contract/signature process stands — this records status manually; it
                    does not perform e-signature itself.
                  </p>

                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded shrink-0 ${
                      contractStatus?.status === 'Signed' ? 'bg-emerald-950/40 text-emerald-400' :
                      contractStatus?.status === 'Rejected' ? 'bg-rose-950/40 text-rose-400' :
                      contractStatus?.status === 'Sent for Signature' ? 'bg-amber-950/40 text-amber-400' :
                      'bg-slate-800 text-slate-400'
                    }`}>{contractStatus?.status || 'Not Started'}</span>
                    {contractStatus?.updated_at && (
                      <span className="text-[10px] text-slate-500">
                        Updated by {contractStatus.updated_by} on {new Date(contractStatus.updated_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                  {contractStatus?.notes && (
                    <p className="text-[11px] text-slate-400 italic">"{contractStatus.notes}"</p>
                  )}

                  {contractStatus?.status !== 'Signed' && contractStatus?.status !== 'Rejected' && (
                    <div className="space-y-3 pt-2 border-t border-slate-800/50">
                      <input
                        type="text"
                        placeholder="Optional notes (e.g. 'Sent via DocuSign to procurement@client.com')"
                        value={contractStatusNotes}
                        onChange={(e) => setContractStatusNotes(e.target.value)}
                        className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => submitContractStatus('Sent for Signature')}
                          disabled={!!contractStatusSubmitting}
                          className="px-3 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg"
                        >
                          {contractStatusSubmitting === 'Sent for Signature' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Mark Sent for Signature'}
                        </button>
                        <button
                          onClick={() => submitContractStatus('Signed')}
                          disabled={!!contractStatusSubmitting}
                          className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg"
                        >
                          {contractStatusSubmitting === 'Signed' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Mark Signed'}
                        </button>
                        <button
                          onClick={() => submitContractStatus('Rejected')}
                          disabled={!!contractStatusSubmitting}
                          className="px-3 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg"
                        >
                          {contractStatusSubmitting === 'Rejected' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Mark Rejected'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Win/Loss */}
                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                  <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">Win / Loss Decision</p>
                  {outcomes?.win_loss ? (
                    <div className="flex items-start gap-3">
                      <span className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded shrink-0 ${
                        outcomes.win_loss.status === 'Won' ? 'bg-emerald-950/40 text-emerald-400' : 'bg-rose-950/40 text-rose-400'
                      }`}>{outcomes.win_loss.status}</span>
                      <div className="space-y-1">
                        <p className="text-xs text-slate-300">{outcomes.win_loss.reason}</p>
                        <p className="text-[10px] text-slate-500">
                          Decided by {outcomes.win_loss.decided_by} on {new Date(outcomes.win_loss.decided_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <textarea
                        placeholder="Reason (e.g. why the client chose us, or why we lost)"
                        value={winLossReason}
                        onChange={(e) => setWinLossReason(e.target.value)}
                        rows={2}
                        className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                      />
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => submitWinLoss('Won')}
                          disabled={!!winLossSubmitting}
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center gap-2"
                        >
                          {winLossSubmitting === 'Won' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                          Mark Won
                        </button>
                        <button
                          onClick={() => submitWinLoss('Lost')}
                          disabled={!!winLossSubmitting}
                          className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center gap-2"
                        >
                          {winLossSubmitting === 'Lost' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                          Mark Lost
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Estimate vs Actual */}
                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                  <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">Estimate vs. Actual</p>

                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div className="bg-slate-900/40 border border-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Estimated Cost</p>
                      <p className="text-white font-bold">{formatCurrency(outcomes?.estimate?.total_cost)}</p>
                    </div>
                    <div className="bg-slate-900/40 border border-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Estimated Duration</p>
                      <p className="text-white font-bold">{outcomes?.estimate?.estimated_completion || 'N/A'}</p>
                    </div>
                  </div>

                  {outcomes?.actuals ? (
                    <div className="space-y-3 pt-2 border-t border-slate-800/50">
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div className="bg-slate-900/40 border border-slate-800/50 rounded-lg p-3">
                          <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Actual Cost</p>
                          <p className="text-white font-bold">{formatCurrency(outcomes.actuals.actual_total_cost)}</p>
                          {outcomes.estimate?.total_cost ? (() => {
                            const variance = ((outcomes.actuals.actual_total_cost - outcomes.estimate.total_cost) / outcomes.estimate.total_cost) * 100;
                            return (
                              <p className={`text-[10px] font-bold mt-1 ${variance > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                                {variance > 0 ? '+' : ''}{variance.toFixed(1)}% vs estimate
                              </p>
                            );
                          })() : null}
                        </div>
                        <div className="bg-slate-900/40 border border-slate-800/50 rounded-lg p-3">
                          <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Actual Duration</p>
                          <p className="text-white font-bold">{outcomes.actuals.actual_duration_weeks} weeks</p>
                        </div>
                      </div>
                      {outcomes.actuals.notes && (
                        <p className="text-[11px] text-slate-400 italic">"{outcomes.actuals.notes}"</p>
                      )}
                      <p className="text-[10px] text-slate-500">
                        Logged by {outcomes.actuals.logged_by} on {new Date(outcomes.actuals.logged_at).toLocaleString()}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3 pt-2 border-t border-slate-800/50">
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          type="number"
                          placeholder="Actual total cost ($)"
                          value={actualsCostInput}
                          onChange={(e) => setActualsCostInput(e.target.value)}
                          className="bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                        />
                        <input
                          type="number"
                          placeholder="Actual duration (weeks)"
                          value={actualsWeeksInput}
                          onChange={(e) => setActualsWeeksInput(e.target.value)}
                          className="bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                        />
                      </div>
                      <textarea
                        placeholder="Notes (what drove any variance)"
                        value={actualsNotes}
                        onChange={(e) => setActualsNotes(e.target.value)}
                        rows={2}
                        className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                      />
                      <button
                        onClick={submitActuals}
                        disabled={actualsSubmitting || !actualsCostInput || !actualsWeeksInput}
                        className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center gap-2"
                      >
                        {actualsSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                        Log Actuals
                      </button>
                    </div>
                  )}
                </div>

                {/* Cost of Bidding */}
                <div className="glass-panel border-slate-800/40 p-6 rounded-2xl space-y-4">
                  <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">Cost of Bidding</p>
                  <p className="text-[11px] text-slate-500">Internal BD/solutioning hours spent preparing this bid — tracked independent of win/loss.</p>

                  {outcomes?.bid_cost ? (
                    <div className="space-y-2">
                      <div className="flex items-baseline gap-2">
                        <span className="text-lg font-extrabold text-white">
                          {formatCurrency(outcomes.bid_cost.internal_hours * outcomes.bid_cost.internal_hourly_rate)}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          ({outcomes.bid_cost.internal_hours} hrs @ {formatCurrency(outcomes.bid_cost.internal_hourly_rate)}/hr)
                        </span>
                      </div>
                      {outcomes.bid_cost.notes && (
                        <p className="text-[11px] text-slate-400 italic">"{outcomes.bid_cost.notes}"</p>
                      )}
                      <p className="text-[10px] text-slate-500">
                        Logged by {outcomes.bid_cost.logged_by} on {new Date(outcomes.bid_cost.logged_at).toLocaleString()}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          type="number"
                          placeholder="Internal hours spent"
                          value={bidHoursInput}
                          onChange={(e) => setBidHoursInput(e.target.value)}
                          className="bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                        />
                        <input
                          type="number"
                          placeholder="Internal hourly rate ($)"
                          value={bidRateInput}
                          onChange={(e) => setBidRateInput(e.target.value)}
                          className="bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                        />
                      </div>
                      <textarea
                        placeholder="Notes (what the time went into)"
                        value={bidCostNotes}
                        onChange={(e) => setBidCostNotes(e.target.value)}
                        rows={2}
                        className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                      />
                      <button
                        onClick={submitBidCost}
                        disabled={bidCostSubmitting || !bidHoursInput}
                        className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg inline-flex items-center gap-2"
                      >
                        {bidCostSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                        Log Cost of Bidding
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

    </div>
  );
}
