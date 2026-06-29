from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import imaplib
import os
from zoneinfo import ZoneInfo


class ImapConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImapConfig:
    host: str
    port: int
    username: str
    password: str
    mailbox: str = "INBOX"
    timeout: float = 30.0


@dataclass(frozen=True)
class ImapMessage:
    message_id: str
    subject: str
    date: str
    body: str


def imap_config_from_env(prefix: str = "DAILYARXIV_IMAP_") -> ImapConfig:
    host = os.environ.get(f"{prefix}HOST", "imap.gmail.com").strip()
    username = _env_or_fallback(f"{prefix}USERNAME", "DAILYARXIV_SMTP_USERNAME")
    password = _env_or_fallback(f"{prefix}PASSWORD", "DAILYARXIV_SMTP_PASSWORD")
    mailbox = os.environ.get(f"{prefix}MAILBOX", "INBOX").strip() or "INBOX"
    port = int(os.environ.get(f"{prefix}PORT", "993"))
    return ImapConfig(host=host, port=port, username=username, password=password, mailbox=mailbox)


def latest_arxiv_from_imap(
    *,
    query: str = "astro-ph daily",
    local_date: str | None = None,
    limit: int = 20,
    config: ImapConfig | None = None,
) -> ImapMessage:
    config = config or imap_config_from_env()
    local_date = local_date or datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    cutoff = _imap_since_date(local_date)
    with imaplib.IMAP4_SSL(config.host, config.port, timeout=config.timeout) as imap:
        _check(imap.login(config.username, config.password), "login")
        _check(imap.select(config.mailbox, readonly=True), f"select {config.mailbox}")
        status, data = imap.search(None, "SINCE", cutoff)
        _check((status, data), f"search since {cutoff}")
        ids = data[0].split()
        for raw_id in reversed(ids[-limit:]):
            status, payload = imap.fetch(raw_id, "(RFC822)")
            _check((status, payload), f"fetch {raw_id.decode()}")
            parsed = _parse_fetch_payload(payload)
            if not parsed:
                continue
            if _message_local_date(parsed) != local_date:
                continue
            subject = parsed.get("Subject", "")
            body = _extract_text_body(parsed)
            haystack = f"{subject}\n{body}".lower()
            if query.lower() not in haystack:
                continue
            return ImapMessage(
                message_id=parsed.get("Message-ID", raw_id.decode()),
                subject=subject,
                date=parsed.get("Date", ""),
                body=body,
            )
    raise SystemExit(f"no Gmail IMAP messages found for query: {query} on local date {local_date}")


def _parse_fetch_payload(payload: list[bytes | tuple[bytes, bytes]]) -> Message | None:
    for item in payload:
        if isinstance(item, tuple):
            return BytesParser(policy=policy.default).parsebytes(item[1])
    return None


def _extract_text_body(message: Message) -> str:
    if message.is_multipart():
        plain_parts = []
        html_parts = []
        for part in message.walk():
            if part.is_multipart():
                continue
            disposition = part.get_content_disposition()
            if disposition == "attachment":
                continue
            content_type = part.get_content_type()
            try:
                content = part.get_content()
            except LookupError:
                content = _decode_payload(part)
            if content_type == "text/plain":
                plain_parts.append(content)
            elif content_type == "text/html":
                html_parts.append(content)
        if plain_parts:
            return "\n".join(plain_parts)
        return "\n".join(html_parts)
    try:
        return message.get_content()
    except LookupError:
        return _decode_payload(message)


def _decode_payload(message: Message) -> str:
    payload = message.get_payload(decode=True) or b""
    charset = message.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _message_local_date(message: Message) -> str | None:
    raw_date = message.get("Date")
    if not raw_date:
        return None
    parsed = parsedate_to_datetime(raw_date)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
    return parsed.astimezone(ZoneInfo("Asia/Shanghai")).date().isoformat()


def _imap_since_date(local_date: str) -> str:
    dt = datetime.fromisoformat(local_date)
    return dt.strftime("%d-%b-%Y")


def _env_or_fallback(key: str, fallback_key: str) -> str:
    value = os.environ.get(key, "").strip() or os.environ.get(fallback_key, "").strip()
    if not value:
        raise ImapConfigError(f"missing required environment variable: {key} or {fallback_key}")
    return value


def _check(result: tuple[str, list[bytes]], action: str) -> None:
    status, data = result
    if status != "OK":
        detail = data[0].decode(errors="replace") if data else ""
        raise RuntimeError(f"IMAP {action} failed: {detail}")
