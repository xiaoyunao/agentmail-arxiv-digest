import os
from email.message import EmailMessage

import pytest

from arxiv_digest.imap_mail import (
    ImapConfigError,
    _extract_text_body,
    _message_local_date,
    imap_config_from_env,
)


def test_imap_config_defaults_to_gmail_and_smtp_credentials(monkeypatch):
    monkeypatch.setenv("DAILYARXIV_SMTP_USERNAME", "dailyarxiv.digest@gmail.com")
    monkeypatch.setenv("DAILYARXIV_SMTP_PASSWORD", "secret")

    config = imap_config_from_env()

    assert config.host == "imap.gmail.com"
    assert config.port == 993
    assert config.username == "dailyarxiv.digest@gmail.com"
    assert config.password == "secret"
    assert config.mailbox == "INBOX"


def test_imap_config_requires_credentials(monkeypatch):
    for key in list(os.environ):
        if key.startswith("DAILYARXIV_IMAP_") or key.startswith("DAILYARXIV_SMTP_"):
            monkeypatch.delenv(key, raising=False)

    with pytest.raises(ImapConfigError, match="DAILYARXIV_IMAP_USERNAME"):
        imap_config_from_env()


def test_extract_text_body_prefers_plain_text():
    message = EmailMessage()
    message.set_content("plain body")
    message.add_alternative("<p>html body</p>", subtype="html")

    assert _extract_text_body(message).strip() == "plain body"


def test_message_local_date_uses_beijing_time():
    message = EmailMessage()
    message["Date"] = "Mon, 29 Jun 2026 01:36:33 +0000"

    assert _message_local_date(message) == "2026-06-29"
