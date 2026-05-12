from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

from backend.app.core.env import load_local_env
from backend.app.services.llm_provider import ExecutionInsightInput, get_execution_insight_provider


def explain_execution_result(
    *,
    root: Path,
    user_request: str,
    code: str,
    stdout: str,
    stderr: str,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    load_local_env()
    if not _is_enabled():
        return _not_requested("AI_EXPLAIN_RESULT_ENABLED=false")

    table_previews = _collect_table_previews(root, artifacts)
    if not _has_real_execution_output(stdout=stdout, stderr=stderr, artifacts=artifacts, table_previews=table_previews):
        return _not_requested("Không có stdout, stderr, artifact hoặc bảng kết quả thật để AI phân tích.")

    provider = get_execution_insight_provider()
    draft = provider.explain_execution_result(
        ExecutionInsightInput(
            user_request=user_request,
            code=code,
            stdout=stdout,
            stderr=stderr,
            artifacts=artifacts,
            table_previews=table_previews,
        )
    )
    return {
        "status": "succeeded",
        "insight": draft.insight,
        "error": "",
        "metadata": draft.metadata,
    }


def _is_enabled() -> bool:
    return os.getenv("AI_EXPLAIN_RESULT_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}


def _collect_table_previews(root: Path, artifacts: list[dict[str, Any]]) -> list[dict[str, str]]:
    previews: list[dict[str, str]] = []
    for artifact in artifacts:
        if artifact.get("type") != "table":
            continue
        path = _artifact_path(root, artifact)
        if path is None:
            continue
        if not path.exists() or not path.is_file():
            continue
        if path.suffix.lower() == ".csv":
            previews.append({"name": path.name, "preview": _csv_preview(path)})
        elif path.suffix.lower() in {".json", ".md"}:
            previews.append({"name": path.name, "preview": path.read_text(encoding="utf-8", errors="replace")[:2000]})
    return previews[:2]


def _has_real_execution_output(
    *,
    stdout: str,
    stderr: str,
    artifacts: list[dict[str, Any]],
    table_previews: list[dict[str, str]],
) -> bool:
    return bool(stdout.strip() or stderr.strip() or artifacts or table_previews)


def _csv_preview(path: Path) -> str:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for index, row in enumerate(reader):
            rows.append(row)
            if index >= 20:
                break
    return "\n".join(",".join(cell for cell in row) for row in rows)


def _artifact_path(root: Path, artifact: dict[str, Any]) -> Path | None:
    raw_path = str(artifact.get("path", ""))
    resolved_root = root.resolve()
    resolved_path = (resolved_root / raw_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved_path


def _not_requested(reason: str) -> dict[str, Any]:
    return {"status": "not_requested", "insight": None, "error": reason, "metadata": {}}
