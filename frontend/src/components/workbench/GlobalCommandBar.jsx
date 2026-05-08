import React from "react";
import { Database, Sparkles, Send } from "lucide-react";
import { StatusBadge } from "../ui/StatusBadge";

export function GlobalCommandBar({ activeDatasetId, datasets, onDatasetChange, prompt, onPromptChange, onGenerate, status }) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-line bg-panel px-3">
      <div className="flex items-center gap-2 shrink-0">
        <Database size={16} className="text-data-blue" />
        <select
          value={activeDatasetId}
          onChange={(e) => onDatasetChange(e.target.value)}
          className="cursor-pointer bg-transparent text-sm font-semibold outline-none"
        >
          {datasets.map((d) => (
            <option key={d.id} value={d.id} className="bg-panel">
              {d.name}
            </option>
          ))}
        </select>
      </div>

      <div className="h-6 w-px shrink-0 bg-line" />

      <div className="flex flex-1 items-center gap-2 border border-line bg-editor px-3 py-1.5 transition-colors focus-within:border-accent">
        <Sparkles className="text-violet" size={16} />
        <input
          className="min-w-0 flex-1 bg-transparent text-sm outline-none"
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="What do you want to analyze?"
          aria-label="Analysis request"
        />
        <button className="flex items-center gap-1.5 bg-accent px-2.5 py-1 text-xs font-semibold text-white transition-opacity hover:opacity-90" onClick={onGenerate}>
          <Send size={12} />
          Generate
        </button>
      </div>
      
      <div className="ml-auto shrink-0">
         <StatusBadge status={status} />
      </div>
    </header>
  );
}
