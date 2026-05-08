from __future__ import annotations

import shutil
import uuid
import json
from pathlib import Path

from backend.app.services import dataset_service


def test_list_datasets_recovers_missing_sample_files(monkeypatch):
    runtime_dir = Path(__file__).resolve().parents[1] / ".test-runtime" / f"dataset_{uuid.uuid4().hex}"
    data_dir = runtime_dir / "data"
    config_path = runtime_dir / "backend" / "config" / "datasets.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            [
                {
                    "id": "sales_2025",
                    "name": "sales_2025.csv",
                    "path": str(data_dir / "sales_2025.csv"),
                    "description": "test dataset",
                    "allowed": True,
                    "created_by": "test",
                },
                {
                    "id": "customer_segments",
                    "name": "customer_segments.csv",
                    "path": str(data_dir / "customer_segments.csv"),
                    "description": "test dataset",
                    "allowed": True,
                    "created_by": "test",
                },
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(dataset_service, "DATA_DIR", data_dir)
    monkeypatch.setattr(dataset_service, "DATASET_CONFIG_PATH", config_path)

    try:
        summaries = dataset_service.list_datasets()

        assert len(summaries) == 2
        assert summaries[0].rows == 4
        assert (data_dir / "sales_2025.csv").exists()
        assert (data_dir / "customer_segments.csv").exists()
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)
