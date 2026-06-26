from __future__ import annotations

import argparse
from pathlib import Path

from .env import load_env_file
from .llm import DEFAULT_TRIAGE_MODEL
from .parser import parse_daily_email
from .profiles import InterestProfile
from .ranker import rank_papers, recall_papers
from .render import render_markdown_digest, render_summarized_markdown_digest, render_triaged_markdown_digest
from .codex_backend import (
    export_codex_summary_tasks,
    export_codex_review_tasks,
    import_codex_review_summaries,
    import_codex_summaries,
    load_cached_codex_summaries,
)
from .triage import triage_with_heuristics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse arXiv daily mail and render a profile digest.")
    parser.add_argument("--mail-file", required=True, help="Path to raw arXiv daily email text.")
    parser.add_argument("--profile", required=True, help="Path to profile JSON.")
    parser.add_argument("--output", help="Optional Markdown output path.")
    parser.add_argument("--export-codex-tasks", help="Write triaged summary tasks for Codex to this JSON file.")
    parser.add_argument("--import-codex-summaries", help="Read Codex-produced summaries from this JSON file and render final digest.")
    parser.add_argument("--use-summary-cache", action="store_true", help="Render cached Codex summaries when available.")
    parser.add_argument(
        "--triage",
        choices=["rules", "codex", "heuristic-ai", "openai"],
        default="rules",
        help="rules uses deterministic ranking; codex exports/imports Codex review tasks; heuristic-ai is local smoke testing; openai is optional API mode.",
    )
    parser.add_argument(
        "--openai-model",
        default=None,
        help=f"OpenAI model for --triage openai. Defaults to OPENAI_TRIAGE_MODEL or {DEFAULT_TRIAGE_MODEL}.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_env_file()
    args = build_parser().parse_args(argv)
    mail_text = Path(args.mail_file).read_text(encoding="utf-8")
    profile = InterestProfile.from_json_file(args.profile)

    papers = parse_daily_email(mail_text)
    if args.triage == "rules":
        if args.export_codex_tasks or args.import_codex_summaries or args.use_summary_cache:
            raise SystemExit("--triage rules cannot export/import summaries; use --triage codex")
        ranked = rank_papers(papers, profile)
        digest = render_markdown_digest(profile, ranked)
    elif args.triage == "codex":
        recalled = recall_papers(papers, profile, limit=profile.recall_limit)
        if args.export_codex_tasks:
            export_codex_review_tasks(profile, recalled, args.export_codex_tasks)
        if args.import_codex_summaries:
            summarized = import_codex_review_summaries(profile, recalled, args.import_codex_summaries)
            digest = render_summarized_markdown_digest(profile, summarized)
        elif args.export_codex_tasks:
            digest = render_markdown_digest(profile, recalled)
        else:
            raise SystemExit("--triage codex requires --export-codex-tasks or --import-codex-summaries")
    else:
        recalled = recall_papers(papers, profile, limit=profile.recall_limit)
        if args.triage == "heuristic-ai":
            triaged = triage_with_heuristics(profile, recalled)
        else:
            from .llm import triage_with_openai

            triaged = triage_with_openai(profile, recalled, model=args.openai_model)

        if args.export_codex_tasks:
            export_codex_summary_tasks(profile, triaged, args.export_codex_tasks)

        if args.import_codex_summaries:
            summarized = import_codex_summaries(profile, triaged, args.import_codex_summaries)
            digest = render_summarized_markdown_digest(profile, summarized)
        elif args.use_summary_cache:
            summarized = load_cached_codex_summaries(profile, triaged)
            digest = render_summarized_markdown_digest(profile, summarized)
        else:
            digest = render_triaged_markdown_digest(profile, triaged)

    if args.output:
        Path(args.output).write_text(digest, encoding="utf-8")
    else:
        print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
