from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

from .profiles import InterestProfile

DEFAULT_CACHE_PATH = ".arxiv_digest_cache.sqlite3"


class SummaryCache:
    def __init__(self, path: str | Path = DEFAULT_CACHE_PATH) -> None:
        self.path = Path(path)
        self._ensure_schema()

    def get(self, key: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT payload_json FROM summaries WHERE cache_key = ?", (key,)).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def put(
        self,
        key: str,
        *,
        arxiv_id: str,
        profile_hash: str,
        model: str,
        prompt_version: str,
        payload: dict[str, Any],
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO summaries
                (cache_key, arxiv_id, profile_hash, model, prompt_version, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (key, arxiv_id, profile_hash, model, prompt_version, json.dumps(payload, ensure_ascii=False)),
            )

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS summaries (
                    cache_key TEXT PRIMARY KEY,
                    arxiv_id TEXT NOT NULL,
                    profile_hash TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )


def profile_hash(profile: InterestProfile) -> str:
    payload = json.dumps(profile.cache_payload(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def summary_cache_key(
    *,
    arxiv_id: str,
    profile: InterestProfile,
    model: str,
    prompt_version: str,
) -> str:
    payload = {
        "arxiv_id": arxiv_id,
        "profile_hash": profile_hash(profile),
        "model": model,
        "prompt_version": prompt_version,
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
