import React from "react";
import { AlertCircle, BarChart3, History, ShieldCheck, X } from "lucide-react";
import { LogsTab } from "./Inspector/LogsTab";
import { PolicyTab } from "./Inspector/PolicyTab";
import { ResultTab } from "./Inspector/ResultTab";

const tabs = [
  { id: "result", label: "Output", icon: BarChart3 },
  { id: "logs", label: "Logs", icon: History },
  { id: "policy", label: "Policy", icon: ShieldCheck }
];

export function BottomPanel({
  activeTab,
  error,
  events,
  executionResult,
  hasResult,
  policyIssues,
  onClose,
  onResizeStart,
  onTabChange,
}) {
  return (
    <section className="relative grid h-full min-h-0 grid-rows-[32px_minmax(0,1fr)] border-t border-line bg-panel">
      <button
        aria-label="Resize bottom panel"
        type="button"
        className="absolute -top-[3px] left-0 z-30 h-[6px] w-full touch-none cursor-row-resize border-0 bg-transparent outline-none hover:bg-accent/70 focus-visible:bg-accent/70 transition-colors"
        onPointerDown={onResizeStart}
        title="Resize panel"
      />
      <div className="flex items-center justify-between border-b border-line bg-tabs px-2">
        <div className="flex h-full">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              className={`flex h-full items-center gap-1.5 border-r border-line px-3 text-xs ${
                activeTab === id
                  ? "bg-panel text-text-main"
                  : "text-muted hover:bg-white/[0.035] hover:text-text-main"
              }`}
              key={id}
              onClick={() => onTabChange(id)}
              aria-label={`Show ${label} panel`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>
        {error && (
          <div className="flex min-w-0 items-center gap-1.5 px-2 text-xs text-rose-soft">
            <AlertCircle size={14} />
            <span className="truncate">{error}</span>
          </div>
        )}
        <button
          aria-label="Hide bottom panel"
          className="grid h-7 w-7 place-items-center text-dim hover:bg-white/[0.055] hover:text-text-main"
          onClick={onClose}
          title="Hide bottom panel"
        >
          <X size={14} />
        </button>
      </div>
      <div className="flex min-h-0 flex-col overflow-x-hidden overflow-y-auto">
        {activeTab === "result" && (
          <div className="flex h-full min-h-0 min-w-0 flex-col overflow-x-auto p-3 [-webkit-overflow-scrolling:touch]">
            <ResultTab executionResult={executionResult} hasResult={hasResult} />
          </div>
        )}
        {activeTab === "logs" && (
          <div className="h-full overflow-auto p-3">
            <LogsTab events={events} />
          </div>
        )}
        {activeTab === "policy" && (
          <div className="h-full overflow-auto p-3">
            <PolicyTab issues={policyIssues} />
          </div>
        )}
      </div>
    </section>
  );
}
