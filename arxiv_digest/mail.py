from __future__ import annotations

import json
import subprocess
from typing import Any


def list_messages(*, limit: int = 10, directory: str = "inbox") -> dict[str, Any]:
    return _run_json(["agently-cli", "message", "+list", "--dir", directory, "--limit", str(limit)])


def read_message(message_id: str) -> dict[str, Any]:
    return _run_json(["agently-cli", "message", "+read", "--id", message_id])


def search_messages(query: str, *, limit: int = 10, directory: str = "inbox") -> dict[str, Any]:
    return _run_json(["agently-cli", "message", "+search", "--q", query, "--dir", directory, "--limit", str(limit)])


def prepare_send(to: str, subject: str, body: str) -> dict[str, Any]:
    return _run_json_checked(
        ["agently-cli", "message", "+send", "--to", to, "--subject", subject, "--body", body],
        ok_returncodes=(0, 8),
    )


def confirm_send(to: str, subject: str, body: str, confirmation_token: str) -> dict[str, Any]:
    return _run_json(
        [
            "agently-cli",
            "message",
            "+send",
            "--to",
            to,
            "--subject",
            subject,
            "--body",
            body,
            "--confirmation-token",
            confirmation_token,
        ]
    )


def _run_json(argv: list[str]) -> dict[str, Any]:
    return _run_json_checked(argv, ok_returncodes=(0,))


def _run_json_checked(argv: list[str], *, ok_returncodes: tuple[int, ...]) -> dict[str, Any]:
    completed = subprocess.run(argv, check=False, text=True, capture_output=True)
    text = completed.stdout.strip()
    if completed.returncode not in ok_returncodes:
        raise RuntimeError(f"{' '.join(argv)} failed: {text or completed.stderr.strip()}")
    return _loads_json_with_tips(text)


def _loads_json_with_tips(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"command did not return JSON: {text}")
    return json.loads(text[start : end + 1])
