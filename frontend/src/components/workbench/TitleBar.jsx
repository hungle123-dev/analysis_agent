import React from "react";
import { PanelBottom, PanelLeft, PanelRight, Search } from "lucide-react";

const menus = ["File", "Edit", "View", "Run", "Terminal", "Help"];

export function TitleBar({
  isBottomPanelOpen,
  isPrimarySidebarOpen,
  isSecondarySidebarOpen,
  onToggleBottomPanel,
  onTogglePrimarySidebar,
  onToggleSecondarySidebar
}) {
  return (
    <header className="grid h-9 grid-cols-[auto_minmax(140px,520px)_auto] items-center gap-2 border-b border-line bg-titlebar px-2 text-xs text-muted">
      <div className="flex items-center gap-3">
        <span className="px-1 font-semibold text-data-blue">AI</span>
        <nav className="flex items-center gap-1 max-[720px]:hidden">
          {menus.map((item) => (
            <button className="px-2 py-1 hover:bg-white/[0.07] hover:text-text-main" key={item}>
              {item}
            </button>
          ))}
        </nav>
      </div>

      <div className="mx-auto flex h-6 w-full items-center gap-2 border border-line bg-editor px-2 text-dim">
        <Search size={14} />
        <span className="truncate">analysis-agent - AI Analysis Workbench</span>
      </div>

      <div className="ml-auto flex items-center gap-1">
        <span className="hidden text-dim xl:inline">Layout</span>
        <LayoutButton active={isPrimarySidebarOpen} icon={PanelLeft} label="Toggle primary sidebar" onClick={onTogglePrimarySidebar} />
        <LayoutButton active={isBottomPanelOpen} icon={PanelBottom} label="Toggle bottom panel" onClick={onToggleBottomPanel} />
        <LayoutButton active={isSecondarySidebarOpen} icon={PanelRight} label="Toggle chat sidebar" onClick={onToggleSecondarySidebar} />
        <span className="ml-2 hidden text-dim lg:inline">Human-in-the-loop</span>
      </div>
    </header>
  );
}

function LayoutButton({ active, icon: Icon, label, onClick }) {
  return (
    <button
      aria-pressed={active}
      aria-label={label}
      className={`grid h-6 w-7 place-items-center border border-transparent hover:bg-white/[0.07] hover:text-text-main ${
        active ? "text-text-main" : "text-dim"
      }`}
      onClick={onClick}
      title={label}
    >
      <Icon size={15} />
    </button>
  );
}
