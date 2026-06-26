from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cache import SummaryCache, profile_hash, summary_cache_key
from .profiles import InterestProfile
from .ranker import RankedPaper
from .summary import SUMMARY_PROMPT_VERSION, PaperSummary, SummarizedPaper
from .triage import TriageDecision, TriagedPaper

CODEX_SUMMARY_MODEL = "codex"


def export_codex_summary_tasks(
    profile: InterestProfile,
    triaged: list[TriagedPaper],
    output_path: str | Path,
) -> None:
    payload = {
        "type": "arxiv_digest_codex_summary_tasks",
        "prompt_version": SUMMARY_PROMPT_VERSION,
        "profile": profile.cache_payload(),
        "instructions": [
            "For each task, use metadata and abstract only for orientation, then open the arXiv URL or PDF and read the full paper before writing.",
            "Do not write a full digest from the abstract alone. If the full text is inaccessible, say so in limitations and keep the summary minimal.",
            "Return JSON matching the summaries schema in this file.",
        ],
        "summary_schema": {
            "arxiv_id": "string",
            "paper_type": "string",
            "topic_sentence": "string",
            "one_sentence_takeaway": "string",
            "why_matched": "string",
            "quick_takeaways": ["string"],
            "background": "string",
            "method_data": "string",
            "key_results": ["string"],
            "main_results": "string",
            "figure_guide": "string",
            "physical_picture": "string",
            "novelty_value": "string",
            "relevance_to_profile": "string",
            "limitations": "string",
            "recommended_reading": "string",
            "follow_up_questions": [],
            "read_priority": "low|medium|high|must_read",
            "suggested_tags": ["string"],
        },
        "tasks": [_task_payload(item) for item in triaged],
    }
    Path(output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_codex_review_tasks(
    profile: InterestProfile,
    recalled: list[RankedPaper],
    output_path: str | Path,
) -> None:
    payload = {
        "type": "arxiv_digest_codex_review_tasks",
        "prompt_version": SUMMARY_PROMPT_VERSION,
        "profile": profile.cache_payload(),
        "instructions": [
            "For each recalled paper, first decide semantic relevance for this user.",
            "At triage time, the recall score and keyword reasons are only hints; do not treat them as final relevance.",
            "Use action=skip for irrelevant papers, short for marginally useful papers, full_read for papers worth a detailed digest.",
            "Only include papers with action short or full_read in the summaries array.",
            "For every included paper, open the arXiv URL or PDF and read the full paper before writing the Chinese summary.",
            "Do not write an included summary from the abstract alone. If full text access fails, either omit the paper or state the access failure clearly in limitations and keep the summary minimal.",
            "Use a research-note tone: specific, concise, and not promotional or generic.",
            "Keep the same section contract every day so subscriber reports stay consistent.",
            "If a field is not supported by the full paper, explicitly say that the paper does not state it.",
            "Set follow_up_questions to an empty array; it is retained only for backward-compatible JSON parsing and is not shown in email.",
            "Return JSON with a top-level summaries array matching the schema in this file.",
        ],
        "summary_item_schema": {
            "arxiv_id": "string",
            "triage": {
                "action": "short|full_read",
                "relevance_score": "number from 0 to 1",
                "reason": "Chinese explanation",
                "matched_interests": ["string"],
                "concerns": ["string"],
            },
            "summary": {
                "arxiv_id": "string",
                "paper_type": "observational|theory|simulation|method|catalog|review|instrumentation|machine learning|unknown",
                "topic_sentence": "string",
                "one_sentence_takeaway": "string",
                "why_matched": "string",
                "quick_takeaways": ["string"],
                "background": "string",
                "method_data": "string",
                "key_results": ["string"],
                "main_results": "string",
                "figure_guide": "string",
                "physical_picture": "string",
                "novelty_value": "string",
                "relevance_to_profile": "string",
                "limitations": "string",
                "recommended_reading": "string",
                "follow_up_questions": [],
                "read_priority": "low|medium|high|must_read",
                "suggested_tags": ["string"],
            },
        },
        "papers": [_recalled_payload(item) for item in recalled],
    }
    Path(output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def import_codex_summaries(
    profile: InterestProfile,
    triaged: list[TriagedPaper],
    input_path: str | Path,
    *,
    cache: SummaryCache | None = None,
) -> list[SummarizedPaper]:
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    summaries_by_id = {
        item["arxiv_id"]: PaperSummary.from_payload(item)
        for item in payload.get("summaries", [])
    }
    cache = cache or SummaryCache()
    result: list[SummarizedPaper] = []
    p_hash = profile_hash(profile)

    for item in triaged:
        arxiv_id = item.ranked.paper.arxiv_id
        if arxiv_id not in summaries_by_id:
            continue
        summary = summaries_by_id[arxiv_id]
        key = summary_cache_key(
            arxiv_id=arxiv_id,
            profile=profile,
            model=CODEX_SUMMARY_MODEL,
            prompt_version=SUMMARY_PROMPT_VERSION,
        )
        cache.put(
            key,
            arxiv_id=arxiv_id,
            profile_hash=p_hash,
            model=CODEX_SUMMARY_MODEL,
            prompt_version=SUMMARY_PROMPT_VERSION,
            payload=summary.to_payload(),
        )
        result.append(SummarizedPaper(triaged=item, summary=summary, cache_hit=False))
    return result


def import_codex_review_summaries(
    profile: InterestProfile,
    recalled: list[RankedPaper],
    input_path: str | Path,
    *,
    cache: SummaryCache | None = None,
) -> list[SummarizedPaper]:
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    items_by_id = {item["arxiv_id"]: item for item in payload.get("summaries", [])}
    ranked_by_id = {item.paper.arxiv_id: item for item in recalled}
    cache = cache or SummaryCache()
    p_hash = profile_hash(profile)
    result: list[SummarizedPaper] = []

    for arxiv_id, item in items_by_id.items():
        if arxiv_id not in ranked_by_id:
            continue
        triage_payload = item["triage"]
        summary = PaperSummary.from_payload(item["summary"])
        triaged = TriagedPaper(
            ranked=ranked_by_id[arxiv_id],
            decision=TriageDecision(
                arxiv_id=arxiv_id,
                action=triage_payload["action"],
                relevance_score=float(triage_payload["relevance_score"]),
                reason=triage_payload["reason"],
                matched_interests=tuple(triage_payload.get("matched_interests", [])),
                concerns=tuple(triage_payload.get("concerns", [])),
            ),
        )
        key = summary_cache_key(
            arxiv_id=arxiv_id,
            profile=profile,
            model=CODEX_SUMMARY_MODEL,
            prompt_version=SUMMARY_PROMPT_VERSION,
        )
        cache.put(
            key,
            arxiv_id=arxiv_id,
            profile_hash=p_hash,
            model=CODEX_SUMMARY_MODEL,
            prompt_version=SUMMARY_PROMPT_VERSION,
            payload=summary.to_payload(),
        )
        result.append(SummarizedPaper(triaged=triaged, summary=summary, cache_hit=False))
    result.sort(key=lambda item: (-item.triaged.decision.relevance_score, item.triaged.ranked.paper.arxiv_id))
    return result


def load_cached_codex_summaries(
    profile: InterestProfile,
    triaged: list[TriagedPaper],
    *,
    cache: SummaryCache | None = None,
) -> list[SummarizedPaper]:
    cache = cache or SummaryCache()
    result: list[SummarizedPaper] = []
    for item in triaged:
        arxiv_id = item.ranked.paper.arxiv_id
        key = summary_cache_key(
            arxiv_id=arxiv_id,
            profile=profile,
            model=CODEX_SUMMARY_MODEL,
            prompt_version=SUMMARY_PROMPT_VERSION,
        )
        payload = cache.get(key)
        if payload is not None:
            result.append(
                SummarizedPaper(
                    triaged=item,
                    summary=PaperSummary.from_payload(payload),
                    cache_hit=True,
                )
            )
    return result


def empty_codex_summary_file(output_path: str | Path) -> None:
    Path(output_path).write_text(
        json.dumps({"summaries": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _task_payload(item: TriagedPaper) -> dict[str, Any]:
    paper = item.ranked.paper
    decision = item.decision
    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "authors": paper.authors,
        "categories": list(paper.categories),
        "comments": paper.comments,
        "abstract": paper.abstract,
        "url": paper.url,
        "pdf_url": paper.url.replace("/abs/", "/pdf/"),
        "triage": {
            "action": decision.action,
            "relevance_score": decision.relevance_score,
            "reason": decision.reason,
            "matched_interests": list(decision.matched_interests),
            "concerns": list(decision.concerns),
        },
    }


def _recalled_payload(item: RankedPaper) -> dict[str, Any]:
    paper = item.paper
    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "authors": paper.authors,
        "categories": list(paper.categories),
        "comments": paper.comments,
        "abstract": paper.abstract,
        "url": paper.url,
        "pdf_url": paper.url.replace("/abs/", "/pdf/"),
        "recall": {
            "score": item.score,
            "reasons": list(item.reasons),
        },
    }
