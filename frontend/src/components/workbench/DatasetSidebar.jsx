import React from "react";
import { Panel } from "../ui/Panel";

export function DatasetSidebar({ dataset }) {
  const columns = dataset.columns ?? [];

  return (
    <aside className="min-w-0 overflow-auto border-r border-line bg-shell p-3 max-[760px]:hidden">
      <div className="mb-4">
        <p className="text-[11px] font-extrabold uppercase text-muted">Context</p>
        <h2 className="text-lg font-bold">Data & Traces</h2>
      </div>

      <Panel title="Schema" meta={`${columns.length} cols`}>
        <div className="grid gap-1.5">
          {columns.map((column) => (
            <div className="grid grid-cols-[minmax(0,1fr)_auto] bg-black/20 px-2 py-2" key={column.name}>
              <span className="truncate text-sm font-semibold">{column.name}</span>
              <span className="text-xs text-mint">{column.dtype}</span>
              <small className="col-span-2 text-xs text-dim">
                {column.nulls ?? column.nullable_count ?? 0} null
              </small>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Workflow" meta="local">
        <div className="grid gap-1.5 text-xs">
          {["Request received", "Proposal generated", "Human review required", "Local execution gated"].map((step) => (
            <div className="bg-white/[0.035] px-2 py-1.5 text-muted" key={step}>
              {step}
            </div>
          ))}
        </div>
      </Panel>
    </aside>
  );
}
