import React from "react";
import { BarChart3 } from "lucide-react";
import { EmptyState } from "../../ui/EmptyState";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function ResultTab({ executionResult, hasResult }) {
  if (!hasResult) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No local artifacts"
        detail="Approve the proposal and run it locally to produce chart, table, and stdout evidence."
      />
    );
  }

  const chartArtifact = executionResult?.artifacts?.find((artifact) => artifact.type === "chart");
  const chartUrl = chartArtifact
    ? `${API_BASE_URL}/artifacts/${chartArtifact.path.replace(/^runs\//, "")}`
    : null;

  return (
    <div className="grid gap-3">
      <div className="rounded-lg border border-white/10 bg-black/20 p-3">
        <div className="mb-3 flex items-center justify-between text-sm font-bold">
          <span>Local chart artifact</span>
          <code className="text-xs text-data-blue">{executionResult?.run_id}</code>
        </div>
        <div className="mb-2 text-[11px] text-dim">
          return_code={executionResult?.return_code ?? "n/a"} | duration={executionResult?.duration_ms ?? 0}ms
        </div>
        {chartUrl ? (
          <img alt={chartArtifact.name} className="max-h-48 w-full rounded-md object-contain" src={chartUrl} />
        ) : (
          <div className="grid h-36 place-items-center rounded-md border border-dashed border-white/10 text-xs text-muted">
            No chart artifact returned by this run.
          </div>
        )}
      </div>

      {executionResult?.artifacts?.length > 0 && (
        <div className="grid gap-2">
          {executionResult.artifacts.map((artifact) => (
            <div className="rounded-md border border-white/10 bg-black/20 p-2 text-xs" key={artifact.path}>
              <div className="font-semibold text-data-blue">{artifact.name}</div>
              <div className="mt-1 truncate text-dim">{artifact.path}</div>
            </div>
          ))}
        </div>
      )}

      <pre className="overflow-auto rounded-lg bg-black/35 p-3 text-xs leading-relaxed text-[#bdffcf]">
{executionResult?.stdout || "No stdout captured."}
      </pre>
      {executionResult?.stderr && (
        <pre className="overflow-auto rounded-lg bg-rose-soft/10 p-3 text-xs leading-relaxed text-[#ffd4da]">
{executionResult.stderr}
        </pre>
      )}
    </div>
  );
}
