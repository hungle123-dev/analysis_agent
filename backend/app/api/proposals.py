from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas import (
    ApprovalResponse,
    ApproveProposalRequest,
    CreateProposalRequest,
    ProposalJobResponse,
    ProposalResponse,
    RejectProposalRequest,
    UpdateProposalRequest,
)
from backend.app.services.proposal_service import (
    approve_proposal,
    create_proposal,
    create_proposal_job,
    get_proposal,
    get_proposal_job,
    reject_proposal,
    update_proposal,
)

router = APIRouter(prefix="/api/ai/proposals", tags=["proposals"])


@router.post("", response_model=ProposalResponse)
def api_create_proposal(payload: CreateProposalRequest):
    return create_proposal(payload)


@router.post("/jobs", response_model=ProposalJobResponse)
def api_create_proposal_job(payload: CreateProposalRequest):
    return create_proposal_job(payload)


@router.get("/jobs/{job_id}", response_model=ProposalJobResponse)
def api_get_proposal_job(job_id: str):
    return get_proposal_job(job_id)


@router.get("/{proposal_id}", response_model=ProposalResponse)
def api_get_proposal(proposal_id: str):
    return get_proposal(proposal_id)


@router.patch("/{proposal_id}", response_model=ProposalResponse)
def api_update_proposal(proposal_id: str, payload: UpdateProposalRequest):
    return update_proposal(proposal_id, payload)


@router.post("/{proposal_id}/approve", response_model=ApprovalResponse)
def api_approve_proposal(proposal_id: str, payload: ApproveProposalRequest):
    return approve_proposal(proposal_id, payload)


@router.post("/{proposal_id}/reject", response_model=ProposalResponse)
def api_reject_proposal(proposal_id: str, payload: RejectProposalRequest):
    return reject_proposal(proposal_id, payload)
