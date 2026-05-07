import React from "react";
import { Check } from "lucide-react";

export function PolicyTab() {
  return (
    <div className="grid gap-2">
      {[
        ["Import allowlist", "Only pandas, numpy, matplotlib, seaborn, plotly are allowed."],
        ["No shell access", "os.system, subprocess, socket, requests, urllib are blocked."],
        ["Output scoped", "Generated files must stay under outputs/{run_id}."],
        ["Approval required", "Execution rejects proposals without matching approved code hash."]
      ].map(([title, detail]) => (
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
