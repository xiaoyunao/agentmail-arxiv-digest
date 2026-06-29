from arxiv_digest import mail_cli
from arxiv_digest.imap_mail import ImapMessage
from arxiv_digest.subscriptions import SUBSCRIBE_SUBJECT


def test_latest_arxiv_filters_by_local_date(tmp_path, monkeypatch):
    messages = [
        {
            "message_id": "old_msg",
            "subject": "astro-ph daily old",
            "created_at": "2026-06-26T10:42:23Z",
        },
        {
            "message_id": "today_msg",
            "subject": "astro-ph daily today",
            "created_at": "2026-06-29T02:15:00Z",
        },
    ]

    monkeypatch.setattr(mail_cli, "search_messages", lambda query, limit: {"data": {"data": messages}})
    monkeypatch.setattr(mail_cli, "read_message", lambda message_id: {"data": {"body": f"body:{message_id}"}})
    monkeypatch.setattr(mail_cli, "load_env_file", lambda: None)

    output = tmp_path / "astro-ph.txt"
    assert mail_cli.main(["latest-arxiv", "--output", str(output), "--local-date", "2026-06-29"]) == 0

    assert output.read_text(encoding="utf-8") == "body:today_msg"


def test_latest_arxiv_exits_when_local_date_missing(tmp_path, monkeypatch):
    messages = [
        {
            "message_id": "old_msg",
            "subject": "astro-ph daily old",
            "created_at": "2026-06-26T10:42:23Z",
        },
    ]

    monkeypatch.setattr(mail_cli, "search_messages", lambda query, limit: {"data": {"data": messages}})
    monkeypatch.setattr(mail_cli, "load_env_file", lambda: None)

    output = tmp_path / "astro-ph.txt"
    try:
        mail_cli.main(["latest-arxiv", "--output", str(output), "--local-date", "2026-06-29"])
    except SystemExit as exc:
        assert "2026-06-29" in str(exc)
    else:
        raise AssertionError("expected SystemExit")
    assert not output.exists()


def test_latest_arxiv_gmail_writes_imap_body(tmp_path, monkeypatch):
    monkeypatch.setattr(mail_cli, "load_env_file", lambda: None)
    monkeypatch.setattr(
        mail_cli,
        "latest_arxiv_from_imap",
        lambda query, local_date, limit: ImapMessage(
            message_id="gmail_msg",
            subject="astro-ph daily",
            date="Mon, 29 Jun 2026 01:36:33 +0000",
            body="daily body",
        ),
    )

    output = tmp_path / "gmail-astro-ph.txt"
    assert mail_cli.main(["latest-arxiv-gmail", "--output", str(output), "--local-date", "2026-06-29"]) == 0

    assert output.read_text(encoding="utf-8") == "daily body"


def test_import_subscriptions_does_not_resend_unchanged_receipts(tmp_path, monkeypatch):
    sent = []
    message = {"message_id": "msg_1", "subject": SUBSCRIBE_SUBJECT}
    full_message = {
        "subject": SUBSCRIBE_SUBJECT,
        "from": {"email": "user@example.com"},
        "body": "dark matter; stellar streams",
    }

    monkeypatch.setattr(mail_cli, "search_messages", lambda query, limit: {"data": {"data": [message]}})
    monkeypatch.setattr(mail_cli, "read_message", lambda message_id: {"data": full_message})
    monkeypatch.setattr(mail_cli, "load_env_file", lambda: None)
    monkeypatch.setattr(
        mail_cli,
        "send_email",
        lambda to, subject, body, html_body=None: sent.append((to, subject, body, html_body)),
    )

    args = [
        "import-subscriptions",
        "--send-receipts",
        "--output-dir",
        str(tmp_path / "subscribers"),
        "--send-log",
        str(tmp_path / "send-log.sqlite3"),
    ]

    assert mail_cli.main(args) == 0
    assert mail_cli.main(args) == 0

    assert len(sent) == 1
    assert sent[0][0] == "user@example.com"
