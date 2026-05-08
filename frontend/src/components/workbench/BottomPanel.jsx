import React from "react";
import { AlertCircle, BarChart3, History, ShieldCheck } from "lucide-react";
import { LogsTab } from "./Inspector/LogsTab";
import { PolicyTab } from "./Inspector/PolicyTab";
import { ResultTab } from "./Inspector/ResultTab";

const tabs = [
  { id: "result", label: "Output", icon: BarChart3 },
  { id: "logs", label: "Logs", icon: History },
  { id: "policy", label: "Policy", icon: ShieldCheck }
];

export function BottomPanel({ activeTab, error, events, executionResult, hasResult, onTabChange }) {
  return (
    <section className="grid min-h-0 grid-rows-[34px_minmax(0,1fr)] border-t border-line bg-panel">
      <div className="flex items-center justify-between border-b border-line bg-tabs px-2">
        <div className="flex h-full">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              className={`flex h-full items-center gap-1.5 border-r border-line px-3 text-xs font-semibold uppercase tracking-wide ${
                activeTab === id
                  ? "bg-panel text-text-main"
                  : "text-muted hover:bg-white/[0.035] hover:text-text-main"
              }`}
              key={id}
              onClick={() => onTabChange(id)}
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
      </div>
      <div className="min-h-0 overflow-auto p-3">
        {activeTab === "result" && <ResultTab executionResult={executionResult} hasResult={hasResult} />}
        {activeTab === "logs" && <LogsTab events={events} />}
        {activeTab === "policy" && <PolicyTab />}
      </div>
    </section>
  );
}
