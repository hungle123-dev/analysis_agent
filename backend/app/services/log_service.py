from __future__ import annotations

import json

from backend.app.db.storage import connect
from backend.app.schemas import LogTraceResponse


def get_trace_logs(trace_id: str) -> LogTraceResponse:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_events WHERE trace_id = ? ORDER BY timestamp ASC",
            (trace_id,),
        ).fetchall()
    return LogTraceResponse(
        trace_id=trace_id,
        events=[
            {
                "id": row["event_id"],
                "type": row["event_type"],
                "actor": row["actor"],
                "time": row["timestamp"],
                "detail": json.loads(row["payload_json"]),
            }
            for row in rows
        ],
    )
