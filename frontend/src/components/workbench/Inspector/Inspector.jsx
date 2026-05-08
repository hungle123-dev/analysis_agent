import React from "react";
import { BarChart3, History, ShieldCheck } from "lucide-react";
import { ResultTab } from "./ResultTab";
import { LogsTab } from "./LogsTab";
import { PolicyTab } from "./PolicyTab";

const tabs = [
  { id: "result", label: "Result", icon: BarChart3 },
  { id: "logs", label: "Logs", icon: History },
  { id: "policy", label: "Policy", icon: ShieldCheck }
];

export function Inspector({ activeTab, events, executionResult, hasResult, onTabChange }) {
  return (
    <aside className="grid min-h-0 grid-rows-[34px_minmax(0,1fr)] border-l border-line bg-shell max-[1180px]:hidden">
      <div className="flex border-b border-line bg-tabs">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            className={`flex flex-1 items-center justify-center gap-1.5 border-r border-line px-2 text-xs font-semibold uppercase transition-colors ${
              activeTab === id ? "bg-panel text-text-main" : "text-muted hover:bg-white/[0.04] hover:text-text-main"
            }`}
            key={id}
            onClick={() => onTabChange(id)}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      <div className="min-h-0 overflow-auto bg-panel p-3">
        {activeTab === "result" && <ResultTab executionResult={executionResult} hasResult={hasResult} />}
        {activeTab === "logs" && <LogsTab events={events} />}
        {activeTab === "policy" && <PolicyTab />}
      </div>
    </aside>
  );
}
