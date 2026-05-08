import React, { useEffect, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import { api } from "./api/client";

import { ActivityBar } from "./components/workbench/ActivityBar";
import { DatasetSidebar } from "./components/workbench/DatasetSidebar";
import { EditorTabs } from "./components/workbench/EditorTabs";
import { BottomPanel } from "./components/workbench/BottomPanel";
import { SecondaryAiSidebar } from "./components/workbench/SecondaryAiSidebar";
import { StatusBar } from "./components/workbench/StatusBar";
import { TitleBar } from "./components/workbench/TitleBar";

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
  const [prompt, setPrompt] = useState("Ve bieu do doanh thu theo thang va nhan xet xu huong.");
  const [code, setCode] = useState(EMPTY_CODE);
  const [status, setStatus] = useState("pending_review");
  const [events, setEvents] = useState([]);
  const [inspectorTab, setInspectorTab] = useState("logs");
  const [proposal, setProposal] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [error, setError] = useState("");
  const [policyIssues, setPolicyIssues] = useState([]);
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
  const canRun = status === "approved" && Boolean(proposal?.code_hash);

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

  function addEvent(type, actor, detail) {
    setEvents((current) => [
      ...current,
      {
        id: `evt_${String(current.length + 1).padStart(3, "0")}`,
        type,
        actor,
        detail,
        time: new Date().toLocaleTimeString("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit"
        })
      }
    ]);
  }

  async function refreshLogs(traceId) {
    if (!traceId) return;
    const logs = await api.getLogs(traceId);
    setEvents(
      logs.events.map((event) => ({
        id: event.id,
        type: event.type,
        actor: event.actor,
        time: new Date(event.time).toLocaleTimeString("en-GB"),
        detail: event.detail
      }))
    );
  }

  async function generateProposal() {
    if (!activeDatasetId) {
      setError("No registered dataset is available. Start the backend and reload datasets first.");
      return;
    }
    setError("");
    setPolicyIssues([]);
    setExecutionResult(null);
    try {
      const nextProposal = await api.createProposal({
        session_id: "demo_01",
        dataset_id: activeDatasetId,
        user_request: prompt,
        mode: "generate_code"
      });
      setProposal(nextProposal);
      setCode(nextProposal.code);
      setStatus(nextProposal.status);
      setInspectorTab("logs");
      await refreshLogs(nextProposal.trace_id);
    } catch (err) {
      setPolicyIssues(normalizePolicyIssues(err?.detail?.policy_errors));
      setError(err.message);
    }
  }

  function updateCode(value) {
    setCode(value ?? "");
    if (proposal && ["pending_review", "approved", "succeeded"].includes(status)) setStatus("edited");
  }

  async function approveProposal() {
    if (!proposal) return;
    setError("");
    setPolicyIssues([]);
    try {
      const updated = await api.updateProposal(proposal.proposal_id, {
        edited_by: "student_01",
        edited_code: code
      });
      const approval = await api.approveProposal(proposal.proposal_id, {
        approved_by: "student_01",
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
    }
  }

  function rejectProposal() {
    setStatus("rejected");
    setInspectorTab("logs");
    addEvent("ai.approval.rejected", "student_01", "Rejected proposal before execution");
  }

  async function runLocal() {
    if (!canRun || !proposal?.code_hash) return;
    setStatus("running");
    setInspectorTab("logs");
    setPolicyIssues([]);
    try {
      const result = await api.runExecution({
        proposal_id: proposal.proposal_id,
        dataset_id: activeDatasetId,
        code_hash: proposal.code_hash,
        requested_by: "student_01"
      });
      setExecutionResult(result);
      setStatus(result.status);
      setInspectorTab("result");
      await refreshLogs(proposal.trace_id);
    } catch (err) {
      setStatus("failed");
      setInspectorTab("policy");
      setPolicyIssues(normalizePolicyIssues(err?.detail?.policy_errors));
      setError(err.message);
    }
  }

  function resetDemo() {
    setCode(EMPTY_CODE);
    setEvents([]);
    setStatus("pending_review");
    setInspectorTab("logs");
    setProposal(null);
    setExecutionResult(null);
    setPolicyIssues([]);
    setError("");
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

    function onMouseMove(moveEvent) {
      if (kind === "primary") {
        setPrimarySidebarWidth(clamp(startPrimaryWidth + moveEvent.clientX - startX, 220, 420));
      }
      if (kind === "secondary") {
        setSecondarySidebarWidth(clamp(startSecondaryWidth - (moveEvent.clientX - startX), 280, 520));
      }
      if (kind === "bottom") {
        setBottomPanelHeight(clamp(startBottomHeight - (moveEvent.clientY - startY), 160, 380));
      }
    }

    function onMouseUp() {
      document.body.classList.remove("select-none", "cursor-col-resize", "cursor-row-resize");
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    }

    document.body.classList.add("select-none", kind === "bottom" ? "cursor-row-resize" : "cursor-col-resize");
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  }

  const mainGridClass = [
    "relative grid min-h-0 min-w-0",
    isBottomPanelOpen && isSecondarySidebarOpen
      ? "max-[980px]:grid-rows-[minmax(0,1fr)_320px]"
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
      ? "grid-rows-[minmax(0,1fr)_var(--bottom-panel-height)] max-[980px]:grid-rows-[minmax(0,1fr)_190px]"
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
              <Editor
                height="100%"
                language="python"
                theme="vs-dark"
                value={code}
                onChange={updateCode}
                loading={<div className="grid h-full place-items-center bg-[#111112] text-muted">Preparing editor...</div>}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  fontFamily: "Cascadia Code, Consolas, monospace",
                  lineNumbersMinChars: 3,
                  scrollBeyondLastLine: false,
                  wordWrap: "on",
                  padding: { top: 12, bottom: 12 }
                }}
              />
            </div>
          </div>

          {isBottomPanelOpen && (
            <BottomPanel
              activeTab={inspectorTab}
              error={error}
              events={events}
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
            status={status}
          />
        )}
      </main>
      <StatusBar proposal={proposal} status={status} />
    </div>
  );
}
