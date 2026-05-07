from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas import ExecutionRequest, ExecutionResponse
from backend.app.services.execution_runner import execute_proposal

router = APIRouter(prefix="/api/executions", tags=["executions"])


@router.post("", response_model=ExecutionResponse)
def api_execute_proposal(payload: ExecutionRequest):
    return execute_proposal(payload)
