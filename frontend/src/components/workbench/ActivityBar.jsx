import React from "react";
import { BarChart3, Database, History, ShieldCheck } from "lucide-react";

const items = [
  { id: "datasets", label: "Datasets", icon: Database },
  { id: "result", label: "Output", icon: BarChart3 },
  { id: "logs", label: "Logs", icon: History },
  { id: "policy", label: "Policy", icon: ShieldCheck }
];

export function ActivityBar({ activePanel, onSelectPanel }) {
  return (
    <nav className="row-span-2 flex min-h-0 w-12 shrink-0 flex-col items-center border-r border-line bg-activity py-2 max-[980px]:w-11 max-[760px]:hidden">
      {items.map(({ id, label, icon: Icon }) => {
        const active = id === "datasets" ? activePanel === "datasets" : activePanel === id;
        const actionLabel = id === "datasets" ? "Toggle datasets sidebar" : `Show ${label} panel`;
        return (
        <button
          aria-label={actionLabel}
          className={`relative grid h-11 w-full place-items-center text-muted transition hover:text-text-main ${
            active ? "text-text-main" : ""
          }`}
          key={id}
          onClick={() => {
            onSelectPanel(id);
          }}
          title={actionLabel}
        >
          {active && <span className="absolute left-0 h-6 w-0.5 rounded-r bg-accent" />}
          <Icon size={20} />
        </button>
        );
      })}
      <div className="mt-auto h-px w-7 bg-line" />
    </nav>
  );
}
