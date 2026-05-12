from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from backend.app.db import storage
from backend.app.schemas import ColumnInfo, CreateProposalRequest, DatasetContext
from backend.app.services import proposal_service
from backend.app.services.proposal_service import build_preflight_draft


def _context(columns: list[ColumnInfo]) -> DatasetContext:
    return DatasetContext(
        id="vietnam_real_estate_cleaned",
        name="cleaned_vietnam_real_estate.csv",
        rows=53812,
        status="ready",
        columns=columns,
    )


def test_preflight_returns_text_only_when_monthly_revenue_columns_are_missing():
    context = _context(
        [
            ColumnInfo(name="timeline_hours", dtype="int64", nullable_count=0, sample_values=[2]),
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[12500.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Ha Noi"]),
        ]
    )
    payload = CreateProposalRequest(
        dataset_id=context.id,
        user_request="Ve bieu do doanh thu theo thang va nhan xet xu huong.",
    )

    draft = build_preflight_draft(payload, context)

    assert draft is not None
    assert draft.expected_outputs == ["text"]
    assert "needs_human_check" in draft.risk_flags
    assert "không có cột ngày/tháng" in draft.code.lower()
    assert "doanh thu" in draft.summary.lower()
    assert "plt.savefig" not in draft.code


def test_preflight_does_not_block_when_time_and_revenue_columns_exist():
    context = _context(
        [
            ColumnInfo(name="date", dtype="object", nullable_count=0, sample_values=["2025-01-05"]),
            ColumnInfo(name="revenue", dtype="int64", nullable_count=0, sample_values=[1240000]),
        ]
    )
    payload = CreateProposalRequest(
        dataset_id=context.id,
        user_request="Ve bieu do doanh thu theo thang",
    )

    assert build_preflight_draft(payload, context) is None


def test_preflight_blocks_correlation_when_dataset_has_less_than_two_numeric_columns():
    context = _context(
        [
            ColumnInfo(name="city", dtype="object", nullable_count=0, sample_values=["Ha Noi"]),
            ColumnInfo(name="segment", dtype="object", nullable_count=0, sample_values=["A"]),
        ]
    )
    payload = CreateProposalRequest(
        dataset_id=context.id,
        user_request="Kiem tra tuong quan giua cac bien so trong dataset",
    )

    draft = build_preflight_draft(payload, context)

    assert draft is not None
    assert draft.expected_outputs == ["text"]
    assert "hai cột số" in draft.summary


def test_preflight_allows_distribution_when_numeric_column_exists():
    context = _context(
        [
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[12500.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Ha Noi"]),
        ]
    )
    payload = CreateProposalRequest(
        dataset_id=context.id,
        user_request="Ve phan bo Gia_Trieu_VND",
    )

    assert build_preflight_draft(payload, context) is None


def test_preflight_allows_distribution_trend_without_calendar_column():
    context = _context(
        [
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[12500.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Ha Noi"]),
        ]
    )
    payload = CreateProposalRequest(
        dataset_id=context.id,
        user_request="Ve bieu do gia trung binh theo Tinh_Thanh va nhan xet xu huong phan bo gia.",
    )

    assert build_preflight_draft(payload, context) is None


def test_create_proposal_short_circuits_llm_when_preflight_detects_missing_columns(monkeypatch):
    context = _context(
        [
            ColumnInfo(name="timeline_hours", dtype="int64", nullable_count=0, sample_values=[2]),
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[12500.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Ha Noi"]),
        ]
    )
    runtime_dir = Path(__file__).resolve().parents[1] / ".test-runtime" / f"preflight_{uuid.uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    try:
        monkeypatch.setattr(storage, "DB_PATH", runtime_dir / "ai_logs.db")
        storage.init_db()
        monkeypatch.setattr(proposal_service, "get_dataset_context", lambda dataset_id: context)

        def fail_if_provider_is_used():
            raise AssertionError("LLM provider should not be called for deterministic schema preflight")

        monkeypatch.setattr(proposal_service, "get_llm_provider", fail_if_provider_is_used)

        proposal = proposal_service.create_proposal(
            CreateProposalRequest(
                dataset_id=context.id,
                user_request="Ve bieu do doanh thu theo thang va nhan xet xu huong.",
            )
        )

        assert proposal.status == "pending_review"
        assert proposal.expected_outputs == ["text"]
        assert "chưa thể thực hiện chính xác" in proposal.summary.lower()
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)
