from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import os
import smtplib


class SmtpConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str = "dailyarxiv"
    security: str = "starttls"
    timeout: float = 30.0


def smtp_config_from_env(prefix: str = "DAILYARXIV_SMTP_") -> SmtpConfig:
    host = _required_env(f"{prefix}HOST")
    username = _required_env(f"{prefix}USERNAME")
    password = _required_env(f"{prefix}PASSWORD")
    from_email = os.environ.get(f"{prefix}FROM_EMAIL", username).strip()
    from_name = os.environ.get(f"{prefix}FROM_NAME", "dailyarxiv").strip()
    security = os.environ.get(f"{prefix}SECURITY", "starttls").strip().lower()
    if security not in {"starttls", "ssl", "none"}:
        raise SmtpConfigError(f"{prefix}SECURITY must be one of: starttls, ssl, none")
    default_port = 465 if security == "ssl" else 587
    port = int(os.environ.get(f"{prefix}PORT", str(default_port)))
    return SmtpConfig(
        host=host,
        port=port,
        username=username,
        password=password,
        from_email=from_email,
        from_name=from_name,
        security=security,
    )


def build_email_message(
    config: SmtpConfig,
    to: str,
    subject: str,
    body: str,
    *,
    html_body: str | None = None,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = f"{config.from_name} <{config.from_email}>"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")
    return message


def send_email(
    to: str,
    subject: str,
    body: str,
    *,
    html_body: str | None = None,
    config: SmtpConfig | None = None,
) -> None:
    config = config or smtp_config_from_env()
    message = build_email_message(config, to, subject, body, html_body=html_body)
    if config.security == "ssl":
        with smtplib.SMTP_SSL(config.host, config.port, timeout=config.timeout) as smtp:
            _login_and_send(smtp, config, message)
        return

    with smtplib.SMTP(config.host, config.port, timeout=config.timeout) as smtp:
        if config.security == "starttls":
            smtp.starttls()
        _login_and_send(smtp, config, message)


def _login_and_send(smtp: smtplib.SMTP, config: SmtpConfig, message: EmailMessage) -> None:
    smtp.login(config.username, config.password)
    smtp.send_message(message)


def _required_env(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        raise SmtpConfigError(f"missing required environment variable: {key}")
    return value
