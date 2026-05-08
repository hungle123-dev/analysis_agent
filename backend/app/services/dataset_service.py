from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.app.core.paths import DATA_DIR
from backend.app.schemas import ColumnInfo, DatasetContext, DatasetSummary

DATASETS: dict[str, dict[str, str]] = {
    "sales_2025": {"name": "sales_2025.csv", "path": str(DATA_DIR / "sales_2025.csv")},
    "customer_segments": {
        "name": "customer_segments.csv",
        "path": str(DATA_DIR / "customer_segments.csv"),
    },
}


def ensure_sample_data() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    sales_path = Path(DATASETS["sales_2025"]["path"])
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

    segments_path = Path(DATASETS["customer_segments"]["path"])
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
    if dataset_id not in DATASETS:
        raise KeyError(dataset_id)
    dataset_path = Path(DATASETS[dataset_id]["path"])
    if not dataset_path.exists():
        ensure_sample_data()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Registered dataset file is missing: {dataset_path}")
    return pd.read_csv(dataset_path)


def list_datasets() -> list[DatasetSummary]:
    return [
        DatasetSummary(
            id=dataset_id,
            name=meta["name"],
            rows=len(read_dataset(dataset_id)),
            status="ready",
        )
        for dataset_id, meta in DATASETS.items()
    ]


def get_dataset_context(dataset_id: str) -> DatasetContext:
    df = read_dataset(dataset_id)
    columns = [
        ColumnInfo(
            name=name,
            dtype=str(df[name].dtype),
            nullable_count=int(df[name].isna().sum()),
            sample_values=df[name].dropna().head(3).tolist(),
        )
        for name in df.columns
    ]
    return DatasetContext(
        id=dataset_id,
        name=DATASETS[dataset_id]["name"],
        rows=len(df),
        status="ready",
        columns=columns,
    )


def get_dataset_path(dataset_id: str) -> Path:
    if dataset_id not in DATASETS:
        raise KeyError(dataset_id)
    return Path(DATASETS[dataset_id]["path"])
