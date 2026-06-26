from __future__ import annotations

import argparse
from pathlib import Path

from .parser import parse_daily_email
from .profiles import InterestProfile
from .ranker import rank_papers, recall_papers
from .render import render_markdown_digest, render_triaged_markdown_digest
from .llm import DEFAULT_TRIAGE_MODEL
from .triage import triage_with_heuristics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse arXiv daily mail and render a profile digest.")
    parser.add_argument("--mail-file", required=True, help="Path to raw arXiv daily email text.")
    parser.add_argument("--profile", required=True, help="Path to profile JSON.")
    parser.add_argument("--output", help="Optional Markdown output path.")
    parser.add_argument(
        "--triage",
        choices=["rules", "heuristic-ai", "openai"],
        default="rules",
        help="rules uses deterministic recall ranking; heuristic-ai exercises the AI triage contract locally; openai calls the OpenAI API.",
    )
    parser.add_argument(
        "--openai-model",
        default=None,
        help=f"OpenAI model for --triage openai. Defaults to OPENAI_TRIAGE_MODEL or {DEFAULT_TRIAGE_MODEL}.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    mail_text = Path(args.mail_file).read_text(encoding="utf-8")
    profile = InterestProfile.from_json_file(args.profile)

    papers = parse_daily_email(mail_text)
    if args.triage == "rules":
        ranked = rank_papers(papers, profile)
        digest = render_markdown_digest(profile, ranked)
    else:
        recalled = recall_papers(papers, profile, limit=profile.recall_limit)
        if args.triage == "heuristic-ai":
            triaged = triage_with_heuristics(profile, recalled)
        else:
            from .llm import triage_with_openai

            triaged = triage_with_openai(profile, recalled, model=args.openai_model)
        digest = render_triaged_markdown_digest(profile, triaged)

    if args.output:
        Path(args.output).write_text(digest, encoding="utf-8")
    else:
        print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
