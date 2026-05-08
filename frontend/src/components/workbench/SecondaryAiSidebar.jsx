import React from "react";
import { Bot, Check, Loader2, Play, RotateCcw, Send, ShieldCheck, X } from "lucide-react";
import { Chip } from "../ui/Chip";

export function SecondaryAiSidebar({
  canRun,
  error,
  onApprove,
  onGenerate,
  onHide,
  onPromptChange,
  onReject,
  onReset,
  onResizeStart,
  onRun,
  prompt,
  proposal,
  status
}) {
  const isRunning = status === "running";
  const hasProposal = Boolean(proposal);
  const outputs = proposal?.expected_outputs ?? [];
  const approveDisabled = !hasProposal || isRunning || status === "approved" || status === "succeeded";
  const rejectDisabled = !hasProposal || isRunning || status === "succeeded";

  return (
    <aside className="relative grid min-h-0 grid-rows-[35px_minmax(0,1fr)_auto] border-l border-line bg-shell max-[980px]:col-start-2 max-[980px]:row-start-2 max-[980px]:border-l-0 max-[980px]:border-t max-[760px]:min-h-[360px]">
      <button
        aria-label="Resize chat sidebar"
        className="absolute left-0 top-0 z-20 h-full w-1 cursor-col-resize bg-transparent hover:bg-accent/70 max-[980px]:hidden"
        onMouseDown={onResizeStart}
        title="Resize chat sidebar"
        type="button"
      />
      <header className="flex items-center justify-between border-b border-line bg-panel-2 px-3 text-xs text-muted">
        <div className="flex items-center gap-2 font-semibold uppercase tracking-wide">
          <Bot size={14} />
          Chat
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-[11px]">
            <ShieldCheck size={13} />
            <code className="text-data-blue">{status}</code>
          </span>
          <button
            aria-label="Hide chat sidebar"
            className="grid h-6 w-6 place-items-center text-dim hover:bg-white/[0.055] hover:text-text-main"
            onClick={onHide}
            title="Hide chat sidebar"
          >
            <X size={14} />
          </button>
        </div>
      </header>

      <div className="min-h-0 overflow-auto px-3 py-2">
        <div className="grid gap-3">
          <MessageBlock label="You" tone="user">
            {prompt}
          </MessageBlock>

          <MessageBlock label="AI proposal" tone="assistant">
            <div className="grid gap-2">
              <p>{proposal?.summary ?? "No proposal generated yet."}</p>
              <p className="text-xs leading-relaxed text-dim">
                {proposal?.explanation ?? "Ask AI to generate analysis code. The generated code opens in proposal.py for review before approval."}
              </p>

              {(proposal?.risk_flags?.length > 0 || outputs.length > 0) && (
                <div className="flex flex-wrap gap-1.5">
                  {proposal?.risk_flags?.map((flag) => (
                    <Chip key={flag}>{flag}</Chip>
                  ))}
                  {outputs.map((item) => (
                    <Chip key={item}>{item}</Chip>
                  ))}
                </div>
              )}
            </div>
          </MessageBlock>

          <div className="border border-line bg-panel px-2 py-2 text-xs text-muted">
            <div className="mb-1 flex items-center justify-between">
              <span className="font-semibold uppercase tracking-wide text-dim">Approval gate</span>
              <code className="text-data-blue">{proposal?.code_hash ? proposal.code_hash.slice(0, 12) : "unapproved"}</code>
            </div>
            <p>{gateMessage(status)}</p>
          </div>

          {error && <div className="border border-rose-soft/35 bg-rose-soft/10 px-2 py-1.5 text-xs text-rose-soft">{error}</div>}
        </div>
      </div>

      <footer className="border-t border-line bg-panel p-2">
        <div className="mb-2 grid grid-cols-[minmax(0,1fr)_auto] gap-2">
          <textarea
            className="h-16 resize-none border border-line bg-editor px-2 py-1.5 text-sm leading-snug text-text-main outline-none focus:border-accent"
            onChange={(event) => onPromptChange(event.target.value)}
            value={prompt}
          />
          <button
            aria-label="Generate proposal"
            className="inline-flex h-16 w-10 items-center justify-center border border-accent bg-accent text-white hover:bg-[#0069ad] disabled:cursor-not-allowed disabled:opacity-45"
            disabled={isRunning}
            onClick={onGenerate}
            title="Generate proposal"
          >
            <Send size={16} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-1">
          <SideAction icon={RotateCcw} label="Reset" onClick={onReset} />
          <SideAction disabled={rejectDisabled} icon={X} label="Reject" onClick={onReject} />
          <SideAction disabled={approveDisabled} icon={Check} label="Approve" onClick={onApprove} tone="approve" />
          <SideAction disabled={!canRun || isRunning} icon={isRunning ? Loader2 : Play} label={isRunning ? "Running" : "Run local"} onClick={onRun} tone="run" />
        </div>
      </footer>
    </aside>
  );
}

function gateMessage(status) {
  return (
    {
      approved: "Approved code is ready to run locally.",
      edited: "Edited code must be approved again before execution.",
      failed: "Execution failed. Inspect Output, Logs, or Policy.",
      pending_review: "Review the generated code before approving execution.",
      rejected: "Proposal was rejected before local execution.",
      running: "Approved code is running locally.",
      succeeded: "Local execution completed and artifacts were logged."
    }[status] ?? "Review proposal state before continuing."
  );
}

function MessageBlock({ children, label, tone }) {
  const toneClass = tone === "user" ? "border-line bg-editor" : "border-line bg-panel";

  return (
    <section className={`border ${toneClass}`}>
      <div className="border-b border-line px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-dim">{label}</div>
      <div className="px-2 py-2 text-sm leading-relaxed text-muted">{children}</div>
    </section>
  );
}

function SideAction({ disabled, icon: Icon, label, onClick, tone = "default" }) {
  const toneClass =
    tone === "run"
      ? "border-accent bg-accent text-white hover:bg-[#0069ad]"
      : tone === "approve"
        ? "border-mint/60 bg-mint/10 text-[#cbffef] hover:bg-mint/20"
        : "border-line bg-panel-2 text-muted hover:bg-white/[0.055] hover:text-text-main";

  return (
    <button
      className={`inline-flex h-8 items-center justify-center gap-1 border px-2 text-xs transition disabled:cursor-not-allowed disabled:opacity-40 ${toneClass}`}
      disabled={disabled}
      onClick={onClick}
    >
      <Icon size={13} className={label === "Running" ? "animate-spin" : ""} />
      <span>{label}</span>
    </button>
  );
}
