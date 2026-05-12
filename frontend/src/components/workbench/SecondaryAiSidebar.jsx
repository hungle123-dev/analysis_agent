import React from "react";
import { Bot, Check, Loader2, Play, RotateCcw, Send, ShieldCheck, X } from "lucide-react";
import { Chip } from "../ui/Chip";

export function SecondaryAiSidebar({
  canRun,
  error,
  isApproving = false,
  isBusy = false,
  isGenerating = false,
  isRejecting = false,
  onApprove,
  onGenerate,
  onHide,
  onPromptChange,
  onReject,
  onReset,
  onResizeStart,
  onRun,
  prompt,
  proposal,
  proposalJob,
  status
}) {
  const isRunning = status === "running";
  const hasProposal = Boolean(proposal);
  const outputs = proposal?.expected_outputs ?? [];
  const approveDisabled = !hasProposal || isBusy || status === "approved" || status === "succeeded";
  const rejectDisabled = !hasProposal || isBusy || status === "succeeded";

  return (
    <aside className="relative grid min-h-0 grid-rows-[35px_minmax(0,1fr)_auto] border-l border-line bg-shell max-[980px]:col-start-2 max-[980px]:row-start-2 max-[980px]:border-l-0 max-[980px]:border-t max-[760px]:min-h-[360px]">
      <button
        aria-label="Kéo để thay đổi kích thước"
        className="absolute left-0 top-0 z-20 h-full w-1 touch-none cursor-col-resize bg-transparent hover:bg-accent/70 max-[980px]:hidden"
        onPointerDown={onResizeStart}
        title="Kéo để thay đổi kích thước"
        type="button"
      />
      <header className="flex items-center justify-between border-b border-line bg-panel-2 px-3 text-xs text-muted">
        <div className="flex items-center gap-2 font-semibold uppercase tracking-wide">
          <Bot size={14} />
          Trợ lý AI
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-[11px]">
            <ShieldCheck size={13} />
            <code className="text-data-blue">{status}</code>
          </span>
          <button
            aria-label="Ẩn thanh chat AI"
            className="grid h-6 w-6 place-items-center text-dim hover:bg-white/[0.055] hover:text-text-main"
            onClick={onHide}
            title="Ẩn thanh chat AI"
          >
            <X size={14} />
          </button>
        </div>
      </header>

      <div className="min-h-0 overflow-auto px-3 py-2">
        <div className="grid gap-3">
          <MessageBlock label="Yêu cầu của bạn" tone="user">
            {prompt}
          </MessageBlock>

          <MessageBlock label="Đề xuất AI" tone="assistant">
            <div className="grid gap-2">
              <p>{proposal?.summary ?? "Chưa có đề xuất nào được tạo."}</p>
              <p className="text-xs leading-relaxed text-dim">
                {proposal?.explanation ?? "Nhập yêu cầu và nhấn gửi để AI tạo code phân tích. Code sẽ mở trong proposal.py để bạn xem xét trước khi phê duyệt."}
              </p>

              {(proposal?.risk_flags?.length > 0 || outputs.length > 0) && (
                <div className="flex flex-wrap gap-1.5">
                  {proposal?.risk_flags?.map((flag) => (
                    <Chip key={flag}>{flag}</Chip>
                  ))}
                  {outputs.map((item) => (
                    <Chip key={item}>{item}</Chip>
                  ))}
                </div>
              )}
            </div>
          </MessageBlock>

          <div className="border border-line bg-panel px-2 py-2 text-xs text-muted">
            <div className="mb-1 flex items-center justify-between">
              <span className="font-semibold uppercase tracking-wide text-dim">Cổng phê duyệt</span>
              <code className="text-data-blue">{proposal?.code_hash ? proposal.code_hash.slice(0, 12) : "chưa duyệt"}</code>
            </div>
            <p>{gateMessage(status)}</p>
            {proposalJob && (
              <div className="mt-2 flex items-center justify-between border-t border-line pt-2">
                <span>Tác vụ AI</span>
                <code className="text-data-blue">{proposalJob.status}</code>
              </div>
            )}
          </div>

          {error && <div className="border border-rose-soft/35 bg-rose-soft/10 px-2 py-1.5 text-xs text-rose-soft">{error}</div>}
        </div>
      </div>

      <footer className="border-t border-line bg-panel p-2">
        <div className="mb-2 grid grid-cols-[minmax(0,1fr)_auto] gap-2">
          <textarea
            className="h-16 resize-none border border-line bg-editor px-2 py-1.5 text-sm leading-snug text-text-main outline-none focus:border-accent"
            onChange={(event) => onPromptChange(event.target.value)}
            placeholder="Nhập yêu cầu phân tích..."
            value={prompt}
          />
          <button
            aria-label="Tạo đề xuất AI"
            className="inline-flex h-16 w-10 items-center justify-center border border-accent bg-accent text-white hover:bg-[#0069ad] disabled:cursor-not-allowed disabled:opacity-45"
            disabled={isBusy}
            onClick={onGenerate}
            title="Tạo đề xuất AI"
          >
            {isGenerating ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-1">
          <SideAction disabled={isBusy} icon={RotateCcw} label="Đặt lại" onClick={onReset} />
          <SideAction disabled={rejectDisabled} icon={isRejecting ? Loader2 : X} label={isRejecting ? "Đang từ chối..." : "Từ chối"} onClick={onReject} />
          <SideAction disabled={approveDisabled} icon={isApproving ? Loader2 : Check} label={isApproving ? "Đang duyệt..." : "Phê duyệt"} onClick={onApprove} tone="approve" />
          <SideAction disabled={!canRun || isBusy} icon={isRunning ? Loader2 : Play} label={isRunning ? "Đang chạy..." : "Chạy local"} onClick={onRun} tone="run" />
        </div>
      </footer>
    </aside>
  );
}

function gateMessage(status) {
  return (
    {
      approved: "Code đã được phê duyệt, sẵn sàng chạy local.",
      edited: "Code đã chỉnh sửa cần được phê duyệt lại trước khi thực thi.",
      failed: "Thực thi thất bại. Kiểm tra tab Kết quả, Nhật ký hoặc Chính sách.",
      generating: "AI đang tạo đề xuất ở nền...",
      pending_review: "Xem xét code được tạo trước khi phê duyệt thực thi.",
      rejected: "Đề xuất đã bị từ chối trước khi chạy local.",
      running: "Code đã duyệt đang chạy local...",
      succeeded: "Thực thi local hoàn tất và artifact đã được ghi lại."
    }[status] ?? "Xem xét trạng thái đề xuất trước khi tiếp tục."
  );
}

function MessageBlock({ children, label, tone }) {
  const toneClass = tone === "user" ? "border-line bg-editor" : "border-line bg-panel";

  return (
    <section className={`border ${toneClass}`}>
      <div className="border-b border-line px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-dim">{label}</div>
      <div className="px-2 py-2 text-sm leading-relaxed text-muted">{children}</div>
    </section>
  );
}

function SideAction({ disabled, icon: Icon, label, onClick, tone = "default" }) {
  const isLoading = label === "Đang chạy..." || label === "Đang từ chối..." || label === "Đang duyệt...";
  const toneClass =
    tone === "run"
      ? "border-accent bg-accent text-white hover:bg-[#0069ad]"
      : tone === "approve"
        ? "border-mint/60 bg-mint/10 text-[#cbffef] hover:bg-mint/20"
        : "border-line bg-panel-2 text-muted hover:bg-white/[0.055] hover:text-text-main";

  return (
    <button
      className={`inline-flex h-8 items-center justify-center gap-1 border px-2 text-xs transition disabled:cursor-not-allowed disabled:opacity-40 ${toneClass}`}
      disabled={disabled}
      onClick={onClick}
    >
      <Icon size={13} className={isLoading ? "animate-spin" : ""} />
      <span>{label}</span>
    </button>
  );
}
