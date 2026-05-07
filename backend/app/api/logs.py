from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas import LogTraceResponse
from backend.app.services.log_service import get_trace_logs

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/{trace_id}", response_model=LogTraceResponse)
def api_get_logs(trace_id: str):
    return get_trace_logs(trace_id)
