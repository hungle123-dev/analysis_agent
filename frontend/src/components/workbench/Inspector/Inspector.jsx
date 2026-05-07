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
    <aside className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] bg-shell p-4 max-[1100px]:hidden">
      <div className="mb-3 flex rounded-lg border border-white/10 bg-black/20 p-1">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-2 py-2 text-sm transition-colors ${
              activeTab === id ? "bg-white/[0.08] text-text-main" : "text-muted hover:text-text-main hover:bg-white/[0.04]"
            }`}
            key={id}
            onClick={() => onTabChange(id)}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      <div className="min-h-0 overflow-auto rounded-lg border border-white/10 bg-panel p-3">
        {activeTab === "result" && <ResultTab executionResult={executionResult} hasResult={hasResult} />}
        {activeTab === "logs" && <LogsTab events={events} />}
        {activeTab === "policy" && <PolicyTab />}
      </div>
    </aside>
  );
}
