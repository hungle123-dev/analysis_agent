from __future__ import annotations

from backend.app.schemas import ColumnInfo, DatasetContext
from backend.app.services.analysis_intent import plan_analysis_request
from backend.app.services.dataset_capabilities import infer_dataset_capabilities, normalize_text


def _context(columns: list[ColumnInfo]) -> DatasetContext:
    return DatasetContext(id="dataset", name="dataset.csv", rows=100, status="ready", columns=columns)


def test_planner_blocks_business_prompt_when_required_business_capabilities_are_missing():
    context = _context(
        [
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[1200.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Hà Nội"]),
        ]
    )
    capabilities = infer_dataset_capabilities(context)

    plan = plan_analysis_request(
        normalize_text("Hãy phân tích tỷ lệ chuyển đổi khách hàng theo kênh quảng cáo và vẽ funnel conversion."),
        capabilities,
    )

    assert not plan.can_execute
    assert "không có cột khách hàng/lead đúng nghĩa trong schema" in plan.missing_reasons
    assert "không có cột kênh quảng cáo/marketing đúng nghĩa trong schema" in plan.missing_reasons
    assert "không có cột trạng thái/tỷ lệ chuyển đổi hoặc bước funnel trong schema" in plan.missing_reasons


def test_planner_blocks_coordinate_heatmap_without_latitude_longitude():
    context = _context(
        [
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[1200.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Hà Nội"]),
            ColumnInfo(name="Quan_Huyen", dtype="object", nullable_count=0, sample_values=["Cầu Giấy"]),
        ]
    )
    capabilities = infer_dataset_capabilities(context)

    plan = plan_analysis_request(
        normalize_text("Hãy vẽ bản đồ nhiệt theo tọa độ latitude/longitude để thể hiện giá bất động sản."),
        capabilities,
    )

    assert not plan.can_execute
    assert plan.missing_reasons == ["không có đủ cột tọa độ latitude/longitude trong schema"]


def test_planner_allows_feasible_correlation_prompt_with_numeric_columns():
    context = _context(
        [
            ColumnInfo(name="Dien_Tich_m2", dtype="float64", nullable_count=0, sample_values=[50.0]),
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[1200.0]),
        ]
    )
    capabilities = infer_dataset_capabilities(context)

    plan = plan_analysis_request(normalize_text("Kiểm tra tương quan giữa diện tích và giá."), capabilities)

    assert plan.can_execute
    assert "correlation" in plan.intent_names
    assert plan.missing_reasons == []


def test_planner_does_not_block_distribution_trend_language_without_time_intent():
    context = _context(
        [
            ColumnInfo(name="Gia_Trieu_VND", dtype="float64", nullable_count=0, sample_values=[1200.0]),
            ColumnInfo(name="Tinh_Thanh", dtype="object", nullable_count=0, sample_values=["Hà Nội"]),
        ]
    )
    capabilities = infer_dataset_capabilities(context)

    plan = plan_analysis_request(
        normalize_text("Vẽ biểu đồ giá trung bình theo Tinh_Thanh và nhận xét xu hướng phân bố giá."),
        capabilities,
    )

    assert plan.can_execute
    assert "group_comparison" in plan.intent_names
    assert "time_series" not in plan.intent_names
