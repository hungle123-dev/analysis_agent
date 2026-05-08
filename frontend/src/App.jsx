import React, { useEffect, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import { api } from "./api/client";

import { ActivityBar } from "./components/workbench/ActivityBar";
import { GlobalCommandBar } from "./components/workbench/GlobalCommandBar";
import { DatasetSidebar } from "./components/workbench/DatasetSidebar";
import { ProposalHeader } from "./components/workbench/ProposalHeader";
import { ApprovalGate } from "./components/workbench/ApprovalGate";
import { Inspector } from "./components/workbench/Inspector/Inspector";
import { EditorTabs } from "./components/workbench/EditorTabs";
import { BottomPanel } from "./components/workbench/BottomPanel";
import { StatusBar } from "./components/workbench/StatusBar";

const EMPTY_CODE = `# Code proposal will appear here after AI generates it.
# AI-generated code must be reviewed, edited if needed, and approved before local execution.`;

const EMPTY_DATASET = {
  id: "",
  name: "No dataset loaded",
  rows: 0,
  status: "unavailable",
  columns: []
};

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
      setError(err.message);
    }
  }

  function updateCode(value) {
    setCode(value ?? "");
    if (["pending_review", "approved", "succeeded"].includes(status)) setStatus("edited");
  }

  async function approveProposal() {
    if (!proposal) return;
    setError("");
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
      setError(err.message);
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
    setError("");
  }

  return (
    <div className="grid h-screen min-h-[720px] grid-rows-[48px_minmax(0,1fr)_24px] overflow-hidden bg-ink text-text-main">
      <GlobalCommandBar 
        activeDatasetId={activeDatasetId} 
        datasets={datasets}
        onDatasetChange={setActiveDatasetId}
        prompt={prompt}
        onPromptChange={setPrompt}
        onGenerate={generateProposal}
        status={status}
      />

      <main className="grid min-h-0 min-w-0 grid-cols-[48px_272px_minmax(520px,1fr)_360px] max-[1180px]:grid-cols-[48px_248px_minmax(0,1fr)] max-[760px]:block max-[760px]:h-auto">
        <ActivityBar onSelectInspector={setInspectorTab} />
        <DatasetSidebar dataset={activeDataset} />

        <section className="grid min-h-0 min-w-0 grid-rows-[auto_minmax(0,1fr)_230px_auto] overflow-hidden border-r border-line bg-editor max-[760px]:min-h-screen">
          <ProposalHeader proposal={proposal} />
          {error && <div className="border-y border-rose-soft/30 bg-rose-soft/10 px-4 py-2 text-sm text-[#ffd4da]">{error}</div>}

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

          <BottomPanel
            activeTab={inspectorTab}
            error={error}
            events={events}
            executionResult={executionResult}
            hasResult={hasResult}
            onTabChange={setInspectorTab}
          />

          <ApprovalGate
            canRun={canRun}
            onApprove={approveProposal}
            onReject={rejectProposal}
            onReset={resetDemo}
            onRun={runLocal}
            status={status}
          />
        </section>

        <Inspector
          activeTab={inspectorTab}
          events={events}
          executionResult={executionResult}
          hasResult={hasResult}
          onTabChange={setInspectorTab}
        />
      </main>
      <StatusBar dataset={activeDataset} proposal={proposal} status={status} />
    </div>
  );
}
