from __future__ import annotations

import uuid

from backend.app.services.execution_insight_service import _collect_table_previews, explain_execution_result
from backend.app.services.llm_provider import ExecutionInsightDraft


def test_explain_execution_result_loads_dotenv_before_enabled_check(monkeypatch, tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("AI_EXPLAIN_RESULT_ENABLED=false\n", encoding="utf-8")
    monkeypatch.setenv("AI_EXPLAIN_RESULT_ENABLED", "")
    monkeypatch.delenv("AI_EXPLAIN_RESULT_ENABLED", raising=False)

    from backend.app.core import env
    from backend.app.core import paths
    from backend.app.services import execution_insight_service

    monkeypatch.setattr(paths, "ROOT", tmp_path)
    monkeypatch.setattr(env, "ROOT", tmp_path)
    monkeypatch.setattr(execution_insight_service, "load_local_env", env.load_local_env)

    result = explain_execution_result(
        root=tmp_path,
        user_request="test",
        code="print('x')",
        stdout="",
        stderr="",
        artifacts=[],
    )

    assert result["status"] == "not_requested"
    assert result["error"] == "AI_EXPLAIN_RESULT_ENABLED=false"


def test_collect_table_previews_ignores_artifacts_outside_root(tmp_path):
    outside_path = tmp_path.parent / f"outside_{uuid.uuid4().hex}.csv"
    outside_path.write_text("a,b\n1,2\n", encoding="utf-8")
    try:
        previews = _collect_table_previews(
            tmp_path,
            [{"type": "table", "name": outside_path.name, "path": f"../{outside_path.name}"}],
        )

        assert previews == []
    finally:
        outside_path.unlink(missing_ok=True)


def test_explain_execution_result_uses_stdout_and_table_without_chart_image(monkeypatch, tmp_path):
    table_path = tmp_path / "runs" / "run_test" / "outputs" / "summary.csv"
    table_path.parent.mkdir(parents=True)
    table_path.write_text("region,revenue\nNorth,100\nSouth,200\n", encoding="utf-8")
    captured = {}

    class StubProvider:
        def explain_execution_result(self, payload):
            captured["payload"] = payload
            return ExecutionInsightDraft(
                insight="- South có revenue 200, cao hơn North 100 theo bảng output thật.",
                metadata={"provider": "stub"},
            )

    from backend.app.services import execution_insight_service

    monkeypatch.setenv("AI_EXPLAIN_RESULT_ENABLED", "true")
    monkeypatch.setattr(execution_insight_service, "get_execution_insight_provider", lambda: StubProvider())

    result = explain_execution_result(
        root=tmp_path,
        user_request="Nhan xet revenue theo region",
        code="print(summary)",
        stdout="region revenue\nNorth 100\nSouth 200",
        stderr="",
        artifacts=[{"type": "table", "name": "summary.csv", "path": "runs/run_test/outputs/summary.csv"}],
    )

    assert result["status"] == "succeeded"
    assert result["insight"].startswith("- South")
    assert captured["payload"].table_previews == [
        {"name": "summary.csv", "preview": "region,revenue\nNorth,100\nSouth,200"}
    ]


def test_explain_execution_result_is_not_requested_without_real_output(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_EXPLAIN_RESULT_ENABLED", "true")

    result = explain_execution_result(
        root=tmp_path,
        user_request="Nhan xet",
        code="print('x')",
        stdout="",
        stderr="",
        artifacts=[],
    )

    assert result["status"] == "not_requested"
    assert "stdout" in result["error"]
