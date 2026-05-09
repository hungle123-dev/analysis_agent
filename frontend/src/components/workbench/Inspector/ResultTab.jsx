import React from "react";
import { BarChart3 } from "lucide-react";
import { EmptyState } from "../../ui/EmptyState";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

/** Hang 1: chart khong bien mat (min-height); hang 2: file + stdout, toi da 40% bang. */
const CHART_GRID_ROWS = `minmax(12.5rem, 1fr) minmax(5rem, 40%)`;

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
    <div
      className="grid h-full min-h-0 min-w-0 gap-3 overflow-auto"
      style={{ gridTemplateRows: CHART_GRID_ROWS }}
    >
      <div className="flex min-h-0 min-w-0 flex-col overflow-hidden rounded-lg border border-white/10 bg-black/20 p-3">
        <div className="mb-2 flex shrink-0 items-center justify-between text-sm font-bold">
          <span>Local chart artifact</span>
          <code className="text-xs text-data-blue">{executionResult?.run_id}</code>
        </div>
        <div className="mb-2 shrink-0 text-[11px] text-dim">
          return_code={executionResult?.return_code ?? "n/a"} | duration={executionResult?.duration_ms ?? 0}ms
        </div>
        {chartUrl ? (
          <div className="flex min-h-0 flex-1 justify-center overflow-auto rounded-md bg-black/15 p-2">
            <img
              alt={chartArtifact.name}
              title="Cuộn nếu panel thấp — ảnh giữ kích thước đọc được"
              className="mx-auto block max-h-none max-w-full object-contain [image-rendering:auto] sm:max-w-none"
              style={{
                height: "auto",
                width: "auto",
                minHeight: "10.5rem",
                minWidth: "min(252px, 100%)",
                maxHeight: "min(680px, 88vh)",
              }}
              src={chartUrl}
            />
          </div>
        ) : (
          <div className="grid min-h-[5rem] flex-1 place-items-center rounded-md border border-dashed border-white/10 text-xs text-muted">
            No chart artifact returned by this run.
          </div>
        )}
      </div>

      <div className="flex min-h-0 min-w-0 flex-col gap-2 overflow-x-hidden overflow-y-auto">
        {executionResult?.artifacts?.length > 0 && (
          <div className="grid shrink-0 gap-2">
            {executionResult.artifacts.map((artifact) => (
              <div className="rounded-md border border-white/10 bg-black/20 p-2 text-xs" key={artifact.path}>
                <div className="font-semibold text-data-blue">{artifact.name}</div>
                <div className="mt-1 truncate text-dim">{artifact.path}</div>
              </div>
            ))}
          </div>
        )}

        <pre className="max-h-[min(16rem,40vh)] min-h-[3rem] shrink-0 overflow-auto rounded-lg bg-black/35 p-3 text-xs leading-relaxed text-[#bdffcf]">
{executionResult?.stdout || "No stdout captured."}
        </pre>
        {executionResult?.stderr && (
          <pre className="max-h-[min(10rem,25vh)] shrink-0 overflow-auto rounded-lg bg-rose-soft/10 p-3 text-xs leading-relaxed text-[#ffd4da]">
{executionResult.stderr}
          </pre>
        )}
      </div>
    </div>
  );
}
