import React from "react";
import { BarChart3 } from "lucide-react";
import { EmptyState } from "../../ui/EmptyState";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function ResultTab({ executionResult, hasResult }) {
  if (!hasResult) {
    return (
      <EmptyState
        icon={BarChart3}
        title="Chưa có artifact local"
        detail="Hãy duyệt proposal rồi chạy local để tạo biểu đồ, bảng và stdout làm bằng chứng."
      />
    );
  }

  const chartArtifact = executionResult?.artifacts?.find((artifact) => artifact.type === "chart");
  const chartUrl = chartArtifact
    ? `${API_BASE_URL}/artifacts/${chartArtifact.path.replace(/^runs\//, "")}`
    : null;

  return (
    <div className="flex flex-col gap-4">

      {/* ── Phần 1: AI nhận xét ── */}
      <div className="rounded-lg border border-white/10 bg-black/20 p-3">
        <div className="mb-2 flex items-center justify-between text-sm font-bold">
          <span>AI nhận xét từ số liệu local</span>
          <code className="text-xs text-data-blue">{executionResult?.ai_insight_status ?? "not_requested"}</code>
        </div>
        {executionResult?.ai_insight_status === "succeeded" && executionResult?.ai_insight ? (
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-text-main">
            {executionResult.ai_insight}
          </div>
        ) : executionResult?.ai_insight_status === "failed" ? (
          <div className="text-xs leading-relaxed text-rose-soft">
            AI chưa tạo được nhận xét từ số liệu local: {executionResult?.ai_insight_error || "Không rõ lỗi."}
          </div>
        ) : (
          <div className="text-xs leading-relaxed text-muted">
            Chưa yêu cầu AI nhận xét vì lần chạy này chưa có stdout/bảng/artifact thật hoặc execution chưa hoàn tất.
          </div>
        )}
      </div>

      {/* ── Phần 2: Biểu đồ ── */}
      <div className="rounded-lg border border-white/10 bg-black/20 p-3">
        <div className="mb-2 flex items-center justify-between text-sm font-bold">
          <span>Biểu đồ local</span>
          <code className="text-xs text-data-blue">{executionResult?.run_id}</code>
        </div>
        <div className="mb-3 text-[11px] text-dim">
          return_code={executionResult?.return_code ?? "n/a"} | thời gian={executionResult?.duration_ms ?? 0}ms
        </div>
        {chartUrl ? (
          <div className="flex justify-center rounded-md bg-black/15 p-2">
            <img
              alt={chartArtifact.name}
              title={chartArtifact.name}
              className="block w-full max-w-full object-contain"
              style={{ height: "auto" }}
              src={chartUrl}
            />
          </div>
        ) : (
          <div className="grid min-h-[5rem] place-items-center rounded-md border border-dashed border-white/10 text-xs text-muted">
            Lần chạy này không trả về biểu đồ.
          </div>
        )}
      </div>

      {/* ── Phần 3: Danh sách artifact ── */}
      {executionResult?.artifacts?.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-dim">Artifact</p>
          {executionResult.artifacts.map((artifact) => (
            <div className="rounded-md border border-white/10 bg-black/20 p-2 text-xs" key={artifact.path}>
              <div className="font-semibold text-data-blue">{artifact.name}</div>
              <div className="mt-1 truncate text-dim">{artifact.path}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── Phần 4: Stdout ── */}
      <div className="flex flex-col gap-1">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-dim">Stdout</p>
        <pre className="overflow-x-auto rounded-lg bg-black/35 p-3 text-xs leading-relaxed text-[#bdffcf]">
{executionResult?.stdout || "Không có stdout."}
        </pre>
      </div>

      {/* ── Phần 5: Stderr (chỉ hiện khi có lỗi) ── */}
      {executionResult?.stderr && (
        <div className="flex flex-col gap-1">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-rose-soft">Stderr</p>
          <pre className="overflow-x-auto rounded-lg bg-rose-soft/10 p-3 text-xs leading-relaxed text-[#ffd4da]">
{executionResult.stderr}
          </pre>
        </div>
      )}

    </div>
  );
}
