import React, { Suspense, lazy, useEffect, useMemo, useState } from "react";

const MIN_BOTTOM_PANEL = 110;

function maxBottomPanelHeightPx() {
  if (typeof window === "undefined") return 920;
  const h = window.innerHeight;
  const reservedChrome = 100;
  const minEditorStripe = 48;
  return Math.max(MIN_BOTTOM_PANEL + 40, Math.floor(h - reservedChrome - minEditorStripe));
}
import { api } from "./api/client";

import { ActivityBar } from "./components/workbench/ActivityBar";
import { DatasetSidebar } from "./components/workbench/DatasetSidebar";
import { EditorTabs } from "./components/workbench/EditorTabs";
import { BottomPanel } from "./components/workbench/BottomPanel";
import { SecondaryAiSidebar } from "./components/workbench/SecondaryAiSidebar";
import { StatusBar } from "./components/workbench/StatusBar";
import { TitleBar } from "./components/workbench/TitleBar";

const ProposalCodeEditor = lazy(() => import("./components/workbench/ProposalCodeEditor"));
// ds2api / local gateways often take ~60s+ per completion; leave headroom for queue + profiling.
const CURRENT_USER_ID = import.meta.env.VITE_CURRENT_USER_ID ?? "student_01";
const SESSION_ID = import.meta.env.VITE_SESSION_ID ?? "demo_01";
const PROPOSAL_JOB_POLL_INTERVAL_MS = Number(import.meta.env.VITE_PROPOSAL_JOB_POLL_INTERVAL_MS ?? 2000);
const PROPOSAL_JOB_MAX_POLLS = Number(import.meta.env.VITE_PROPOSAL_JOB_MAX_POLLS ?? 300);

const EMPTY_CODE = `# Code proposal will appear here after AI generates it.
# AI-generated code must be reviewed, edited if needed, and approved before local execution.`;

const EMPTY_DATASET = {
  id: "",
  name: "No dataset loaded",
  rows: 0,
  status: "unavailable",
  columns: []
};

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

function evtId(seed) {
  return `evt_${seed}_${Math.random().toString(36).slice(2, 9)}`;
}

function timelineFromSessions(sessions) {
  return sessions.flatMap((session, i) => {
    const rows = session.events ?? [];
    if (i === 0) return rows;
    const divider = [
      {
        id: `separator_${session.traceId}`,
        type: "trace.separator",
        actor: "system",
        detail: `Phiên trace: ${session.traceId}`,
        time: "–––"
      }
    ];
    return [...divider, ...rows];
  });
}
const normalizePolicyIssues = (issues) =>
  Array.isArray(issues)
    ? issues.map((issue) =>
        typeof issue === "string"
          ? { code: "policy_error", message: issue, severity: "error" }
          : {
              code: issue?.code ?? "policy_error",
              message: issue?.message ?? JSON.stringify(issue),
              severity: issue?.severity ?? "error"
            }
      )
    : [];

export default function App() {
  const [datasets, setDatasets] = useState([]);
  const [activeDatasetId, setActiveDatasetId] = useState("");
  const [prompt, setPrompt] = useState("Hay de xuat va ve mot bieu do phu hop voi dataset hien tai, kem bang so lieu va nhan xet cac diem noi bat.");
  const [code, setCode] = useState(EMPTY_CODE);
  const [status, setStatus] = useState("pending_review");
  /** Lưu audit theo trace_id — lần prompt sau không làm mất trace cũ. */
  const [auditSessions, setAuditSessions] = useState([]);
  const [pendingClientEvents, setPendingClientEvents] = useState([]);
  const [inspectorTab, setInspectorTab] = useState("logs");
  const [proposal, setProposal] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [error, setError] = useState("");
  const [policyIssues, setPolicyIssues] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [proposalJob, setProposalJob] = useState(null);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isPrimarySidebarOpen, setIsPrimarySidebarOpen] = useState(() =>
    typeof window === "undefined" ? true : window.innerWidth > 980
  );
  const [isSecondarySidebarOpen, setIsSecondarySidebarOpen] = useState(true);
  const [isBottomPanelOpen, setIsBottomPanelOpen] = useState(true);
  const [primarySidebarWidth, setPrimarySidebarWidth] = useState(286);
  const [secondarySidebarWidth, setSecondarySidebarWidth] = useState(352);
  const [bottomPanelHeight, setBottomPanelHeight] = useState(230);

  const activeDataset = useMemo(
    () => datasets.find((dataset) => dataset.id === activeDatasetId) ?? datasets[0] ?? EMPTY_DATASET,
    [activeDatasetId, datasets]
  );

  const hasResult = status === "succeeded";
  const isBusy = isGenerating || isApproving || isRejecting || isExecuting;
  const canRun = status === "approved" && Boolean(proposal?.code_hash) && !isExecuting;

  useEffect(() => {
    function onViewportResize() {
      setBottomPanelHeight((current) =>
        clamp(current, MIN_BOTTOM_PANEL, maxBottomPanelHeightPx())
      );
    }

    window.addEventListener("resize", onViewportResize);
    onViewportResize();
    return () => window.removeEventListener("resize", onViewportResize);
  }, []);

  useEffect(() => {
    api
      .listDatasets()
      .then((items) => {
        setDatasets(items);
        if (items[0]) {
          setActiveDatasetId(items[0].id);
        }
      })
      .catch((err) => setError(`Backend unavailable: ${err.message}`));
  }, []);

  useEffect(() => {
    if (!activeDatasetId) return;
    api
      .getDatasetContext(activeDatasetId)
      .then((context) => {
        setDatasets((items) => items.map((item) => (item.id === context.id ? context : item)));
      })
      .catch((err) => setError(`Dataset context failed: ${err.message}`));
  }, [activeDatasetId]);

  const timelineEvents = useMemo(
    () => [...timelineFromSessions(auditSessions), ...pendingClientEvents],
    [auditSessions, pendingClientEvents]
  );

  function addEvent(type, actor, detail) {
    const time = new Date().toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
    setPendingClientEvents((current) => [
      ...current,
      { id: evtId(`${type}_${current.length}`), type, actor, detail, time }
    ]);
  }

  async function refreshLogs(traceId) {
    if (!traceId) return;
    const logs = await api.getLogs(traceId);
    const mapped = logs.events.map((event) => ({
      id: event.id,
      type: event.type,
      actor: event.actor,
      time: new Date(event.time).toLocaleTimeString("en-GB"),
      detail: event.detail
    }));
    setAuditSessions((prev) => {
      const idx = prev.findIndex((session) => session.traceId === traceId);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { traceId, events: mapped };
        return next;
      }
      return [...prev, { traceId, events: mapped }];
    });
    setPendingClientEvents([]);
  }

  async function generateProposal() {
    if (!activeDatasetId) {
      setError("No registered dataset is available. Start the backend and reload datasets first.");
      return;
    }
    setError("");
    setPolicyIssues([]);
    setExecutionResult(null);
    setIsGenerating(true);
    setProposalJob(null);
    setStatus("generating");
    addEvent("ai.proposal.job_started", CURRENT_USER_ID, "Starting background proposal generation");
    try {
      const job = await api.createProposalJob({
        session_id: SESSION_ID,
        dataset_id: activeDatasetId,
        user_request: prompt,
        mode: "generate_code"
      });
      setProposalJob(job);
      addEvent("ai.proposal.job_queued", "system", `Job ${job.job_id} queued`);

      const finalJob = await waitForProposalJob(job.job_id);
      if (finalJob.status !== "succeeded" || !finalJob.proposal_id) {
        throw new Error(finalJob.error || "Proposal generation failed");
      }

      const nextProposal = await api.getProposal(finalJob.proposal_id);
      setProposal(nextProposal);
      setCode(nextProposal.code);
      setStatus(nextProposal.status);
      setInspectorTab("logs");
      await refreshLogs(nextProposal.trace_id);
    } catch (err) {
      setPolicyIssues(normalizePolicyIssues(err?.detail?.policy_errors));
      setError(err.message);
      if (err?.isProposalPollTimeout) {
        setStatus("generating");
        if (err.proposalJob) {
          setProposalJob(err.proposalJob);
        }
      } else {
        setStatus("failed");
      }
    } finally {
      setIsGenerating(false);
    }
  }

  async function waitForProposalJob(jobId) {
    let latest = null;
    for (let attempt = 0; attempt < PROPOSAL_JOB_MAX_POLLS; attempt += 1) {
      latest = await api.getProposalJob(jobId);
      setProposalJob(latest);

      if (latest.status === "succeeded" || latest.status === "failed") {
        return latest;
      }

      await new Promise((resolve) => window.setTimeout(resolve, PROPOSAL_JOB_POLL_INTERVAL_MS));
    }
    const timeoutError = new Error(
      `AI job ${jobId} vẫn đang chạy quá lâu ở backend. Hãy kiểm tra ds2api/model hoặc thử yêu cầu hẹp hơn.`
    );
    timeoutError.isProposalPollTimeout = true;
    timeoutError.proposalJob = latest;
    throw timeoutError;
  }

  function updateCode(value) {
    setCode(value ?? "");
    if (proposal && ["pending_review", "approved", "rejected", "failed", "succeeded"].includes(status)) setStatus("edited");
  }

  async function approveProposal() {
    if (!proposal) return;
    setError("");
    setPolicyIssues([]);
    setIsApproving(true);
    try {
      const updated = await api.updateProposal(proposal.proposal_id, {
        edited_by: CURRENT_USER_ID,
        edited_code: code
      });
      const approval = await api.approveProposal(proposal.proposal_id, {
        approved_by: CURRENT_USER_ID,
        approval_note: "Approved from frontend review gate"
      });
      setProposal({ ...updated, status: approval.status, code_hash: approval.code_hash });
      setStatus(approval.status);
      setInspectorTab("policy");
      await refreshLogs(updated.trace_id);
    } catch (err) {
      setPolicyIssues(normalizePolicyIssues(err?.detail?.policy_errors));
      setError(err.message);
      setInspectorTab("policy");
    } finally {
      setIsApproving(false);
    }
  }

  async function rejectProposal() {
    if (!proposal) return;
    setError("");
    setIsRejecting(true);
    try {
      const rejected = await api.rejectProposal(proposal.proposal_id, {
        rejected_by: CURRENT_USER_ID,
        rejection_reason: "Rejected from frontend review gate"
      });
      setProposal(rejected);
      setStatus(rejected.status);
      setInspectorTab("logs");
      await refreshLogs(rejected.trace_id);
    } catch (err) {
      setError(err.message);
      setInspectorTab("logs");
      addEvent("ai.approval.reject_failed", "system", err.message);
    } finally {
      setIsRejecting(false);
    }
  }

  async function runLocal() {
    if (!canRun || !proposal?.code_hash) return;
    setIsExecuting(true);
    setStatus("running");
    setInspectorTab("logs");
    setPolicyIssues([]);
    try {
      const result = await api.runExecution({
        proposal_id: proposal.proposal_id,
        dataset_id: proposal.dataset_id,
        code_hash: proposal.code_hash,
        requested_by: CURRENT_USER_ID
      });
      setExecutionResult(result);
      setStatus(result.status);
      setInspectorTab("result");
      await refreshLogs(proposal.trace_id);
    } catch (err) {
      setStatus((current) => (current === "running" ? "failed" : current));
      setInspectorTab("policy");
      setPolicyIssues(normalizePolicyIssues(err?.detail?.policy_errors));
      setError(err.message);
    } finally {
      setIsExecuting(false);
    }
  }

  function resetDemo() {
    setCode(EMPTY_CODE);
    setAuditSessions([]);
    setPendingClientEvents([]);
    setStatus("pending_review");
    setInspectorTab("logs");
    setProposal(null);
    setExecutionResult(null);
    setPolicyIssues([]);
    setError("");
    setProposalJob(null);
    setIsGenerating(false);
    setIsApproving(false);
    setIsRejecting(false);
    setIsExecuting(false);
  }

  function selectActivityItem(id) {
    if (id === "datasets") {
      setIsPrimarySidebarOpen((value) => !value);
      return;
    }
    setInspectorTab(id);
    setIsBottomPanelOpen(true);
  }

  function startResizePane(kind, event) {
    event.preventDefault();
    const startX = event.clientX;
    const startY = event.clientY;
    const startPrimaryWidth = primarySidebarWidth;
    const startSecondaryWidth = secondarySidebarWidth;
    const startBottomHeight = bottomPanelHeight;

    function onPointerMove(moveEvent) {
      if (kind === "primary") {
        setPrimarySidebarWidth(clamp(startPrimaryWidth + moveEvent.clientX - startX, 220, 420));
      }
      if (kind === "secondary") {
        setSecondarySidebarWidth(clamp(startSecondaryWidth - (moveEvent.clientX - startX), 280, 520));
      }
      if (kind === "bottom") {
        const cap = maxBottomPanelHeightPx();
        setBottomPanelHeight(
          clamp(startBottomHeight - (moveEvent.clientY - startY), MIN_BOTTOM_PANEL, cap)
        );
      }
    }

    function onPointerUp() {
      document.body.classList.remove("select-none", "cursor-col-resize", "cursor-row-resize");
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);
    }

    document.body.classList.add("select-none", kind === "bottom" ? "cursor-row-resize" : "cursor-col-resize");
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
  }

  const mainGridClass = [
    "relative grid min-h-0 min-w-0",
    isBottomPanelOpen && isSecondarySidebarOpen
      ? "max-[980px]:grid-rows-[minmax(0,1fr)_var(--bottom-panel-height)]"
      : "max-[980px]:grid-rows-[minmax(0,1fr)]",
    isPrimarySidebarOpen && isSecondarySidebarOpen
      ? "grid-cols-[48px_var(--primary-sidebar-width)_minmax(0,1fr)_var(--secondary-sidebar-width)] max-[1180px]:grid-cols-[44px_var(--primary-sidebar-width)_minmax(0,1fr)_var(--secondary-sidebar-width)]"
      : isPrimarySidebarOpen
        ? "grid-cols-[48px_var(--primary-sidebar-width)_minmax(0,1fr)] max-[1180px]:grid-cols-[44px_var(--primary-sidebar-width)_minmax(0,1fr)]"
        : isSecondarySidebarOpen
          ? "grid-cols-[48px_minmax(0,1fr)_var(--secondary-sidebar-width)] max-[1180px]:grid-cols-[44px_minmax(0,1fr)_var(--secondary-sidebar-width)]"
          : "grid-cols-[48px_minmax(0,1fr)] max-[1180px]:grid-cols-[44px_minmax(0,1fr)]",
    "max-[980px]:grid-cols-[44px_minmax(0,1fr)] max-[760px]:block max-[760px]:h-auto"
  ].join(" ");

  const editorSectionClass = [
    "grid min-h-0 min-w-0 overflow-hidden bg-editor max-[980px]:col-start-2 max-[980px]:row-start-1 max-[760px]:min-h-screen",
    isBottomPanelOpen
      ? "grid-rows-[minmax(0,1fr)_var(--bottom-panel-height)] max-[980px]:grid-rows-[minmax(0,1fr)_var(--bottom-panel-height)]"
      : "grid-rows-[minmax(0,1fr)]"
  ].join(" ");

  return (
    <div className="grid h-screen min-h-[720px] grid-rows-[36px_minmax(0,1fr)_24px] overflow-hidden bg-ink text-text-main max-[760px]:h-auto max-[760px]:min-h-screen max-[760px]:overflow-auto">
      <TitleBar
        isBottomPanelOpen={isBottomPanelOpen}
        isPrimarySidebarOpen={isPrimarySidebarOpen}
        isSecondarySidebarOpen={isSecondarySidebarOpen}
        onToggleBottomPanel={() => setIsBottomPanelOpen((value) => !value)}
        onTogglePrimarySidebar={() => setIsPrimarySidebarOpen((value) => !value)}
        onToggleSecondarySidebar={() => setIsSecondarySidebarOpen((value) => !value)}
      />

      <main
        className={mainGridClass}
        style={{
          "--bottom-panel-height": `${bottomPanelHeight}px`,
          "--primary-sidebar-width": `${primarySidebarWidth}px`,
          "--secondary-sidebar-width": `${secondarySidebarWidth}px`
        }}
      >
        <ActivityBar activePanel={isPrimarySidebarOpen ? "datasets" : inspectorTab} onSelectPanel={selectActivityItem} />
        {isPrimarySidebarOpen && (
          <DatasetSidebar
            activeDatasetId={activeDatasetId}
            dataset={activeDataset}
            datasets={datasets}
            onDatasetChange={setActiveDatasetId}
            onResizeStart={(event) => startResizePane("primary", event)}
          />
        )}

        <section className={editorSectionClass}>
          <div className="min-h-0 min-w-0 flex flex-col overflow-hidden bg-editor">
            <EditorTabs lineCount={code.split("\n").length} proposalId={proposal?.proposal_id} />
            <div className="min-h-0 min-w-0 flex-1 overflow-hidden">
              <Suspense fallback={<div className="grid h-full place-items-center bg-[#111112] text-muted">Preparing editor...</div>}>
                <ProposalCodeEditor code={code} onChange={updateCode} readOnly={status === "running"} />
              </Suspense>
            </div>
          </div>

          {isBottomPanelOpen && (
            <BottomPanel
              activeTab={inspectorTab}
              error={error}
              events={timelineEvents}
              executionResult={executionResult}
              hasResult={hasResult}
              policyIssues={policyIssues}
              onClose={() => setIsBottomPanelOpen(false)}
              onResizeStart={(event) => startResizePane("bottom", event)}
              onTabChange={setInspectorTab}
            />
          )}
        </section>
        {isSecondarySidebarOpen && (
          <SecondaryAiSidebar
            canRun={canRun}
            error={error}
            isApproving={isApproving}
            isBusy={isBusy}
            isGenerating={isGenerating}
            isRejecting={isRejecting}
            onApprove={approveProposal}
            onGenerate={generateProposal}
            onHide={() => setIsSecondarySidebarOpen(false)}
            onPromptChange={setPrompt}
            onReject={rejectProposal}
            onReset={resetDemo}
            onResizeStart={(event) => startResizePane("secondary", event)}
            onRun={runLocal}
            prompt={prompt}
            proposal={proposal}
            proposalJob={proposalJob}
            status={status}
          />
        )}
      </main>
      <StatusBar proposal={proposal} status={status} />
    </div>
  );
}
