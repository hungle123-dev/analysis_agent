from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.core.paths import DB_PATH


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS proposals (
              proposal_id TEXT PRIMARY KEY,
              trace_id TEXT NOT NULL,
              session_id TEXT NOT NULL,
              dataset_id TEXT NOT NULL,
              user_request TEXT NOT NULL,
              ai_code TEXT NOT NULL,
              edited_code TEXT,
              explanation TEXT NOT NULL,
              summary TEXT NOT NULL,
              assumptions_json TEXT NOT NULL,
              risk_flags_json TEXT NOT NULL,
              expected_outputs_json TEXT NOT NULL,
              status TEXT NOT NULL,
              code_hash TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approvals (
              approval_id TEXT PRIMARY KEY,
              proposal_id TEXT NOT NULL,
              approved_by TEXT NOT NULL,
              approved_at TEXT NOT NULL,
              approval_note TEXT NOT NULL,
              code_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS executions (
              run_id TEXT PRIMARY KEY,
              proposal_id TEXT NOT NULL,
              status TEXT NOT NULL,
              stdout TEXT NOT NULL,
              stderr TEXT NOT NULL,
              artifacts_json TEXT NOT NULL,
              started_at TEXT NOT NULL,
              finished_at TEXT NOT NULL,
              duration_ms INTEGER DEFAULT 0,
              return_code INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS audit_events (
              event_id TEXT PRIMARY KEY,
              trace_id TEXT NOT NULL,
              event_type TEXT NOT NULL,
              actor TEXT NOT NULL,
              timestamp TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            """
        )
        _ensure_execution_columns(conn)


def _ensure_execution_columns(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(executions)").fetchall()}
    if "duration_ms" not in columns:
        conn.execute("ALTER TABLE executions ADD COLUMN duration_ms INTEGER DEFAULT 0")
    if "return_code" not in columns:
        conn.execute("ALTER TABLE executions ADD COLUMN return_code INTEGER DEFAULT 0")


def append_event(trace_id: str, event_type: str, actor: str, payload: dict[str, Any]) -> None:
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO audit_events(event_id, trace_id, event_type, actor, timestamp, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, trace_id, event_type, actor, now_iso(), json.dumps(payload)),
        )


def row_to_proposal(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "proposal_id": row["proposal_id"],
        "trace_id": row["trace_id"],
        "dataset_id": row["dataset_id"],
        "status": row["status"],
        "summary": row["summary"],
        "code": row["edited_code"] or row["ai_code"],
        "explanation": row["explanation"],
        "assumptions": json.loads(row["assumptions_json"]),
        "risk_flags": json.loads(row["risk_flags_json"]),
        "expected_outputs": json.loads(row["expected_outputs_json"]),
        "code_hash": row["code_hash"],
    }
