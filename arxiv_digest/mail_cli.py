from __future__ import annotations

import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .cleanup import cleanup_runtime_files
from .env import load_env_file
from .imap_mail import latest_arxiv_from_imap
from .mail import prepare_send, read_message, search_messages
from .profiles import InterestProfile
from .send_log import DEFAULT_SEND_LOG_PATH, SendLog, make_dedupe_key
from .smtp_sender import send_email
from .subscriptions import (
    SUBSCRIBE_SUBJECT,
    is_subscription_subject,
    parse_subscription_request,
    render_subscription_receipt,
    render_subscription_receipt_html,
    save_profile,
    should_send_subscription_receipt,
    subscription_receipt_subject,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent Mail helpers for arXiv digest workflows.")
    sub = parser.add_subparsers(dest="command", required=True)

    latest = sub.add_parser("latest-arxiv", help="Fetch latest arXiv daily email body to a file.")
    latest.add_argument("--query", default="astro-ph daily", help="Search query for arXiv daily email.")
    latest.add_argument("--output", required=True, help="Output text path.")
    latest.add_argument("--limit", type=int, default=10)
    latest.add_argument(
        "--local-date",
        help="Only accept a message whose created_at matches this Asia/Shanghai date, e.g. 2026-06-29.",
    )

    latest_gmail = sub.add_parser("latest-arxiv-gmail", help="Fetch latest arXiv daily email body from Gmail IMAP.")
    latest_gmail.add_argument("--query", default="astro-ph daily", help="Search text for arXiv daily email.")
    latest_gmail.add_argument("--output", required=True, help="Output text path.")
    latest_gmail.add_argument("--limit", type=int, default=20)
    latest_gmail.add_argument(
        "--local-date",
        help="Only accept a message whose Date header matches this Asia/Shanghai date, e.g. 2026-06-29.",
    )

    subs = sub.add_parser("import-subscriptions", help="Import fixed-format subscription request emails.")
    subs.add_argument("--query", default=SUBSCRIBE_SUBJECT)
    subs.add_argument("--limit", type=int, default=20)
    subs.add_argument("--output-dir", default="subscribers")
    subs.add_argument("--send-receipts", action="store_true", help="Send automatic subscription receipts via SMTP.")
    subs.add_argument("--send-log", default=DEFAULT_SEND_LOG_PATH, help="SQLite send log path for receipt dedupe.")

    send = sub.add_parser("prepare-send", help="Prepare a digest email and print confirmation details.")
    send.add_argument("--to", required=True)
    send.add_argument("--subject", required=True)
    send.add_argument("--body-file", required=True)

    smtp = sub.add_parser("send-smtp", help="Send an email immediately through the configured SMTP backend.")
    smtp.add_argument("--to", required=True)
    smtp.add_argument("--subject", required=True)
    smtp.add_argument("--body-file", required=True)
    smtp.add_argument("--html-body-file", help="Optional HTML body path for rich email rendering.")
    smtp.add_argument("--message-type", default="smtp", help="Message type stored in the send log.")
    smtp.add_argument("--dedupe-key", help="Optional explicit dedupe key. Defaults to recipient+subject+body hash.")
    smtp.add_argument("--send-log", default=DEFAULT_SEND_LOG_PATH, help="SQLite send log path.")
    smtp.add_argument("--force", action="store_true", help="Send even if the dedupe key already exists.")

    cleanup = sub.add_parser("cleanup", help="Remove old runtime files after daily digest sends.")
    cleanup.add_argument("--keep-days", type=int, default=7, help="Keep files newer than this many days.")
    cleanup.add_argument("--path", action="append", default=["data", "out"], help="Runtime directory to clean. Repeatable.")
    cleanup.add_argument("--drop-cache", action="store_true", help="Also delete local summary cache sqlite files.")

    return parser


def main(argv: list[str] | None = None) -> int:
    load_env_file()
    args = build_parser().parse_args(argv)
    if args.command == "latest-arxiv":
        message = _latest_message(args.query, args.limit, local_date=args.local_date)
        body = read_message(message["message_id"])["data"]["body"]
        Path(args.output).write_text(body, encoding="utf-8")
        print(f"wrote {args.output} from {message['message_id']}")
        return 0

    if args.command == "latest-arxiv-gmail":
        message = latest_arxiv_from_imap(query=args.query, local_date=args.local_date, limit=args.limit)
        Path(args.output).write_text(message.body, encoding="utf-8")
        print(f"wrote {args.output} from Gmail IMAP message {message.message_id}")
        return 0

    if args.command == "import-subscriptions":
        result = search_messages(args.query, limit=args.limit)
        send_log = SendLog(args.send_log) if args.send_receipts else None
        imported = []
        for message in result["data"].get("data", []):
            full = read_message(message["message_id"])["data"]
            subject = full.get("subject") or message.get("subject") or ""
            if not is_subscription_subject(subject):
                continue
            sender = full.get("from", {}).get("email", "")
            profile = parse_subscription_request(full.get("body", ""), sender)
            receipt_key = _subscription_receipt_key(profile)
            profile_changed = should_send_subscription_receipt(profile, args.output_dir)
            send_receipt = (
                send_log is not None
                and profile_changed
                and not send_log.already_sent(receipt_key)
            )
            path = save_profile(profile, args.output_dir)
            imported.append(path)
            if send_receipt:
                receipt_subject = subscription_receipt_subject()
                send_email(
                    profile.recipient,
                    receipt_subject,
                    render_subscription_receipt(profile),
                    html_body=render_subscription_receipt_html(profile),
                )
                send_log.record_sent(
                    dedupe_key=receipt_key,
                    recipient=profile.recipient,
                    subject=receipt_subject,
                    message_type="subscription_receipt",
                    metadata={
                        "message_id": message.get("message_id"),
                        "interests": list(profile.research_interests),
                    },
                )
        for path in imported:
            print(path)
        return 0

    if args.command == "prepare-send":
        body = Path(args.body_file).read_text(encoding="utf-8")
        result = prepare_send(args.to, args.subject, body)
        print(result)
        return 0

    if args.command == "send-smtp":
        body = Path(args.body_file).read_text(encoding="utf-8")
        html_body = Path(args.html_body_file).read_text(encoding="utf-8") if args.html_body_file else None
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if html_body:
            body_hash = hashlib.sha256((body + "\n--HTML--\n" + html_body).encode("utf-8")).hexdigest()
        dedupe_key = args.dedupe_key or make_dedupe_key(args.message_type, args.to, args.subject, body_hash)
        send_log = SendLog(args.send_log)
        if not args.force and send_log.already_sent(dedupe_key):
            print(f"skipped duplicate {args.subject!r} to {args.to} via SMTP ({dedupe_key})")
            return 0
        send_email(args.to, args.subject, body, html_body=html_body)
        send_log.record_sent(
            dedupe_key=dedupe_key,
            recipient=args.to,
            subject=args.subject,
            message_type=args.message_type,
            metadata={"body_file": args.body_file, "body_sha256": body_hash},
        )
        print(f"sent {args.subject!r} to {args.to} via SMTP")
        return 0

    if args.command == "cleanup":
        removed = cleanup_runtime_files(args.path, keep_days=args.keep_days, drop_cache=args.drop_cache)
        for path in removed:
            print(path)
        print(f"removed {len(removed)} files")
        return 0

    raise SystemExit(f"unknown command: {args.command}")


def _latest_message(query: str, limit: int, *, local_date: str | None = None) -> dict:
    result = search_messages(query, limit=limit)
    messages = result["data"].get("data", [])
    if local_date:
        messages = [
            message
            for message in messages
            if _message_local_date(message) == local_date
        ]
    if not messages:
        date_suffix = f" on local date {local_date}" if local_date else ""
        raise SystemExit(f"no messages found for query: {query}{date_suffix}")
    return messages[0]


def _message_local_date(message: dict) -> str | None:
    created_at = message.get("created_at")
    if not created_at:
        return None
    if created_at.endswith("Z"):
        created_at = created_at[:-1] + "+00:00"
    return (
        datetime.fromisoformat(created_at)
        .astimezone(ZoneInfo("Asia/Shanghai"))
        .date()
        .isoformat()
    )


def _subscription_receipt_key(profile: InterestProfile) -> str:
    return make_dedupe_key(
        "subscription_receipt",
        profile.recipient,
        list(profile.research_interests),
        list(profile.include_categories),
        profile.summary_requirements,
    )


if __name__ == "__main__":
    raise SystemExit(main())
