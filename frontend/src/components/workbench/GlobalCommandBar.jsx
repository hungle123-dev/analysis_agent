import React from "react";
import { Database, Sparkles, Send } from "lucide-react";
import { StatusBadge } from "../ui/StatusBadge";

export function GlobalCommandBar({ activeDatasetId, datasets, onDatasetChange, prompt, onPromptChange, onGenerate, status }) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-4 border-b border-white/10 bg-panel px-4">
      <div className="flex items-center gap-2 shrink-0">
        <Database size={16} className="text-data-blue" />
        <select
          value={activeDatasetId}
          onChange={(e) => onDatasetChange(e.target.value)}
          className="bg-transparent text-sm font-semibold outline-none cursor-pointer"
        >
          {datasets.map((d) => (
            <option key={d.id} value={d.id} className="bg-panel">
              {d.name}
            </option>
          ))}
        </select>
      </div>

      <div className="h-6 w-px bg-white/10 shrink-0" />

      <div className="flex flex-1 items-center gap-2 rounded-lg border border-white/10 bg-ink px-3 py-1.5 focus-within:border-violet/50 transition-colors">
        <Sparkles className="text-violet" size={16} />
        <input
          className="min-w-0 flex-1 bg-transparent text-sm outline-none"
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="What do you want to analyze?"
          aria-label="Analysis request"
        />
        <button className="flex items-center gap-1.5 rounded-md bg-mint px-2.5 py-1 text-xs font-semibold text-ink transition-opacity hover:opacity-90" onClick={onGenerate}>
          <Send size={12} />
          Generate
        </button>
      </div>
      
      <div className="shrink-0 ml-auto">
         <StatusBadge status={status} />
      </div>
    </header>
  );
}
