from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str
    dtype: str
    nullable_count: int
    sample_values: list[Any] = Field(default_factory=list)


class DatasetSummary(BaseModel):
    id: str
    name: str
    rows: int
    status: str


class DatasetContext(DatasetSummary):
    columns: list[ColumnInfo]


class CreateProposalRequest(BaseModel):
    session_id: str = "demo_01"
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


class UpdateProposalRequest(BaseModel):
    edited_by: str = "student_01"
    edited_code: str


class ApproveProposalRequest(BaseModel):
    approved_by: str = "student_01"
    approval_note: str = ""


class ApprovalResponse(BaseModel):
    proposal_id: str
    status: str
    code_hash: str


class ExecutionRequest(BaseModel):
    proposal_id: str
    dataset_id: str
    code_hash: str
    requested_by: str = "student_01"


class Artifact(BaseModel):
    type: str
    name: str
    path: str


class ExecutionResponse(BaseModel):
    run_id: str
    proposal_id: str
    status: str
    stdout: str
    stderr: str
    artifacts: list[Artifact]


class LogTraceResponse(BaseModel):
    trace_id: str
    events: list[dict[str, Any]]
