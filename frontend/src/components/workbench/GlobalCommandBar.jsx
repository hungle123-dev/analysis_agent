import React from "react";
import { Sparkles, Send } from "lucide-react";

export function GlobalCommandBar({ prompt, onPromptChange, onGenerate }) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-line bg-panel px-3">
      <div className="flex w-[320px] shrink-0 items-center gap-2 text-sm font-semibold max-[760px]:hidden">
        <span className="text-data-blue">AI</span>
        <span>Analysis Workbench</span>
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
    </header>
  );
}
