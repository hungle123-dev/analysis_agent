from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.services.dataset_service import get_dataset_context, list_datasets

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("")
def api_list_datasets():
    return list_datasets()


@router.get("/{dataset_id}/context")
def api_dataset_context(dataset_id: str):
    try:
        return get_dataset_context(dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc
