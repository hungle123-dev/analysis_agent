from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime

from fastapi import HTTPException

from backend.app.core.paths import ROOT, RUNS_DIR
from backend.app.db.storage import append_event, connect, now_iso
from backend.app.schemas import ExecutionRequest, ExecutionResponse
from backend.app.services.dataset_service import get_dataset_path
from backend.app.services.policy_checker import validate_code


def execute_proposal(payload: ExecutionRequest) -> ExecutionResponse:
    try:
        get_dataset_path(payload.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    proposal = _claim_approved_proposal(payload)
    code = proposal["edited_code"] or proposal["ai_code"]
    policy_errors = validate_code(code)
    if policy_errors:
        append_event(proposal["trace_id"], "execution.policy_rejected", "system", {"errors": policy_errors})
        _set_proposal_status(payload.proposal_id, "failed")
        raise HTTPException(status_code=400, detail={"policy_errors": policy_errors})

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    append_event(proposal["trace_id"], "execution.started", payload.requested_by, {"run_id": run_id})
    try:
        result = run_code(run_id, payload.dataset_id, code)
    except Exception as exc:
        result = _failed_run_result(str(exc))
    append_event(proposal["trace_id"], f"execution.{result['status']}", "system", {"run_id": run_id})

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO executions(
              run_id, proposal_id, status, stdout, stderr, artifacts_json,
              started_at, finished_at, duration_ms, return_code
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                payload.proposal_id,
                result["status"],
                result["stdout"],
                result["stderr"],
                result["artifacts_json"],
                result["started_at"],
                result["finished_at"],
                result["duration_ms"],
                result["return_code"],
            ),
        )
        conn.execute(
            "UPDATE proposals SET status = ?, updated_at = ? WHERE proposal_id = ?",
            ("succeeded" if result["status"] == "succeeded" else "failed", now_iso(), payload.proposal_id),
        )

    return ExecutionResponse(
        run_id=run_id,
        proposal_id=payload.proposal_id,
        status=result["status"],
        stdout=result["stdout"],
        stderr=result["stderr"],
        artifacts=result["artifacts"],
        return_code=result["return_code"],
        duration_ms=result["duration_ms"],
        started_at=result["started_at"],
        finished_at=result["finished_at"],
    )


def _claim_approved_proposal(payload: ExecutionRequest) -> dict:
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM proposals WHERE proposal_id = ?", (payload.proposal_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Proposal not found")
        if row["status"] != "approved":
            raise HTTPException(status_code=409, detail="Proposal must be approved before execution")
        if row["dataset_id"] != payload.dataset_id:
            raise HTTPException(status_code=400, detail="Dataset mismatch")
        if row["code_hash"] != payload.code_hash:
            raise HTTPException(status_code=409, detail="Code hash mismatch")

        updated = conn.execute(
            "UPDATE proposals SET status = 'running', updated_at = ? WHERE proposal_id = ? AND status = 'approved'",
            (now_iso(), payload.proposal_id),
        )
        if updated.rowcount != 1:
            raise HTTPException(status_code=409, detail="Proposal is already running or no longer approved")
        return dict(row)


def _set_proposal_status(proposal_id: str, status: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE proposals SET status = ?, updated_at = ? WHERE proposal_id = ?",
            (status, now_iso(), proposal_id),
        )


def run_code(run_id: str, dataset_id: str, code: str) -> dict:
    try:
        timeout_seconds = max(1, int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "30")))
    except ValueError:
        timeout_seconds = 30
    started_at = now_iso()
    started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    run_dir = RUNS_DIR / run_id
    outputs_dir = run_dir / "outputs"
    run_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    code_path = run_dir / "proposal_code.py"
    runner_path = run_dir / "runner.py"
    code_path.write_text(code, encoding="utf-8")
    runner_path.write_text(
        f"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv({str(get_dataset_path(dataset_id))!r})
outputs_dir = Path({str(outputs_dir)!r})
user_code = Path({str(code_path)!r}).read_text(encoding="utf-8")
exec(compile(user_code, {str(code_path)!r}, "exec"), {{"df": df, "pd": pd, "plt": plt, "outputs_dir": outputs_dir}})
""",
        encoding="utf-8",
    )
    try:
        completed = subprocess.run(
            [sys.executable, str(runner_path)],
            cwd=run_dir,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
        status = "succeeded" if completed.returncode == 0 else "failed"
        stdout = _limit_output(completed.stdout)
        stderr = _limit_output(completed.stderr)
        return_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        status = "failed"
        stdout = _limit_output(exc.stdout or "")
        stderr = _limit_output((exc.stderr or "") + f"\nExecution timed out after {timeout_seconds} seconds.")
        return_code = -1

    artifacts = [
        {
            "type": _infer_artifact_type(path),
            "name": path.name,
            "path": path.relative_to(ROOT).as_posix(),
        }
        for path in sorted(outputs_dir.glob("*"))
        if path.is_file()
    ]
    finished_at = now_iso()
    finished_dt = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    return {
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "artifacts": artifacts,
        "artifacts_json": json.dumps(artifacts),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": int((finished_dt - started_dt).total_seconds() * 1000),
        "return_code": return_code,
    }


def _failed_run_result(message: str) -> dict:
    finished_at = now_iso()
    return {
        "status": "failed",
        "stdout": "",
        "stderr": _limit_output(message),
        "artifacts": [],
        "artifacts_json": "[]",
        "started_at": finished_at,
        "finished_at": finished_at,
        "duration_ms": 0,
        "return_code": -1,
    }


def _limit_output(value: str) -> str:
    try:
        max_chars = max(1_000, int(os.getenv("EXECUTION_MAX_OUTPUT_CHARS", "20000")))
    except ValueError:
        max_chars = 20_000
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + f"\n...[truncated to {max_chars} characters]"


def _infer_artifact_type(path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".webp"}:
        return "chart"
    if suffix in {".csv", ".json", ".parquet", ".xlsx"}:
        return "table"
    if suffix in {".txt", ".log"}:
        return "log"
    return "text"
