import React from "react";
import { AlertTriangle, Check } from "lucide-react";

const defaultRules = [
  ["Import allowlist", "Only pandas, numpy, matplotlib, seaborn, math, and statistics are allowed."],
  ["No shell access", "os.system, subprocess, socket, requests, urllib are blocked."],
  ["Output scoped", "Generated files must stay under outputs/{run_id}."],
  ["Approval required", "Execution rejects proposals without matching approved code hash."]
];

export function PolicyTab({ issues = [] }) {
  if (issues.length > 0) {
    return (
      <div className="grid gap-2">
        {issues.map((issue, idx) => (
          <div className="rounded-md border border-rose-soft/30 bg-rose-soft/10 p-3" key={`${issue.code}-${idx}`}>
            <div className="flex items-center gap-2 text-sm font-bold text-[#ffd4da]">
              <AlertTriangle size={14} />
              <span>{issue.code}</span>
              <code className="ml-auto text-[11px] uppercase text-rose-soft">{issue.severity}</code>
            </div>
            <p className="mt-1 text-xs leading-snug text-[#ffd4da]">{issue.message}</p>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-2">
      {defaultRules.map(([title, detail]) => (
        <div className="rounded-md border border-white/10 bg-white/[0.025] p-3" key={title}>
          <div className="flex items-center gap-2 text-sm font-bold text-[#cbffef]">
            <Check size={14} />
            {title}
          </div>
          <p className="mt-1 text-xs leading-snug text-muted">{detail}</p>
        </div>
      ))}
    </div>
  );
}
