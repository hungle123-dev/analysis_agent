from __future__ import annotations

from backend.app.core import env


def test_load_local_env_reads_dotenv_without_overriding(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AI_PROVIDER=deepseek",
                "DEEPSEEK_BASE_URL='http://127.0.0.1:5001'",
                "EXISTING_VALUE=from_file",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(env, "ROOT", tmp_path)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.setenv("EXISTING_VALUE", "from_env")

    env.load_local_env()

    assert env.os.environ["AI_PROVIDER"] == "deepseek"
    assert env.os.environ["DEEPSEEK_BASE_URL"] == "http://127.0.0.1:5001"
    assert env.os.environ["EXISTING_VALUE"] == "from_env"
