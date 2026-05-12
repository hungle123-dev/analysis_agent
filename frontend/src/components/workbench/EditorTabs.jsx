import React from "react";
import { Code2, FileText, X } from "lucide-react";

export function EditorTabs({ lineCount, proposalId }) {
  return (
    <div className="flex h-9 shrink-0 items-center justify-between border-b border-line bg-tabs text-xs text-muted">
      <div className="flex h-full min-w-0">
        <div className="flex h-full min-w-[164px] items-center gap-2 border-r border-line border-t border-t-accent bg-editor px-3 text-text-main">
          <Code2 size={14} className="text-data-blue" />
          <span className="truncate">proposal.py</span>
          <X size={13} className="ml-auto text-dim" />
        </div>
        <div className="hidden h-full items-center gap-2 border-r border-line px-3 text-dim md:flex">
          <FileText size={14} />
          <span>policy.json</span>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-3 px-3">
        <span>{lineCount} dòng</span>
        <code className="hidden text-dim sm:inline">{proposalId ?? "chưa có proposal"}</code>
      </div>
    </div>
  );
}
