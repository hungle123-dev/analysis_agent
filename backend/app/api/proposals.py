from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas import (
    ApprovalResponse,
    ApproveProposalRequest,
    CreateProposalRequest,
    ProposalResponse,
    UpdateProposalRequest,
)
from backend.app.services.proposal_service import approve_proposal, create_proposal, update_proposal

router = APIRouter(prefix="/api/ai/proposals", tags=["proposals"])


@router.post("", response_model=ProposalResponse)
def api_create_proposal(payload: CreateProposalRequest):
    return create_proposal(payload)


@router.patch("/{proposal_id}", response_model=ProposalResponse)
def api_update_proposal(proposal_id: str, payload: UpdateProposalRequest):
    return update_proposal(proposal_id, payload)


@router.post("/{proposal_id}/approve", response_model=ApprovalResponse)
def api_approve_proposal(proposal_id: str, payload: ApproveProposalRequest):
    return approve_proposal(proposal_id, payload)
