import React from "react";
import Editor, { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";

self.MonacoEnvironment = {
  getWorker() {
    return new EditorWorker();
  }
};

loader.config({ monaco });

export default function ProposalCodeEditor({ code, onChange, readOnly }) {
  return (
    <Editor
      height="100%"
      language="python"
      theme="vs-dark"
      value={code}
      onChange={onChange}
      loading={<div className="grid h-full place-items-center bg-[#111112] text-muted">Preparing editor...</div>}
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        fontFamily: "Cascadia Code, Consolas, monospace",
        lineNumbersMinChars: 3,
        padding: { top: 12, bottom: 12 },
        readOnly,
        scrollBeyondLastLine: false,
        wordWrap: "on"
      }}
    />
  );
}
