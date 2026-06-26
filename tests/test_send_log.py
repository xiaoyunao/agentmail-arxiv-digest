import sqlite3

import pytest

from arxiv_digest.send_log import SendLog, make_dedupe_key


def test_make_dedupe_key_is_stable_and_namespaced():
    key = make_dedupe_key("digest", "user@example.com", "subject", "body-hash")

    assert key == make_dedupe_key("digest", "user@example.com", "subject", "body-hash")
    assert key != make_dedupe_key("receipt", "user@example.com", "subject", "body-hash")
    assert key.startswith("digest:")


def test_send_log_records_and_reads_sent_messages(tmp_path):
    log = SendLog(tmp_path / "send-log.sqlite3")
    key = make_dedupe_key("digest", "user@example.com", "subject")

    assert not log.already_sent(key)
    log.record_sent(
        dedupe_key=key,
        recipient="user@example.com",
        subject="dailyarxiv digest",
        message_type="digest",
        metadata={"date": "2026-06-26"},
    )

    assert log.already_sent(key)
    sent = log.get(key)
    assert sent is not None
    assert sent.recipient == "user@example.com"
    assert sent.subject == "dailyarxiv digest"
    assert sent.message_type == "digest"
    assert sent.metadata["date"] == "2026-06-26"


def test_send_log_rejects_duplicate_records(tmp_path):
    log = SendLog(tmp_path / "send-log.sqlite3")
    key = make_dedupe_key("digest", "user@example.com", "subject")
    log.record_sent(
        dedupe_key=key,
        recipient="user@example.com",
        subject="dailyarxiv digest",
        message_type="digest",
    )

    with pytest.raises(sqlite3.IntegrityError):
        log.record_sent(
            dedupe_key=key,
            recipient="user@example.com",
            subject="dailyarxiv digest",
            message_type="digest",
        )
