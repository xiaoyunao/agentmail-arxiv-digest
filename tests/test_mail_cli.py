from arxiv_digest import mail_cli
from arxiv_digest.subscriptions import SUBSCRIBE_SUBJECT


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
