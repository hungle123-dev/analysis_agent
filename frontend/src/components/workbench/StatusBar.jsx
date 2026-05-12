import React from "react";
import { Braces, GitBranch, ShieldCheck } from "lucide-react";

export function StatusBar({ proposal, status }) {
  return (
    <footer className="flex h-6 shrink-0 items-center justify-between border-t border-[#005a9e] bg-status px-2 text-[11px] text-white">
      <div className="flex min-w-0 items-center gap-4">
        <span className="flex items-center gap-1">
          <GitBranch size={13} />
          main
        </span>
        <span className="hidden items-center gap-1 sm:flex">
          <ShieldCheck size={13} />
          {status}
        </span>
      </div>
      <div className="flex shrink-0 items-center gap-4">
        <span className="hidden md:inline">{proposal?.code_hash ? proposal.code_hash.slice(0, 18) : "chưa phê duyệt"}</span>
        <span className="flex items-center gap-1">
          <Braces size={13} />
          Python
        </span>
      </div>
    </footer>
  );
}
