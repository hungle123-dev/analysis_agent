from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import uuid

from fastapi import HTTPException

from backend.app.core.env import load_local_env
from backend.app.db.storage import append_event, connect, now_iso, row_to_proposal
from backend.app.schemas import (
    ApprovalResponse,
    ApproveProposalRequest,
    CreateProposalRequest,
    DatasetContext,
    ProposalJobResponse,
    ProposalResponse,
    RejectProposalRequest,
    UpdateProposalRequest,
)
from backend.app.services.dataset_service import get_dataset_context
from backend.app.services.dataset_capabilities import (
    analysis_suggestions,
    infer_dataset_capabilities,
    normalize_text,
    serialize_capabilities,
)
from backend.app.services.analysis_intent import plan_analysis_request
from backend.app.services.llm_provider import ProposalDraft, get_llm_provider
from backend.app.services.policy_checker import validate_code


def _proposal_job_max_concurrency() -> int:
    load_local_env()
    try:
        return max(1, int(os.getenv("PROPOSAL_JOB_MAX_CONCURRENCY", "1")))
    except ValueError:
        return 1


_JOB_THREADS: dict[str, threading.Thread] = {}
_JOB_THREADS_LOCK = threading.Lock()
_JOB_SEMAPHORE = threading.BoundedSemaphore(_proposal_job_max_concurrency())


def create_proposal(payload: CreateProposalRequest) -> ProposalResponse:
    try:
        context = get_dataset_context(payload.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
    trace_id = f"trace_{uuid.uuid4().hex[:8]}"
    draft = build_preflight_draft(payload, context)
    provider = None
    provider_name = "schema_preflight"
    if draft is None:
        provider = get_llm_provider()
        provider_name = provider.name
        try:
            draft = provider.create_proposal(payload, context)
        except RuntimeError as exc:
            if _should_fallback_to_mock(provider.name):
                from backend.app.services.mock_llm_provider import MockLLMProvider

                fallback_provider = MockLLMProvider()
                draft = fallback_provider.create_proposal(payload, context)
                append_event(
                    trace_id,
                    "ai.proposal.fallback_to_mock",
                    "system",
                    {"from_provider": provider.name, "reason": str(exc)},
                )
                provider_name = fallback_provider.name
            else:
                append_event(
                    trace_id,
                    "ai.proposal.generation_failed",
                    "system",
                    {"provider": provider.name, "error": str(exc)},
                )
                raise HTTPException(status_code=503, detail=str(exc)) from exc

    draft = _normalize_runtime_contract_code(draft)
    if provider is not None and provider_name != "mock" and _has_syntax_error(draft):
        try:
            retry_draft = provider.create_proposal(payload, context)
            retry_draft = _normalize_runtime_contract_code(retry_draft)
            if not _has_syntax_error(retry_draft):
                draft = retry_draft
                append_event(
                    trace_id,
                    "ai.proposal.syntax_retry_succeeded",
                    "system",
                    {"provider": provider.name},
                )
        except RuntimeError as exc:
            append_event(
                trace_id,
                "ai.proposal.syntax_retry_failed",
                "system",
                {"provider": provider.name, "error": str(exc)},
            )
    now = now_iso()
    generation_metadata = draft.metadata or {}
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO proposals(
              proposal_id, trace_id, session_id, dataset_id, user_request, ai_code, edited_code,
              explanation, summary, assumptions_json, risk_flags_json, expected_outputs_json,
              status, code_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, 'pending_review', NULL, ?, ?)
            """,
            (
                proposal_id,
                trace_id,
                payload.session_id,
                payload.dataset_id,
                payload.user_request,
                draft.code,
                draft.explanation,
                draft.summary,
                json.dumps(draft.assumptions),
                json.dumps(draft.risk_flags),
                json.dumps(draft.expected_outputs),
                now,
                now,
            ),
        )

    append_event(trace_id, "ai.request.created", _default_actor_id(), payload.model_dump())
    append_event(
        trace_id,
        "ai.proposal.generated",
        "ai",
        {"proposal_id": proposal_id, "provider": provider_name, **generation_metadata},
    )
    return get_proposal(proposal_id)


def build_preflight_draft(payload: CreateProposalRequest, context: DatasetContext) -> ProposalDraft | None:
    if payload.mode != "generate_code":
        return None

    request_text = normalize_text(payload.user_request)
    capabilities = infer_dataset_capabilities(context)
    analysis_plan = plan_analysis_request(request_text, capabilities)
    missing_reasons = analysis_plan.missing_reasons

    if not missing_reasons:
        return None

    column_names = [column.name for column in context.columns]
    suggestions = analysis_suggestions(context)
    suggestions_text = "; ".join(suggestions) if suggestions else "chọn lại câu hỏi dựa trên các cột có thật trong dataset"
    missing_text = "; ".join(missing_reasons)
    available_columns = ", ".join(column_names)

    code = f'''# Đoạn code này không vẽ biểu đồ vì schema hiện tại không đủ cột để thực hiện đúng yêu cầu.
# Mục tiêu là hiển thị lý do rõ ràng để con người quyết định câu hỏi phân tích mới.
work_df = df.copy()
available_columns = list(work_df.columns)

print("KHÔNG THỂ THỰC HIỆN CHÍNH XÁC YÊU CẦU PHÂN TÍCH.")
print("Lý do: {missing_text}.")
print("Dataset đang có các cột:")
print(", ".join(available_columns))
print("Gợi ý phân tích thay thế: {suggestions_text}.")
'''

    return ProposalDraft(
        summary=(
            "Yêu cầu hiện tại chưa thể thực hiện chính xác với dataset đang chọn vì "
            f"{missing_text}. Backend tạo proposal text-only để tránh AI tự bịa cột hoặc tự vẽ biểu đồ sai."
        ),
        code=code,
        explanation=(
            "Đoạn code này chỉ tạo bản sao dữ liệu, in ra lý do không thể thực hiện đúng yêu cầu, "
            "liệt kê các cột thật đang có và gợi ý hướng phân tích thay thế. Code không tạo biểu đồ "
            "vì schema chưa có đủ cột phù hợp với yêu cầu."
        ),
        assumptions=[
            "Không tự suy diễn cột gần giống thành đúng khái niệm người dùng yêu cầu nếu schema không xác nhận.",
            "Không tự tạo cột thời gian/doanh thu/nhóm phân tích nếu dataset không có cột phù hợp.",
            "Người dùng cần chọn lại câu hỏi phân tích dựa trên các cột thật trong schema.",
        ],
        risk_flags=["needs_human_check"],
        expected_outputs=["text"],
        metadata={
            "preflight_reason": "missing_required_schema_columns",
            "missing_reasons": missing_reasons,
            "analysis_intents": analysis_plan.intent_names,
            "recommended_strategy": analysis_plan.recommended_strategy,
            "available_columns": column_names,
            "dataset_capabilities": serialize_capabilities(capabilities),
        },
    )


def _normalize_runtime_contract_code(draft: ProposalDraft) -> ProposalDraft:
    """Loại bỏ các dòng luôn sai với runtime contract trước khi người dùng duyệt."""
    code_lines: list[str] = []
    removed: list[str] = []
    for line in draft.code.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"from\s+pathlib\s+import\s+Path", stripped):
            removed.append(stripped)
            continue
        if re.fullmatch(r"import\s+pathlib(\s+as\s+\w+)?", stripped):
            removed.append(stripped)
            continue
        if re.match(r"^outputs_dir\s*=", stripped):
            removed.append(stripped)
            continue
        code_lines.append(line)

    if not removed:
        return draft

    metadata = {**(draft.metadata or {}), "runtime_contract_normalized": removed}
    assumptions = [
        *draft.assumptions,
        "Backend đã loại bỏ các dòng import pathlib/gán lại outputs_dir vì outputs_dir là biến runtime được cấp sẵn.",
    ]
    return ProposalDraft(
        summary=draft.summary,
        code="\n".join(code_lines).strip() + "\n",
        explanation=draft.explanation,
        assumptions=assumptions,
        risk_flags=draft.risk_flags,
        expected_outputs=draft.expected_outputs,
        metadata=metadata,
    )


def _has_syntax_error(draft: ProposalDraft) -> bool:
    return any(issue["code"] == "syntax_error" for issue in validate_code(draft.code))


def create_proposal_job(payload: CreateProposalRequest) -> ProposalJobResponse:
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    now = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO proposal_jobs(
              job_id, status, session_id, dataset_id, user_request, mode,
              trace_id, proposal_id, error, created_at, updated_at
            )
            VALUES (?, 'queued', ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
            """,
            (job_id, payload.session_id, payload.dataset_id, payload.user_request, payload.mode, now, now),
        )

    thread = threading.Thread(target=_run_proposal_job, args=(job_id, payload), daemon=True)
    with _JOB_THREADS_LOCK:
        _JOB_THREADS[job_id] = thread
    thread.start()
    return get_proposal_job(job_id)


def get_proposal_job(job_id: str) -> ProposalJobResponse:
    with connect() as conn:
        row = conn.execute("SELECT * FROM proposal_jobs WHERE job_id = ?", (job_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Proposal job not found")
    return ProposalJobResponse(
        job_id=row["job_id"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        dataset_id=row["dataset_id"],
        trace_id=row["trace_id"],
        proposal_id=row["proposal_id"],
        error=row["error"],
    )


def _run_proposal_job(job_id: str, payload: CreateProposalRequest) -> None:
    try:
        with _JOB_SEMAPHORE:
            _update_proposal_job(job_id, status="running")
            try:
                proposal = create_proposal(payload)
            except Exception as exc:
                _update_proposal_job(job_id, status="failed", error=str(exc))
                return
            _update_proposal_job(
                job_id,
                status="succeeded",
                proposal_id=proposal.proposal_id,
                trace_id=proposal.trace_id,
            )
    finally:
        with _JOB_THREADS_LOCK:
            _JOB_THREADS.pop(job_id, None)


def _update_proposal_job(
    job_id: str,
    *,
    status: str,
    proposal_id: str | None = None,
    trace_id: str | None = None,
    error: str | None = None,
) -> None:
    updates = ["status = ?", "updated_at = ?"]
    values: list[str | None] = [status, now_iso()]
    if proposal_id is not None:
        updates.append("proposal_id = ?")
        values.append(proposal_id)
    if trace_id is not None:
        updates.append("trace_id = ?")
        values.append(trace_id)
    if error is not None:
        updates.append("error = ?")
        values.append(error)

    values.append(job_id)
    with connect() as conn:
        conn.execute(f"UPDATE proposal_jobs SET {', '.join(updates)} WHERE job_id = ?", values)


def update_proposal(proposal_id: str, payload: UpdateProposalRequest) -> ProposalResponse:
    proposal = get_proposal_row(proposal_id)
    if proposal["status"] == "running":
        raise HTTPException(status_code=409, detail="Cannot edit a proposal while execution is running")

    errors = validate_code(payload.edited_code)
    if errors:
        append_event(proposal["trace_id"], "ai.proposal.validation_failed", "system", {"errors": errors})
        raise HTTPException(status_code=400, detail={"policy_errors": errors})

    with connect() as conn:
        conn.execute(
            "UPDATE proposals SET edited_code = ?, status = 'edited', updated_at = ? WHERE proposal_id = ?",
            (payload.edited_code, now_iso(), proposal_id),
        )
    append_event(proposal["trace_id"], "ai.proposal.edited", payload.edited_by, {"proposal_id": proposal_id})
    return get_proposal(proposal_id)


def approve_proposal(proposal_id: str, payload: ApproveProposalRequest) -> ApprovalResponse:
    proposal = get_proposal_row(proposal_id)
    if proposal["status"] in {"running", "succeeded"}:
        raise HTTPException(status_code=409, detail=f"Cannot approve proposal with status {proposal['status']}")

    code = proposal["edited_code"] or proposal["ai_code"]
    errors = validate_code(code)
    if errors:
        append_event(proposal["trace_id"], "ai.proposal.validation_failed", "system", {"errors": errors})
        raise HTTPException(status_code=400, detail={"policy_errors": errors})

    code_hash = hash_code(code)
    if proposal["status"] == "approved" and proposal["code_hash"] == code_hash:
        return ApprovalResponse(proposal_id=proposal_id, status="approved", code_hash=code_hash)

    approval_id = f"appr_{uuid.uuid4().hex[:8]}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO approvals(approval_id, proposal_id, approved_by, approved_at, approval_note, code_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (approval_id, proposal_id, payload.approved_by, now_iso(), payload.approval_note, code_hash),
        )
        conn.execute(
            "UPDATE proposals SET status = 'approved', code_hash = ?, updated_at = ? WHERE proposal_id = ?",
            (code_hash, now_iso(), proposal_id),
        )
    append_event(
        proposal["trace_id"],
        "ai.approval.approved",
        payload.approved_by,
        {"proposal_id": proposal_id, "approval_id": approval_id, "code_hash": code_hash},
    )
    return ApprovalResponse(proposal_id=proposal_id, status="approved", code_hash=code_hash)


def reject_proposal(proposal_id: str, payload: RejectProposalRequest) -> ProposalResponse:
    proposal = get_proposal_row(proposal_id)
    if proposal["status"] in {"running", "succeeded"}:
        raise HTTPException(status_code=409, detail=f"Cannot reject proposal with status {proposal['status']}")

    with connect() as conn:
        conn.execute(
            "UPDATE proposals SET status = 'rejected', code_hash = NULL, updated_at = ? WHERE proposal_id = ?",
            (now_iso(), proposal_id),
        )
    append_event(
        proposal["trace_id"],
        "ai.approval.rejected",
        payload.rejected_by,
        {"proposal_id": proposal_id, "reason": payload.rejection_reason},
    )
    return get_proposal(proposal_id)


def get_proposal_row(proposal_id: str):
    with connect() as conn:
        row = conn.execute("SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return row


def get_proposal(proposal_id: str) -> ProposalResponse:
    return ProposalResponse(**row_to_proposal(get_proposal_row(proposal_id)))


def hash_code(code: str) -> str:
    return "sha256:" + hashlib.sha256(code.encode("utf-8")).hexdigest()


def _should_fallback_to_mock(provider_name: str) -> bool:
    if provider_name == "mock":
        return False
    return os.getenv("AI_FALLBACK_TO_MOCK_ON_ERROR", "false").strip().lower() in {"1", "true", "yes", "on"}


def _default_actor_id() -> str:
    return os.getenv("DEFAULT_ACTOR_ID", "student_01")
