from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.db import storage
from backend.app.main import app
from backend.app.services import dataset_service, execution_runner


@pytest.fixture()
def client(monkeypatch):
    runtime_dir = Path(__file__).resolve().parents[1] / ".test-runtime" / f"case_{uuid.uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(storage, "DB_PATH", runtime_dir / "ai_logs.db")
    monkeypatch.setattr(execution_runner, "RUNS_DIR", runtime_dir / "runs")
    monkeypatch.setattr(execution_runner, "ROOT", runtime_dir)

    storage.init_db()
    dataset_service.ensure_sample_data()
    try:
        yield TestClient(app)
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)


def create_proposal(client: TestClient) -> dict:
    response = client.post(
        "/api/ai/proposals",
        json={
            "session_id": "test_session",
            "dataset_id": "sales_2025",
            "user_request": "Ve doanh thu theo thang",
        },
    )
    assert response.status_code == 200
    return response.json()


def approve_proposal(client: TestClient, proposal_id: str) -> dict:
    response = client.post(
        f"/api/ai/proposals/{proposal_id}/approve",
        json={"approved_by": "tester", "approval_note": "pytest approval"},
    )
    assert response.status_code == 200
    return response.json()


def test_execution_requires_approval(client: TestClient):
    proposal = create_proposal(client)

    response = client.post(
        "/api/executions",
        json={
            "proposal_id": proposal["proposal_id"],
            "dataset_id": "sales_2025",
            "code_hash": "sha256:not-approved",
            "requested_by": "tester",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Proposal must be approved before execution"


def test_execution_rejects_code_hash_mismatch(client: TestClient):
    proposal = create_proposal(client)
    approve_proposal(client, proposal["proposal_id"])

    response = client.post(
        "/api/executions",
        json={
            "proposal_id": proposal["proposal_id"],
            "dataset_id": "sales_2025",
            "code_hash": "sha256:wrong",
            "requested_by": "tester",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Code hash mismatch"


def test_policy_rejects_unsafe_edited_code(client: TestClient):
    proposal = create_proposal(client)

    response = client.patch(
        f"/api/ai/proposals/{proposal['proposal_id']}",
        json={
            "edited_by": "tester",
            "edited_code": "import os\nos.system('dir')\ndf['new_column'] = 1",
        },
    )

    assert response.status_code == 400
    errors = response.json()["detail"]["policy_errors"]
    assert any("Import khong duoc phep: os" in error for error in errors)
    assert any("Khong duoc gan truc tiep vao df goc" in error for error in errors)
    assert any(".system()" in error for error in errors)


def test_approved_proposal_executes_locally_and_returns_artifact(client: TestClient):
    proposal = create_proposal(client)
    approval = approve_proposal(client, proposal["proposal_id"])

    response = client.post(
        "/api/executions",
        json={
            "proposal_id": proposal["proposal_id"],
            "dataset_id": "sales_2025",
            "code_hash": approval["code_hash"],
            "requested_by": "tester",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["artifacts"]
    assert body["artifacts"][0]["type"] == "chart"
