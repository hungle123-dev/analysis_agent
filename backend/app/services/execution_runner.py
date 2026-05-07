from __future__ import annotations

import subprocess
import sys
import uuid

from fastapi import HTTPException

from backend.app.core.paths import ROOT, RUNS_DIR
from backend.app.db.storage import append_event, connect, now_iso
from backend.app.schemas import ExecutionRequest, ExecutionResponse
from backend.app.services.dataset_service import get_dataset_path
from backend.app.services.policy_checker import validate_code
from backend.app.services.proposal_service import get_proposal_row


def execute_proposal(payload: ExecutionRequest) -> ExecutionResponse:
    proposal = get_proposal_row(payload.proposal_id)
    if proposal["status"] != "approved":
        raise HTTPException(status_code=409, detail="Proposal must be approved before execution")
    if proposal["dataset_id"] != payload.dataset_id:
        raise HTTPException(status_code=400, detail="Dataset mismatch")
    if proposal["code_hash"] != payload.code_hash:
        raise HTTPException(status_code=409, detail="Code hash mismatch")

    code = proposal["edited_code"] or proposal["ai_code"]
    errors = validate_code(code)
    if errors:
        append_event(proposal["trace_id"], "execution.policy_rejected", "system", {"errors": errors})
        raise HTTPException(status_code=400, detail={"policy_errors": errors})

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    append_event(proposal["trace_id"], "execution.started", payload.requested_by, {"run_id": run_id})
    result = run_code(run_id, payload.dataset_id, code)
    append_event(proposal["trace_id"], f"execution.{result['status']}", "system", {"run_id": run_id})

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO executions(run_id, proposal_id, status, stdout, stderr, artifacts_json, started_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    )


def run_code(run_id: str, dataset_id: str, code: str) -> dict:
    import json

    started_at = now_iso()
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
            timeout=30,
        )
        status = "succeeded" if completed.returncode == 0 else "failed"
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        status = "failed"
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + "\nExecution timed out after 30 seconds."

    artifacts = [
        {"type": "chart", "name": path.name, "path": path.relative_to(ROOT).as_posix()}
        for path in outputs_dir.glob("*")
        if path.is_file()
    ]
    return {
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "artifacts": artifacts,
        "artifacts_json": json.dumps(artifacts),
        "started_at": started_at,
        "finished_at": now_iso(),
    }
