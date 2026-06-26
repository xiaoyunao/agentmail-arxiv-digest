import os

from arxiv_digest.env import load_env_file


def test_load_env_file_does_not_override_existing_values(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "OPENAI_API_KEY=from-file\nOPENAI_TRIAGE_MODEL=from-file-model\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "already-set")
    monkeypatch.delenv("OPENAI_TRIAGE_MODEL", raising=False)

    load_env_file(env_path)

    assert os.environ["OPENAI_API_KEY"] == "already-set"
    assert os.environ["OPENAI_TRIAGE_MODEL"] == "from-file-model"
