from __future__ import annotations

import argparse
from pathlib import Path

from .parser import parse_daily_email
from .profiles import InterestProfile
from .ranker import rank_papers
from .render import render_markdown_digest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse arXiv daily mail and render a profile digest.")
    parser.add_argument("--mail-file", required=True, help="Path to raw arXiv daily email text.")
    parser.add_argument("--profile", required=True, help="Path to profile JSON.")
    parser.add_argument("--output", help="Optional Markdown output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    mail_text = Path(args.mail_file).read_text(encoding="utf-8")
    profile = InterestProfile.from_json_file(args.profile)

    papers = parse_daily_email(mail_text)
    ranked = rank_papers(papers, profile)
    digest = render_markdown_digest(profile, ranked)

    if args.output:
        Path(args.output).write_text(digest, encoding="utf-8")
    else:
        print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
