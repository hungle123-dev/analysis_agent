from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, Field


def _default_session_id() -> str:
    return os.getenv("DEFAULT_SESSION_ID", "demo_01")


def _default_actor_id() -> str:
    return os.getenv("DEFAULT_ACTOR_ID", "student_01")


class ColumnInfo(BaseModel):
    name: str
    dtype: str
    nullable_count: int
    sample_values: list[Any] = Field(default_factory=list)
    unique_count: int | None = None
    top_values: list[dict[str, Any]] = Field(default_factory=list)
    numeric_summary: dict[str, float | int | None] = Field(default_factory=dict)


class DatasetSummary(BaseModel):
    id: str
    name: str
    rows: int
    status: str


class DatasetContext(DatasetSummary):
    columns: list[ColumnInfo]


class CreateProposalRequest(BaseModel):
    session_id: str = Field(default_factory=_default_session_id)
    dataset_id: str
    user_request: str
    mode: Literal["generate_code", "suggestions", "explain_result"] = "generate_code"


class ProposalResponse(BaseModel):
    proposal_id: str
    trace_id: str
    dataset_id: str
    status: str
    summary: str
    code: str
    explanation: str
    assumptions: list[str]
    risk_flags: list[str]
    expected_outputs: list[str]
    code_hash: str | None = None


class ProposalJobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    created_at: str
    updated_at: str
    dataset_id: str
    trace_id: str | None = None
    proposal_id: str | None = None
    error: str | None = None


class UpdateProposalRequest(BaseModel):
    edited_by: str = Field(default_factory=_default_actor_id)
    edited_code: str


class ApproveProposalRequest(BaseModel):
    approved_by: str = Field(default_factory=_default_actor_id)
    approval_note: str = ""


class RejectProposalRequest(BaseModel):
    rejected_by: str = Field(default_factory=_default_actor_id)
    rejection_reason: str = ""


class ApprovalResponse(BaseModel):
    proposal_id: str
    status: str
    code_hash: str


class ExecutionRequest(BaseModel):
    proposal_id: str
    dataset_id: str
    code_hash: str
    requested_by: str = Field(default_factory=_default_actor_id)


class Artifact(BaseModel):
    type: str
    name: str
    path: str


class PolicyIssue(BaseModel):
    code: str
    message: str
    severity: Literal["error", "warning"] = "error"


class ExecutionResponse(BaseModel):
    run_id: str
    proposal_id: str
    status: str
    stdout: str
    stderr: str
    artifacts: list[Artifact]
    ai_insight: str | None = None
    ai_insight_status: Literal["not_requested", "succeeded", "failed"] = "not_requested"
    ai_insight_error: str | None = None
    return_code: int
    duration_ms: int
    started_at: str
    finished_at: str


class LogTraceResponse(BaseModel):
    trace_id: str
    events: list[dict[str, Any]]
