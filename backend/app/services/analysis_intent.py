from __future__ import annotations

from dataclasses import dataclass


Capabilities = dict[str, list[str]]


@dataclass(frozen=True)
class Requirement:
    capability: str
    min_count: int
    reason: str


@dataclass(frozen=True)
class IntentSpec:
    name: str
    tokens: tuple[str, ...]
    requirements: tuple[Requirement, ...] = ()


@dataclass(frozen=True)
class AnalysisPlan:
    intent_names: list[str]
    can_execute: bool
    missing_reasons: list[str]
    recommended_strategy: str


INTENT_SPECS: tuple[IntentSpec, ...] = (
    IntentSpec(
        name="time_series",
        tokens=(
            "theo thang",
            "theo ngay",
            "theo nam",
            "theo quy",
            "date",
            "month",
            "year",
            "quarter",
            "time series",
            "theo thoi gian",
            "qua thoi gian",
            "trend over time",
            "seasonality",
            "du bao",
            "forecast",
            "predict",
            "cohort",
            "dang ky",
        ),
        requirements=(
            Requirement("calendar", 1, "không có cột ngày/tháng để gom nhóm theo thời gian"),
        ),
    ),
    IntentSpec(
        name="revenue",
        tokens=("doanh thu", "revenue", "turnover", "sales amount", "sales"),
        requirements=(Requirement("revenue", 1, "không có cột doanh thu đúng nghĩa trong schema"),),
    ),
    IntentSpec(
        name="profit",
        tokens=("loi nhuan", "profit", "margin"),
        requirements=(Requirement("profit", 1, "không có cột lợi nhuận đúng nghĩa trong schema"),),
    ),
    IntentSpec(
        name="customer",
        tokens=("khach hang", "customer", "client", "lead", "retention"),
        requirements=(Requirement("customer", 1, "không có cột khách hàng/lead đúng nghĩa trong schema"),),
    ),
    IntentSpec(
        name="marketing_channel",
        tokens=("kenh quang cao", "channel", "campaign", "marketing", "ads", "utm"),
        requirements=(
            Requirement("marketing_channel", 1, "không có cột kênh quảng cáo/marketing đúng nghĩa trong schema"),
        ),
    ),
    IntentSpec(
        name="conversion_funnel",
        tokens=("chuyen doi", "conversion", "funnel", "ti le chuyen doi"),
        requirements=(
            Requirement("conversion", 1, "không có cột trạng thái/tỷ lệ chuyển đổi hoặc bước funnel trong schema"),
        ),
    ),
    IntentSpec(
        name="coordinate_map",
        tokens=("latitude", "longitude", "lat/lon", "toa do", "kinh do", "vi do", "ban do nhiet"),
        requirements=(Requirement("coordinate", 2, "không có đủ cột tọa độ latitude/longitude trong schema"),),
    ),
    IntentSpec(
        name="correlation",
        tokens=("tuong quan", "correlation", "scatter", "hoi quy", "regression", "relationship", "moi quan he"),
        requirements=(Requirement("numeric", 2, "cần ít nhất hai cột số để phân tích tương quan/hồi quy"),),
    ),
    IntentSpec(
        name="distribution",
        tokens=("phan bo", "histogram", "distribution", "outlier", "boxplot", "trung binh", "mean", "median", "tong", "sum"),
        requirements=(Requirement("numeric", 1, "cần ít nhất một cột số để phân tích phân bố hoặc thống kê"),),
    ),
    IntentSpec(
        name="group_comparison",
        tokens=("so sanh", "compare", "nhom", "group", "by category", "theo loai", "theo nhom", "theo tinh", "theo quan"),
        requirements=(Requirement("categorical", 1, "cần ít nhất một cột phân loại để so sánh theo nhóm"),),
    ),
    IntentSpec(
        name="geographic_category",
        tokens=("dia ly", "geographic", "geo", "tinh thanh", "quan huyen"),
        requirements=(Requirement("geo", 1, "cần cột địa lý như tỉnh/thành, quận/huyện hoặc khu vực"),),
    ),
)


def plan_analysis_request(request_text: str, capabilities: Capabilities) -> AnalysisPlan:
    intent_names: list[str] = []
    missing_reasons: list[str] = []

    for spec in INTENT_SPECS:
        if not _matches_any(request_text, spec.tokens):
            continue
        intent_names.append(spec.name)
        for requirement in spec.requirements:
            if _capability_count(capabilities, requirement.capability) < requirement.min_count:
                missing_reasons.append(requirement.reason)

    missing_reasons = _dedupe(missing_reasons)
    intent_names = intent_names or ["general_dataset_question"]
    return AnalysisPlan(
        intent_names=intent_names,
        can_execute=not missing_reasons,
        missing_reasons=missing_reasons,
        recommended_strategy=_recommended_strategy(intent_names, missing_reasons),
    )


def _matches_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _capability_count(capabilities: Capabilities, capability: str) -> int:
    return len(capabilities.get(capability, []))


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _recommended_strategy(intent_names: list[str], missing_reasons: list[str]) -> str:
    if missing_reasons:
        return "text_only_missing_schema"
    if "time_series" in intent_names:
        return "aggregate_by_calendar_column_then_chart"
    if "correlation" in intent_names:
        return "compute_numeric_relationships_then_chart"
    if "distribution" in intent_names:
        return "summarize_distribution_then_chart"
    if "group_comparison" in intent_names or "geographic_category" in intent_names:
        return "groupby_category_then_chart"
    return "general_schema_grounded_analysis"
