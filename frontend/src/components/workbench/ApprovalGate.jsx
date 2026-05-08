import React from "react";
import { Check, Loader2, Play, RotateCcw, X } from "lucide-react";
import { ActionButton } from "../ui/ActionButton";

export function ApprovalGate({ canRun, onApprove, onReject, onReset, onRun, status }) {
  const isRunning = status === "running";
  
  return (
    <div className="flex shrink-0 items-center justify-between gap-3 border-t border-line bg-panel px-4 py-2 max-[760px]:flex-col max-[760px]:items-stretch">
      <div>
        <p className="text-[11px] font-extrabold uppercase text-muted">Human approval gate</p>
        <p className="text-sm text-muted">
          {canRun ? "Approved code can run locally." : "Run is disabled until this code is approved."}
        </p>
      </div>
      <div className="flex flex-wrap justify-end gap-2">
        <ActionButton onClick={onReset} tone="ghost" icon={RotateCcw}>Reset</ActionButton>
        <ActionButton onClick={onReject} tone="danger" icon={X} disabled={isRunning}>Reject</ActionButton>
        <ActionButton onClick={onApprove} tone="approve" icon={Check} disabled={isRunning}>Approve</ActionButton>
        <ActionButton 
          className="run-action min-w-[120px]" 
          disabled={!canRun || isRunning} 
          onClick={onRun} 
          tone="run" 
          icon={isRunning ? Loader2 : Play}
          iconClassName={isRunning ? "animate-spin" : ""}
        >
          {isRunning ? "Running..." : "Run local"}
        </ActionButton>
      </div>
    </div>
  );
}
