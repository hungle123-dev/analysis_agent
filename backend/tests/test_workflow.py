from __future__ import annotations

import shutil
import time
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

    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_EXPLAIN_RESULT_PROVIDER", "mock")
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


def test_proposal_job_creates_proposal_in_background(client: TestClient):
    response = client.post(
        "/api/ai/proposals/jobs",
        json={
            "session_id": "test_session",
            "dataset_id": "sales_2025",
            "user_request": "Ve doanh thu theo thang",
        },
    )
    assert response.status_code == 200
    job = response.json()
    assert job["status"] in {"queued", "running", "succeeded"}

    final_job = job
    for _ in range(20):
        poll = client.get(f"/api/ai/proposals/jobs/{job['job_id']}")
        assert poll.status_code == 200
        final_job = poll.json()
        if final_job["status"] == "succeeded":
            break
        time.sleep(0.05)

    assert final_job["status"] == "succeeded"
    assert final_job["proposal_id"]
    proposal = client.get(f"/api/ai/proposals/{final_job['proposal_id']}")
    assert proposal.status_code == 200
    assert proposal.json()["status"] == "pending_review"


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


def test_rejected_proposal_is_logged_and_cannot_execute(client: TestClient):
    proposal = create_proposal(client)

    rejected = client.post(
        f"/api/ai/proposals/{proposal['proposal_id']}/reject",
        json={"rejected_by": "tester", "rejection_reason": "needs different chart"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    logs = client.get(f"/api/logs/{proposal['trace_id']}")
    assert logs.status_code == 200
    assert any(event["type"] == "ai.approval.rejected" for event in logs.json()["events"])

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
    assert any("Import khong duoc phep: os" in error["message"] for error in errors)
    assert any("Khong duoc gan truc tiep vao df goc" in error["message"] for error in errors)
    assert any(".system()" in error["message"] for error in errors)


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
    assert body["ai_insight_status"] == "succeeded"
    assert body["ai_insight"]
    assert isinstance(body["duration_ms"], int)
    assert isinstance(body["return_code"], int)
    assert "started_at" in body
    assert "finished_at" in body


def test_completed_proposal_cannot_run_twice(client: TestClient):
    proposal = create_proposal(client)
    approval = approve_proposal(client, proposal["proposal_id"])

    first = client.post(
        "/api/executions",
        json={
            "proposal_id": proposal["proposal_id"],
            "dataset_id": "sales_2025",
            "code_hash": approval["code_hash"],
            "requested_by": "tester",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/api/executions",
        json={
            "proposal_id": proposal["proposal_id"],
            "dataset_id": "sales_2025",
            "code_hash": approval["code_hash"],
            "requested_by": "tester",
        },
    )
    assert second.status_code == 409


def test_execution_returns_table_artifacts(client: TestClient):
    proposal = create_proposal(client)
    edited_code = """
import matplotlib.pyplot as plt
work_df = df.copy()
summary = work_df.groupby("region", as_index=False)["revenue"].sum()
summary.to_csv(outputs_dir / "summary.csv", index=False)
plt.figure(figsize=(6, 4))
plt.bar(summary["region"], summary["revenue"])
plt.tight_layout()
plt.savefig(outputs_dir / "summary.png")
print(summary.to_string(index=False))
"""
    update_response = client.patch(
        f"/api/ai/proposals/{proposal['proposal_id']}",
        json={"edited_by": "tester", "edited_code": edited_code},
    )
    assert update_response.status_code == 200
    approval = approve_proposal(client, proposal["proposal_id"])

    execution = client.post(
        "/api/executions",
        json={
            "proposal_id": proposal["proposal_id"],
            "dataset_id": "sales_2025",
            "code_hash": approval["code_hash"],
            "requested_by": "tester",
        },
    )
    assert execution.status_code == 200
    assert execution.json()["ai_insight_status"] == "succeeded"
    artifacts = execution.json()["artifacts"]
    assert any(item["type"] == "table" and item["name"] == "summary.csv" for item in artifacts)
    assert any(item["type"] == "chart" and item["name"] == "summary.png" for item in artifacts)


def test_execution_fails_when_proposal_promises_chart_but_code_creates_no_chart(client: TestClient):
    proposal = create_proposal(client)
    edited_code = """
work_df = df.copy()
summary = work_df.groupby("region", as_index=False)["revenue"].sum()
print(summary.to_string(index=False))
"""
    update_response = client.patch(
        f"/api/ai/proposals/{proposal['proposal_id']}",
        json={"edited_by": "tester", "edited_code": edited_code},
    )
    assert update_response.status_code == 200
    approval = approve_proposal(client, proposal["proposal_id"])

    execution = client.post(
        "/api/executions",
        json={
            "proposal_id": proposal["proposal_id"],
            "dataset_id": "sales_2025",
            "code_hash": approval["code_hash"],
            "requested_by": "tester",
        },
    )

    assert execution.status_code == 200
    body = execution.json()
    assert body["status"] == "failed"
    assert body["return_code"] == 0
    assert "did not create expected artifact(s): chart" in body["stderr"]


def test_execution_fails_when_declared_chart_is_not_created(client: TestClient):
    proposal = create_proposal(client)
    edited_code = """
import matplotlib.pyplot as plt
work_df = df.copy()
if "missing_date" not in work_df.columns:
    print("LỖI: Không tìm thấy cột ngày tháng.")
else:
    plt.figure()
    plt.plot([1, 2, 3], [1, 4, 9])
    plt.savefig(outputs_dir / "chart.png")
"""
    update_response = client.patch(
        f"/api/ai/proposals/{proposal['proposal_id']}",
        json={"edited_by": "tester", "edited_code": edited_code},
    )
    assert update_response.status_code == 200
    approval = approve_proposal(client, proposal["proposal_id"])

    execution = client.post(
        "/api/executions",
        json={
            "proposal_id": proposal["proposal_id"],
            "dataset_id": "sales_2025",
            "code_hash": approval["code_hash"],
            "requested_by": "tester",
        },
    )

    assert execution.status_code == 200
    body = execution.json()
    assert body["status"] == "failed"
    assert body["return_code"] == 0
    assert body["ai_insight_status"] == "not_requested"
    assert "did not create expected artifact(s): chart" in body["stderr"]


def test_execution_still_succeeds_when_ai_insight_fails(client: TestClient, monkeypatch):
    proposal = create_proposal(client)
    approval = approve_proposal(client, proposal["proposal_id"])

    def fail_insight(**kwargs):
        raise RuntimeError("insight provider unavailable")

    monkeypatch.setattr(execution_runner, "explain_execution_result", fail_insight)
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
    assert body["ai_insight_status"] == "failed"
    assert "insight provider unavailable" in body["ai_insight_error"]
