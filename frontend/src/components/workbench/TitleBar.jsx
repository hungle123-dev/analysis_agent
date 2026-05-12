import React from "react";
import { PanelBottom, PanelLeft, PanelRight } from "lucide-react";

export function TitleBar({
  isBottomPanelOpen,
  isPrimarySidebarOpen,
  isSecondarySidebarOpen,
  onToggleBottomPanel,
  onTogglePrimarySidebar,
  onToggleSecondarySidebar,
}) {
  return (
    <header className="flex h-9 min-w-0 items-center gap-3 border-b border-line bg-titlebar px-3 text-xs text-muted">
      <div className="flex min-w-0 shrink-0 items-baseline gap-2">
        <span className="font-semibold text-data-blue">AI</span>
        <span className="truncate font-medium text-text-main">Hỗ trợ phân tích</span>
      </div>

      <p className="min-w-0 flex-1 truncate text-center text-[11px] text-dim md:text-xs">
        analysis-agent · Human in Loop
      </p>

      <div className="flex shrink-0 items-center gap-1">
        <span className="hidden text-dim xl:inline">Bố cục</span>
        <LayoutButton active={isPrimarySidebarOpen} icon={PanelLeft} label="Ẩn/hiện thanh dataset" onClick={onTogglePrimarySidebar} />
        <LayoutButton active={isBottomPanelOpen} icon={PanelBottom} label="Ẩn/hiện panel dưới" onClick={onToggleBottomPanel} />
        <LayoutButton active={isSecondarySidebarOpen} icon={PanelRight} label="Ẩn/hiện thanh chat AI" onClick={onToggleSecondarySidebar} />
      </div>
    </header>
  );
}

function LayoutButton({ active, icon: Icon, label, onClick }) {
  return (
    <button
      aria-pressed={active}
      aria-label={label}
      className={`grid h-7 w-8 shrink-0 place-items-center rounded border border-transparent hover:bg-white/[0.07] hover:text-text-main ${
        active ? "text-text-main" : "text-dim"
      }`}
      onClick={onClick}
      title={label}
      type="button"
    >

      <Icon size={15} />
    </button>
  );
}
