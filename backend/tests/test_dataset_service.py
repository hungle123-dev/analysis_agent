from __future__ import annotations

import json
import shutil
import uuid
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


def test_dataset_row_count_cache_invalidates_when_file_changes(monkeypatch):
    runtime_dir = Path(__file__).resolve().parents[1] / ".test-runtime" / f"dataset_{uuid.uuid4().hex}"
    data_dir = runtime_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    config_path = runtime_dir / "backend" / "config" / "datasets.json"
    dataset_path = data_dir / "rows.csv"
    dataset_path.write_text("name,value\na,1\n", encoding="utf-8")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            [
                {
                    "id": "rows",
                    "name": "rows.csv",
                    "path": str(dataset_path),
                    "allowed": True,
                    "created_by": "test",
                }
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(dataset_service, "DATA_DIR", data_dir)
    monkeypatch.setattr(dataset_service, "DATASET_CONFIG_PATH", config_path)
    dataset_service.clear_dataset_caches()

    try:
        first = dataset_service.list_datasets()
        dataset_path.write_text("name,value\na,1\nb,2\n", encoding="utf-8")
        second = dataset_service.list_datasets()

        assert first[0].rows == 1
        assert second[0].rows == 2
    finally:
        dataset_service.clear_dataset_caches()
        shutil.rmtree(runtime_dir, ignore_errors=True)
