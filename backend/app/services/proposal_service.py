from __future__ import annotations

import hashlib
import json
import uuid

from fastapi import HTTPException

from backend.app.db.storage import append_event, connect, now_iso, row_to_proposal
from backend.app.schemas import (
    ApprovalResponse,
    ApproveProposalRequest,
    CreateProposalRequest,
    ProposalResponse,
    UpdateProposalRequest,
)
from backend.app.services.dataset_service import get_dataset_context
from backend.app.services.llm_provider import get_llm_provider
from backend.app.services.policy_checker import validate_code


def create_proposal(payload: CreateProposalRequest) -> ProposalResponse:
    try:
        context = get_dataset_context(payload.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
    trace_id = f"trace_{uuid.uuid4().hex[:8]}"
    provider = get_llm_provider()
    draft = provider.create_proposal(payload, context)
    now = now_iso()
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

    append_event(trace_id, "ai.request.created", "student_01", payload.model_dump())
    append_event(trace_id, "ai.proposal.generated", "ai", {"proposal_id": proposal_id, "provider": provider.name})
    return get_proposal(proposal_id)


def update_proposal(proposal_id: str, payload: UpdateProposalRequest) -> ProposalResponse:
    proposal = get_proposal_row(proposal_id)
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
    code = proposal["edited_code"] or proposal["ai_code"]
    errors = validate_code(code)
    if errors:
        append_event(proposal["trace_id"], "ai.proposal.validation_failed", "system", {"errors": errors})
        raise HTTPException(status_code=400, detail={"policy_errors": errors})

    code_hash = hash_code(code)
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
