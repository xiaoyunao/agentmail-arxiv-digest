import os

import pytest

from arxiv_digest.smtp_sender import SmtpConfig, SmtpConfigError, build_email_message, smtp_config_from_env


def test_smtp_config_from_env(monkeypatch):
    monkeypatch.setenv("DAILYARXIV_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("DAILYARXIV_SMTP_USERNAME", "daily@example.com")
    monkeypatch.setenv("DAILYARXIV_SMTP_PASSWORD", "secret")
    monkeypatch.setenv("DAILYARXIV_SMTP_FROM_EMAIL", "digest@example.com")
    monkeypatch.setenv("DAILYARXIV_SMTP_FROM_NAME", "Daily Arxiv")
    monkeypatch.setenv("DAILYARXIV_SMTP_SECURITY", "ssl")

    config = smtp_config_from_env()

    assert config.host == "smtp.example.com"
    assert config.port == 465
    assert config.from_email == "digest@example.com"
    assert config.from_name == "Daily Arxiv"


def test_smtp_config_requires_host(monkeypatch):
    for key in list(os.environ):
        if key.startswith("DAILYARXIV_SMTP_"):
            monkeypatch.delenv(key, raising=False)

    with pytest.raises(SmtpConfigError, match="DAILYARXIV_SMTP_HOST"):
        smtp_config_from_env()


def test_build_email_message():
    config = SmtpConfig(
        host="smtp.example.com",
        port=587,
        username="daily@example.com",
        password="secret",
        from_email="digest@example.com",
        from_name="Daily Arxiv",
    )

    message = build_email_message(config, "user@example.com", "Subject", "Body")

    assert message["From"] == "Daily Arxiv <digest@example.com>"
    assert message["To"] == "user@example.com"
    assert message["Subject"] == "Subject"
    assert message.get_content().strip() == "Body"


def test_build_email_message_with_html_alternative():
    config = SmtpConfig(
        host="smtp.example.com",
        port=587,
        username="daily@example.com",
        password="secret",
        from_email="digest@example.com",
        from_name="Daily Arxiv",
    )

    message = build_email_message(
        config,
        "user@example.com",
        "Subject",
        "Plain body",
        html_body="<h1>HTML body</h1>",
    )

    assert message.is_multipart()
    parts = list(message.iter_parts())
    assert parts[0].get_content_type() == "text/plain"
    assert parts[1].get_content_type() == "text/html"
    assert "Plain body" in parts[0].get_content()
    assert "<h1>HTML body</h1>" in parts[1].get_content()
