import React from "react";
import { ChevronDown, Database, FileText, GitCommitHorizontal } from "lucide-react";

const workflowSteps = [
  "Yêu cầu",
  "Đề xuất AI",
  "Xem xét",
  "Phê duyệt",
  "Chạy local",
  "Nhật ký (Logs)"
];

export function DatasetSidebar({ activeDatasetId, dataset, datasets, onDatasetChange, onResizeStart }) {
  const columns = dataset.columns ?? [];

  return (
    <aside className="relative min-w-0 overflow-auto border-r border-line bg-shell text-sm max-[980px]:absolute max-[980px]:inset-y-0 max-[980px]:left-11 max-[980px]:z-30 max-[980px]:w-[min(320px,calc(100vw-44px))] max-[980px]:shadow-2xl max-[760px]:left-0 max-[760px]:max-h-[72vh]">
      <ExplorerSection title="Dữ liệu">
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

      <ExplorerSection title="Cấu trúc">
        {columns.length === 0 ? (
          <div className="px-3 py-2 text-xs text-dim">Chưa tải thông tin dataset.</div>
        ) : (
          <div className="grid gap-0.5">
            {columns.map((column) => (
              <div className="grid grid-cols-[18px_minmax(0,1fr)_auto] items-center gap-1 px-3 py-1.5 hover:bg-white/[0.035]" key={column.name}>
                <FileText size={14} className="text-dim" />
                <span className="truncate font-medium">{column.name}</span>
                <span className="text-[11px] text-mint">{column.dtype}</span>
                <span className="col-span-3 ml-5 text-[11px] text-dim">
                  {column.nulls ?? column.nullable_count ?? 0} giá trị null
                </span>
              </div>
            ))}
          </div>
        )}
      </ExplorerSection>

      <ExplorerSection title="Quy trình">
        <div className="grid gap-0.5 px-2 py-1">
          {workflowSteps.map((step, index) => (
            <div className="flex items-center gap-2 px-1 py-1 text-xs text-muted" key={step}>
              <GitCommitHorizontal size={14} className={index < 3 ? "text-data-blue" : "text-dim"} />
              <span>{step}</span>
            </div>
          ))}
        </div>
      </ExplorerSection>
      <ResizeHandle ariaLabel="Kéo để thay đổi kích thước" edge="right" onResizeStart={onResizeStart} />
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

function ResizeHandle({ ariaLabel, edge, onResizeStart }) {
  return (
    <button
      aria-label={ariaLabel}
      className={`absolute top-0 z-20 h-full w-1 touch-none cursor-col-resize bg-transparent hover:bg-accent/70 ${
        edge === "right" ? "right-0" : "left-0"
      }`}
      onPointerDown={onResizeStart}
      title={ariaLabel}
      type="button"
    />
  );
}
