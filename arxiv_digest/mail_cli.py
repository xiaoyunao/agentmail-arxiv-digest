from __future__ import annotations

import argparse
from pathlib import Path

from .cleanup import cleanup_runtime_files
from .env import load_env_file
from .mail import prepare_send, read_message, search_messages
from .smtp_sender import send_email
from .subscriptions import (
    SUBSCRIBE_SUBJECT,
    is_subscription_subject,
    parse_subscription_request,
    render_subscription_receipt,
    save_profile,
    subscription_receipt_subject,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent Mail helpers for arXiv digest workflows.")
    sub = parser.add_subparsers(dest="command", required=True)

    latest = sub.add_parser("latest-arxiv", help="Fetch latest arXiv daily email body to a file.")
    latest.add_argument("--query", default="astro-ph daily", help="Search query for arXiv daily email.")
    latest.add_argument("--output", required=True, help="Output text path.")
    latest.add_argument("--limit", type=int, default=10)

    subs = sub.add_parser("import-subscriptions", help="Import fixed-format subscription request emails.")
    subs.add_argument("--query", default=SUBSCRIBE_SUBJECT)
    subs.add_argument("--limit", type=int, default=20)
    subs.add_argument("--output-dir", default="subscribers")
    subs.add_argument("--send-receipts", action="store_true", help="Send automatic subscription receipts via SMTP.")

    send = sub.add_parser("prepare-send", help="Prepare a digest email and print confirmation details.")
    send.add_argument("--to", required=True)
    send.add_argument("--subject", required=True)
    send.add_argument("--body-file", required=True)

    smtp = sub.add_parser("send-smtp", help="Send an email immediately through the configured SMTP backend.")
    smtp.add_argument("--to", required=True)
    smtp.add_argument("--subject", required=True)
    smtp.add_argument("--body-file", required=True)

    cleanup = sub.add_parser("cleanup", help="Remove old runtime files after daily digest sends.")
    cleanup.add_argument("--keep-days", type=int, default=7, help="Keep files newer than this many days.")
    cleanup.add_argument("--path", action="append", default=["data", "out"], help="Runtime directory to clean. Repeatable.")
    cleanup.add_argument("--drop-cache", action="store_true", help="Also delete local summary cache sqlite files.")

    return parser


def main(argv: list[str] | None = None) -> int:
    load_env_file()
    args = build_parser().parse_args(argv)
    if args.command == "latest-arxiv":
        message = _latest_message(args.query, args.limit)
        body = read_message(message["message_id"])["data"]["body"]
        Path(args.output).write_text(body, encoding="utf-8")
        print(f"wrote {args.output} from {message['message_id']}")
        return 0

    if args.command == "import-subscriptions":
        result = search_messages(args.query, limit=args.limit)
        imported = []
        for message in result["data"].get("data", []):
            full = read_message(message["message_id"])["data"]
            subject = full.get("subject") or message.get("subject") or ""
            if not is_subscription_subject(subject):
                continue
            sender = full.get("from", {}).get("email", "")
            profile = parse_subscription_request(full.get("body", ""), sender)
            path = save_profile(profile, args.output_dir)
            imported.append(path)
            if args.send_receipts:
                send_email(
                    profile.recipient,
                    subscription_receipt_subject(),
                    render_subscription_receipt(profile),
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
        send_email(args.to, args.subject, body)
        print(f"sent {args.subject!r} to {args.to} via SMTP")
        return 0

    if args.command == "cleanup":
        removed = cleanup_runtime_files(args.path, keep_days=args.keep_days, drop_cache=args.drop_cache)
        for path in removed:
            print(path)
        print(f"removed {len(removed)} files")
        return 0

    raise SystemExit(f"unknown command: {args.command}")


def _latest_message(query: str, limit: int) -> dict:
    result = search_messages(query, limit=limit)
    messages = result["data"].get("data", [])
    if not messages:
        raise SystemExit(f"no messages found for query: {query}")
    return messages[0]


if __name__ == "__main__":
    raise SystemExit(main())
