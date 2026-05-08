import React from "react";
import { ChevronDown, Database, FileText, GitCommitHorizontal } from "lucide-react";

const workflowSteps = [
  "request",
  "proposal",
  "review",
  "approval",
  "local run",
  "audit log"
];

export function DatasetSidebar({ activeDatasetId, dataset, datasets, onDatasetChange }) {
  const columns = dataset.columns ?? [];

  return (
    <aside className="min-w-0 overflow-auto border-r border-line bg-shell text-sm max-[760px]:hidden">
      <ExplorerSection title="Datasets">
        <div className="grid gap-0.5">
          {datasets.map((item) => (
            <button
              className={`flex min-w-0 items-center gap-2 px-3 py-1.5 text-left ${
                item.id === activeDatasetId ? "bg-accent/35 text-text-main" : "text-muted hover:bg-white/[0.045]"
              }`}
              key={item.id}
              onClick={() => onDatasetChange(item.id)}
            >
              <Database size={15} className="shrink-0 text-data-blue" />
              <span className="truncate">{item.name}</span>
              <span className="ml-auto shrink-0 text-[11px] text-dim">{item.rows}</span>
            </button>
          ))}
        </div>
      </ExplorerSection>

      <ExplorerSection title="Schema">
        {columns.length === 0 ? (
          <div className="px-3 py-2 text-xs text-dim">No dataset context loaded.</div>
        ) : (
          <div className="grid gap-0.5">
            {columns.map((column) => (
              <div className="grid grid-cols-[18px_minmax(0,1fr)_auto] items-center gap-1 px-3 py-1.5 hover:bg-white/[0.035]" key={column.name}>
                <FileText size={14} className="text-dim" />
                <span className="truncate font-medium">{column.name}</span>
                <span className="text-[11px] text-mint">{column.dtype}</span>
                <span className="col-span-3 ml-5 text-[11px] text-dim">
                  {column.nulls ?? column.nullable_count ?? 0} null values
                </span>
              </div>
            ))}
          </div>
        )}
      </ExplorerSection>

      <ExplorerSection title="Workflow">
        <div className="grid gap-0.5 px-2 py-1">
          {workflowSteps.map((step, index) => (
            <div className="flex items-center gap-2 px-1 py-1 text-xs text-muted" key={step}>
              <GitCommitHorizontal size={14} className={index < 3 ? "text-data-blue" : "text-dim"} />
              <span>{step}</span>
            </div>
          ))}
        </div>
      </ExplorerSection>
    </aside>
  );
}

function ExplorerSection({ children, title }) {
  return (
    <section className="border-b border-line">
      <div className="flex h-7 items-center gap-1 bg-panel-2 px-2 text-[11px] font-bold uppercase tracking-wide text-muted">
        <ChevronDown size={14} />
        {title}
      </div>
      <div className="py-1">{children}</div>
    </section>
  );
}
