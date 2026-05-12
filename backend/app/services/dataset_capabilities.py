from __future__ import annotations

import re
import unicodedata

from backend.app.schemas import DatasetContext
from backend.app.services.analysis_intent import plan_analysis_request


def infer_dataset_capabilities(context: DatasetContext) -> dict[str, list[str]]:
    capabilities: dict[str, list[str]] = {
        "calendar": [],
        "numeric": [],
        "categorical": [],
        "revenue": [],
        "profit": [],
        "customer": [],
        "marketing_channel": [],
        "conversion": [],
        "coordinate": [],
        "value": [],
        "geo": [],
    }
    for column in context.columns:
        dtype = column.dtype.lower()
        name = normalize_text(column.name).replace("_", " ")
        compact_name = name.replace(" ", "")

        if "datetime" in dtype or _contains_any(
            name,
            {"date", "ngay", "thang", "month", "year", "nam", "timestamp", "created", "posted"},
        ):
            capabilities["calendar"].append(column.name)
        if _contains_any(dtype, {"int", "float", "double", "decimal"}) and "bool" not in dtype:
            capabilities["numeric"].append(column.name)
        if _contains_any(dtype, {"object", "string", "category", "bool"}):
            capabilities["categorical"].append(column.name)
        if _contains_any(name, {"doanh thu", "revenue", "turnover", "sales", "sale amount", "sales amount"}):
            capabilities["revenue"].append(column.name)
        if compact_name in {"doanhthu", "saleamount", "salesamount", "totalsales"}:
            capabilities["revenue"].append(column.name)
        if _contains_any(name, {"loi nhuan", "profit", "net income", "gross profit", "margin"}):
            capabilities["profit"].append(column.name)
        if _contains_any(name, {"khach hang", "customer", "client", "lead", "user", "buyer"}):
            capabilities["customer"].append(column.name)
        if _contains_any(name, {"kenh", "channel", "campaign", "marketing", "ads", "utm", "source", "medium"}):
            capabilities["marketing_channel"].append(column.name)
        if _contains_any(name, {"chuyen doi", "conversion", "funnel", "stage", "step", "click", "signup", "purchase"}):
            capabilities["conversion"].append(column.name)
        if _contains_any(name, {"latitude", "longitude", "lat", "lon", "lng", "toa do", "kinh do", "vi do"}):
            capabilities["coordinate"].append(column.name)
        if _contains_any(name, {"gia", "price", "amount", "value", "tri gia"}):
            capabilities["value"].append(column.name)
        if _contains_any(name, {"tinh", "thanh", "quan", "huyen", "province", "city", "district", "region"}):
            capabilities["geo"].append(column.name)

    return {key: _dedupe(values) for key, values in capabilities.items()}


def missing_schema_reasons(request_text: str, capabilities: dict[str, list[str]]) -> list[str]:
    return plan_analysis_request(request_text, capabilities).missing_reasons


def analysis_suggestions(context: DatasetContext) -> list[str]:
    capabilities = infer_dataset_capabilities(context)
    primary_numeric = capabilities["value"] or capabilities["numeric"]
    numeric = capabilities["numeric"]
    categorical = capabilities["geo"] or capabilities["categorical"]

    suggestions: list[str] = []
    if primary_numeric and categorical:
        suggestions.append(f"vẽ trung bình {primary_numeric[0]} theo {categorical[0]}")
    if primary_numeric:
        suggestions.append(f"vẽ phân bố {primary_numeric[0]}")
    if len(numeric) >= 2:
        suggestions.append(f"kiểm tra tương quan giữa {numeric[0]} và {numeric[1]}")
    if categorical:
        suggestions.append(f"đếm số dòng theo {categorical[0]}")
    return suggestions[:4]


def normalize_text(value: str) -> str:
    text = value.lower().replace("đ", "d")
    text = "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", text).strip()


def serialize_capabilities(capabilities: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        "calendar_columns": capabilities["calendar"],
        "numeric_columns": capabilities["numeric"],
        "categorical_columns": capabilities["categorical"],
        "revenue_columns": capabilities["revenue"],
        "profit_columns": capabilities["profit"],
        "customer_columns": capabilities["customer"],
        "marketing_channel_columns": capabilities["marketing_channel"],
        "conversion_columns": capabilities["conversion"],
        "coordinate_columns": capabilities["coordinate"],
        "value_columns": capabilities["value"],
        "geo_columns": capabilities["geo"],
    }


def _contains_any(text: str, tokens: set[str]) -> bool:
    return any(token in text for token in tokens)


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
