from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


DEFAULT_SEND_LOG_PATH = ".arxiv_digest_send_log.sqlite3"


@dataclass(frozen=True)
class SentMessage:
    dedupe_key: str
    recipient: str
    subject: str
    message_type: str
    sent_at_utc: str
    metadata: dict[str, Any]


class SendLog:
    def __init__(self, path: str | Path = DEFAULT_SEND_LOG_PATH) -> None:
        self.path = Path(path)
        self._ensure_schema()

    def already_sent(self, dedupe_key: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "select 1 from sent_messages where dedupe_key = ?",
                (dedupe_key,),
            ).fetchone()
        return row is not None

    def record_sent(
        self,
        *,
        dedupe_key: str,
        recipient: str,
        subject: str,
        message_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        payload = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)
        sent_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                insert into sent_messages (
                    dedupe_key, recipient, subject, message_type, sent_at_utc, metadata_json
                ) values (?, ?, ?, ?, ?, ?)
                """,
                (dedupe_key, recipient, subject, message_type, sent_at, payload),
            )

    def get(self, dedupe_key: str) -> SentMessage | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                select dedupe_key, recipient, subject, message_type, sent_at_utc, metadata_json
                from sent_messages
                where dedupe_key = ?
                """,
                (dedupe_key,),
            ).fetchone()
        if row is None:
            return None
        return SentMessage(
            dedupe_key=row[0],
            recipient=row[1],
            subject=row[2],
            message_type=row[3],
            sent_at_utc=row[4],
            metadata=json.loads(row[5]),
        )

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists sent_messages (
                    dedupe_key text primary key,
                    recipient text not null,
                    subject text not null,
                    message_type text not null,
                    sent_at_utc text not null,
                    metadata_json text not null
                )
                """
            )
            conn.execute(
                """
                create index if not exists idx_sent_messages_recipient_type
                on sent_messages (recipient, message_type)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.path)


def make_dedupe_key(message_type: str, *parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{message_type}:{digest}"
