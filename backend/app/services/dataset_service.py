from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.paths import DATA_DIR, ROOT
from backend.app.schemas import ColumnInfo, DatasetContext, DatasetSummary

DATASET_CONFIG_PATH = ROOT / "backend" / "config" / "datasets.json"
CSV_CHUNK_SIZE = 50_000
NUMERIC_PROFILE_MAX_VALUES = 100_000
_REGISTRY_CACHE: dict[str, dict[str, Any]] | None = None
_REGISTRY_CACHE_MTIME_NS: int | None = None
_REGISTRY_CACHE_PATH: Path | None = None
_ROW_COUNT_CACHE: dict[Path, tuple[tuple[int, int], int]] = {}
_PROFILE_CACHE: dict[Path, tuple[tuple[int, int], dict[str, Any]]] = {}

DEFAULT_DATASET_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "sales_2025",
        "name": "sales_2025.csv",
        "path": "data/sales_2025.csv",
        "description": "Demo sales dataset for workflow validation.",
        "allowed": True,
        "created_by": "system",
    },
    {
        "id": "customer_segments",
        "name": "customer_segments.csv",
        "path": "data/customer_segments.csv",
        "description": "Demo customer segmentation dataset.",
        "allowed": True,
        "created_by": "system",
    },
    {
        "id": "vietnam_real_estate_cleaned",
        "name": "cleaned_vietnam_real_estate.csv",
        "path": "cleaned_vietnam_real_estate.csv",
        "description": "Processed Vietnam real estate listings for analysis.",
        "allowed": True,
        "created_by": "student",
    },
]


def _ensure_dataset_registry_file() -> None:
    DATASET_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATASET_CONFIG_PATH.exists():
        DATASET_CONFIG_PATH.write_text(
            json.dumps(DEFAULT_DATASET_REGISTRY, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _load_registry() -> dict[str, dict[str, Any]]:
    global _REGISTRY_CACHE, _REGISTRY_CACHE_MTIME_NS, _REGISTRY_CACHE_PATH

    _ensure_dataset_registry_file()
    config_path = DATASET_CONFIG_PATH.resolve()
    config_mtime_ns = DATASET_CONFIG_PATH.stat().st_mtime_ns
    if (
        _REGISTRY_CACHE is not None
        and _REGISTRY_CACHE_MTIME_NS == config_mtime_ns
        and _REGISTRY_CACHE_PATH == config_path
    ):
        return _REGISTRY_CACHE

    try:
        raw = json.loads(DATASET_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid dataset config JSON at {DATASET_CONFIG_PATH}") from exc

    if not isinstance(raw, list):
        raise RuntimeError("Dataset registry must be a list of dataset objects.")

    registry: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        dataset_id = str(item.get("id", "")).strip()
        if not dataset_id:
            continue
        if not bool(item.get("allowed", False)):
            continue

        raw_path = str(item.get("path", "")).strip()
        if not raw_path:
            continue

        dataset_path = Path(raw_path)
        if not dataset_path.is_absolute():
            dataset_path = ROOT / dataset_path

        registry[dataset_id] = {
            "id": dataset_id,
            "name": str(item.get("name", dataset_path.name)),
            "path": dataset_path,
            "description": str(item.get("description", "")),
            "allowed": True,
            "visible": bool(item.get("visible", True)),
            "created_by": str(item.get("created_by", "unknown")),
        }
    _REGISTRY_CACHE = registry
    _REGISTRY_CACHE_MTIME_NS = config_mtime_ns
    _REGISTRY_CACHE_PATH = config_path
    return registry


def _get_registry() -> dict[str, dict[str, Any]]:
    registry = _load_registry()
    if not registry:
        raise RuntimeError("No allowed datasets configured in backend/config/datasets.json")
    return registry


def ensure_sample_data() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    registry = _get_registry()
    sales_meta = registry.get("sales_2025")
    segments_meta = registry.get("customer_segments")
    if not sales_meta or not segments_meta:
        return

    sales_path = Path(sales_meta["path"])
    if not sales_path.exists():
        pd.DataFrame(
            [
                ["2025-01-05", "North", "Notebook", 1240000, 12],
                ["2025-02-14", "South", "Monitor", 1580000, 9],
                ["2025-03-21", "Central", "Keyboard", 1430000, 18],
                ["2025-04-07", "North", "Mouse", 1890000, 24],
            ],
            columns=["date", "region", "product", "revenue", "quantity"],
        ).to_csv(sales_path, index=False)

    segments_path = Path(segments_meta["path"])
    if not segments_path.exists():
        pd.DataFrame(
            [
                ["C001", 22, "Hanoi", 71.5],
                ["C002", 31, "Danang", 64.2],
                ["C003", 28, "HCMC", 83.9],
                ["C004", 45, "Can Tho", 58.4],
            ],
            columns=["customer_id", "age", "city", "spend_score"],
        ).to_csv(segments_path, index=False)


def read_dataset(dataset_id: str) -> pd.DataFrame:
    registry = _get_registry()
    if dataset_id not in registry:
        raise KeyError(dataset_id)
    dataset_path = Path(registry[dataset_id]["path"])
    if not dataset_path.exists():
        ensure_sample_data()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Registered dataset file is missing: {dataset_path}")
    return pd.read_csv(dataset_path, memory_map=True)


def list_datasets() -> list[DatasetSummary]:
    summaries: list[DatasetSummary] = []
    for dataset_id, meta in _get_registry().items():
        if not meta.get("visible", True):
            continue
        dataset_path = Path(meta["path"])
        if not dataset_path.exists():
            ensure_sample_data()
        if not dataset_path.exists():
            summaries.append(
                DatasetSummary(
                    id=dataset_id,
                    name=meta["name"],
                    rows=0,
                    status="missing",
                )
            )
            continue
        row_count = _cached_count_csv_rows(dataset_path)
        summaries.append(DatasetSummary(id=dataset_id, name=meta["name"], rows=row_count, status="ready"))
    return summaries


def get_dataset_context(dataset_id: str) -> DatasetContext:
    registry = _get_registry()
    if dataset_id not in registry:
        raise KeyError(dataset_id)
    dataset_path = get_dataset_path(dataset_id)
    profile = _cached_profile_csv(dataset_path)
    columns = [
        ColumnInfo(
            name=name,
            dtype=profile["dtypes"].get(name, "object"),
            nullable_count=profile["null_counts"].get(name, 0),
            sample_values=profile["sample_values"].get(name, []),
            unique_count=profile["unique_counts"].get(name),
            top_values=profile["top_values"].get(name, []),
            numeric_summary=profile["numeric_summary"].get(name, {}),
        )
        for name in profile["columns"]
    ]
    return DatasetContext(
        id=dataset_id,
        name=registry[dataset_id]["name"],
        rows=profile["rows"],
        status="ready",
        columns=columns,
    )


def get_dataset_path(dataset_id: str) -> Path:
    registry = _get_registry()
    if dataset_id not in registry:
        raise KeyError(dataset_id)
    dataset_path = Path(registry[dataset_id]["path"])
    if not dataset_path.exists():
        ensure_sample_data()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Registered dataset file is missing: {dataset_path}")
    return dataset_path


def _count_csv_rows(dataset_path: Path) -> int:
    header = pd.read_csv(dataset_path, nrows=0)
    if header.columns.empty:
        return 0

    first_column = header.columns[0]
    row_count = 0
    for chunk in pd.read_csv(dataset_path, usecols=[first_column], chunksize=CSV_CHUNK_SIZE):
        row_count += len(chunk)
    return row_count


def _cached_count_csv_rows(dataset_path: Path) -> int:
    cache_key = dataset_path.resolve()
    fingerprint = _csv_fingerprint(cache_key)
    cached = _ROW_COUNT_CACHE.get(cache_key)
    if cached and cached[0] == fingerprint:
        return cached[1]

    row_count = _count_csv_rows(cache_key)
    _ROW_COUNT_CACHE[cache_key] = (fingerprint, row_count)
    return row_count


def _cached_profile_csv(dataset_path: Path) -> dict[str, Any]:
    cache_key = dataset_path.resolve()
    fingerprint = _csv_fingerprint(cache_key)
    cached = _PROFILE_CACHE.get(cache_key)
    if cached and cached[0] == fingerprint:
        return cached[1]

    profile = _profile_csv(cache_key)
    _PROFILE_CACHE[cache_key] = (fingerprint, profile)
    _ROW_COUNT_CACHE[cache_key] = (fingerprint, int(profile["rows"]))
    return profile


def _csv_fingerprint(dataset_path: Path) -> tuple[int, int]:
    stat = dataset_path.stat()
    return stat.st_mtime_ns, stat.st_size


def clear_dataset_caches() -> None:
    _ROW_COUNT_CACHE.clear()
    _PROFILE_CACHE.clear()


def _profile_csv(dataset_path: Path) -> dict[str, Any]:
    header = pd.read_csv(dataset_path, nrows=0)
    columns = list(header.columns)
    dtypes = {column: str(dtype) for column, dtype in header.dtypes.items()}
    null_counts = {column: 0 for column in columns}
    sample_values: dict[str, list[Any]] = {column: [] for column in columns}
    unique_values: dict[str, set[Any]] = {column: set() for column in columns}
    top_value_counts: dict[str, dict[str, int]] = {column: {} for column in columns}
    numeric_series_values: dict[str, list[float]] = {column: [] for column in columns}
    row_count = 0

    for chunk in pd.read_csv(dataset_path, chunksize=CSV_CHUNK_SIZE):
        row_count += len(chunk)
        dtypes.update({column: str(dtype) for column, dtype in chunk.dtypes.items()})
        chunk_nulls = chunk.isna().sum()
        for column in columns:
            null_counts[column] += int(chunk_nulls.get(column, 0))
            remaining = 3 - len(sample_values[column])
            if remaining > 0:
                sample_values[column].extend(chunk[column].dropna().head(remaining).tolist())
            non_null = chunk[column].dropna()
            if len(unique_values[column]) <= 1000:
                unique_values[column].update(non_null.drop_duplicates().head(1001).tolist())
            if _is_categorical_dtype(str(chunk[column].dtype)):
                for value, count in non_null.astype(str).value_counts().head(20).items():
                    top_value_counts[column][value] = top_value_counts[column].get(value, 0) + int(count)
            if _is_numeric_dtype(str(chunk[column].dtype)):
                numeric_values = pd.to_numeric(non_null, errors="coerce").dropna()
                if not numeric_values.empty:
                    remaining = NUMERIC_PROFILE_MAX_VALUES - len(numeric_series_values[column])
                    if remaining > 0:
                        numeric_series_values[column].extend(numeric_values.head(remaining).tolist())

    return {
        "columns": columns,
        "dtypes": dtypes,
        "null_counts": null_counts,
        "sample_values": sample_values,
        "unique_counts": {
            column: (len(values) if len(values) <= 1000 else 1001)
            for column, values in unique_values.items()
        },
        "top_values": {
            column: [
                {"value": value, "count": count}
                for value, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]
            ]
            for column, counts in top_value_counts.items()
        },
        "numeric_summary": {
            column: _numeric_summary(values)
            for column, values in numeric_series_values.items()
            if values
        },
        "rows": row_count,
    }


def _is_numeric_dtype(dtype: str) -> bool:
    value = dtype.lower()
    return any(token in value for token in ("int", "float", "double", "decimal")) and "bool" not in value


def _is_categorical_dtype(dtype: str) -> bool:
    value = dtype.lower()
    return any(token in value for token in ("object", "string", "category", "bool"))


def _numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    series = pd.Series(values)
    return {
        "count": int(series.count()),
        "mean": _round_or_none(series.mean()),
        "std": _round_or_none(series.std()),
        "min": _round_or_none(series.min()),
        "p25": _round_or_none(series.quantile(0.25)),
        "median": _round_or_none(series.median()),
        "p75": _round_or_none(series.quantile(0.75)),
        "max": _round_or_none(series.max()),
    }


def _round_or_none(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 4)
