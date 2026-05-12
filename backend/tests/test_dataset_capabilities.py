from __future__ import annotations

from backend.app.schemas import ColumnInfo, DatasetContext
from backend.app.services.dataset_capabilities import (
    analysis_suggestions,
    infer_dataset_capabilities,
    missing_schema_reasons,
    normalize_text,
)


def _context(columns: list[ColumnInfo]) -> DatasetContext:
    return DatasetContext(id="dataset", name="dataset.csv", rows=10, status="ready", columns=columns)


def test_infer_dataset_capabilities_without_dataset_specific_branching():
    context = _context(
        [
            ColumnInfo(name="posted_date", dtype="object", nullable_count=0, sample_values=["2025-01-05"]),
            ColumnInfo(name="sale_amount", dtype="float64", nullable_count=0, sample_values=[1200.0]),
            ColumnInfo(name="region", dtype="object", nullable_count=0, sample_values=["North"]),
        ]
    )

    capabilities = infer_dataset_capabilities(context)

    assert capabilities["calendar"] == ["posted_date"]
    assert capabilities["numeric"] == ["sale_amount"]
    assert capabilities["revenue"] == ["sale_amount"]
    assert capabilities["geo"] == ["region"]


def test_missing_schema_reasons_are_shared_by_prompt_and_preflight():
    context = _context(
        [
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[12500.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Ha Noi"]),
        ]
    )
    capabilities = infer_dataset_capabilities(context)

    reasons = missing_schema_reasons(normalize_text("Ve doanh thu theo thang"), capabilities)

    assert "không có cột ngày/tháng để gom nhóm theo thời gian" in reasons
    assert "không có cột doanh thu đúng nghĩa trong schema" in reasons


def test_missing_schema_blocks_profit_forecast_without_profit_or_calendar_columns():
    context = _context(
        [
            ColumnInfo(name="timeline_hours", dtype="int64", nullable_count=0, sample_values=[2]),
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[12500.0]),
        ]
    )
    capabilities = infer_dataset_capabilities(context)

    reasons = missing_schema_reasons(normalize_text("Phân tích lợi nhuận theo quý và dự báo quý tiếp theo"), capabilities)

    assert "không có cột ngày/tháng để gom nhóm theo thời gian" in reasons
    assert "không có cột lợi nhuận đúng nghĩa trong schema" in reasons


def test_analysis_suggestions_are_generated_from_capabilities():
    context = _context(
        [
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[12500.0]),
            ColumnInfo(name="Dien_Tich_m2", dtype="float64", nullable_count=0, sample_values=[50.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Ha Noi"]),
        ]
    )

    suggestions = analysis_suggestions(context)

    assert suggestions[0] == "vẽ trung bình Gia_Trieu_VND theo Tinh_Thanh"
    assert "kiểm tra tương quan giữa Gia_Trieu_VND và Dien_Tich_m2" in suggestions
