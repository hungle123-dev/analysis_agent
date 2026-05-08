import React from "react";
import { BarChart3, Bot, Database, History, ShieldCheck } from "lucide-react";

const items = [
  { id: "datasets", label: "Datasets", icon: Database, active: true },
  { id: "ai", label: "AI Proposal", icon: Bot },
  { id: "results", label: "Results", icon: BarChart3 },
  { id: "logs", label: "Logs", icon: History },
  { id: "policy", label: "Policy", icon: ShieldCheck }
];

export function ActivityBar({ onSelectInspector }) {
  return (
    <nav className="flex min-h-0 w-12 shrink-0 flex-col items-center border-r border-line bg-activity py-2 max-[760px]:hidden">
      {items.map(({ id, label, icon: Icon, active }) => (
        <button
          aria-label={label}
          className={`relative grid h-11 w-full place-items-center text-muted transition hover:text-text-main ${
            active ? "text-text-main" : ""
          }`}
          key={id}
          onClick={() => {
            if (["results", "logs", "policy"].includes(id)) onSelectInspector(id === "results" ? "result" : id);
          }}
          title={label}
        >
          {active && <span className="absolute left-0 h-6 w-0.5 rounded-r bg-accent" />}
          <Icon size={20} />
        </button>
      ))}
      <div className="mt-auto h-px w-7 bg-line" />
    </nav>
  );
}
