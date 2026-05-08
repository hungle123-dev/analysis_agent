from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from backend.app.services import dataset_service


def test_list_datasets_recovers_missing_sample_files(monkeypatch):
    runtime_dir = Path(__file__).resolve().parents[1] / ".test-runtime" / f"dataset_{uuid.uuid4().hex}"
    data_dir = runtime_dir / "data"
    monkeypatch.setattr(dataset_service, "DATA_DIR", data_dir)
    monkeypatch.setattr(
        dataset_service,
        "DATASETS",
        {
            "sales_2025": {"name": "sales_2025.csv", "path": str(data_dir / "sales_2025.csv")},
            "customer_segments": {
                "name": "customer_segments.csv",
                "path": str(data_dir / "customer_segments.csv"),
            },
        },
    )

    try:
        summaries = dataset_service.list_datasets()

        assert len(summaries) == 2
        assert summaries[0].rows == 4
        assert (data_dir / "sales_2025.csv").exists()
        assert (data_dir / "customer_segments.csv").exists()
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)
