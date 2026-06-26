from __future__ import annotations

import json
from pathlib import Path
import re

from .profiles import InterestProfile

DEFAULT_SUBSCRIBER_DIR = "subscribers"
SUBSCRIBE_SUBJECT = "Subscribe to dailyarxiv"
DEFAULT_ASTROPH_CATEGORIES = (
    "astro-ph.GA",
    "astro-ph.CO",
    "astro-ph.EP",
    "astro-ph.HE",
    "astro-ph.IM",
    "astro-ph.SR",
)


def parse_subscription_request(body: str, sender_email: str) -> InterestProfile:
    recipient = sender_email.strip()
    if not recipient:
        raise ValueError("subscription request is missing sender email")
    terms = _parse_semicolon_terms(body)
    if not terms:
        raise ValueError("subscription request body must contain at least one semicolon-separated interest term")
    summary_requirements = (
        "只根据这些兴趣线索筛选 astro-ph daily："
        + "; ".join(terms)
        + "。先宽松召回，再由 Codex 判断语义相关性；入选文章用中文科研笔记格式总结。"
    )
    return InterestProfile(
        name=recipient,
        recipient=recipient,
        language="zh",
        include_categories=DEFAULT_ASTROPH_CATEGORIES,
        research_interests=tuple(terms),
        boost_keywords=tuple(terms),
        favorite_authors=tuple(terms),
        max_papers=8,
        min_score=1,
        recall_limit=50,
        ai_triage_threshold=0.65,
        summary_requirements=summary_requirements,
        metadata={"source": "email-subscription", "format": "semicolon-v1"},
    )


def save_profile(profile: InterestProfile, directory: str | Path = DEFAULT_SUBSCRIBER_DIR) -> Path:
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{_safe_profile_name(profile.recipient)}.json"
    payload = {
        "name": profile.name,
        "recipient": profile.recipient,
        "language": profile.language,
        "include_categories": list(profile.include_categories),
        "research_interests": list(profile.research_interests),
        "must_keywords": list(profile.must_keywords),
        "boost_keywords": list(profile.boost_keywords),
        "exclude_keywords": list(profile.exclude_keywords),
        "favorite_authors": list(profile.favorite_authors),
        "max_papers": profile.max_papers,
        "min_score": profile.min_score,
        "recall_limit": profile.recall_limit,
        "ai_triage_threshold": profile.ai_triage_threshold,
        "summary_requirements": profile.summary_requirements,
        "metadata": profile.metadata,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_profiles(directory: str | Path = DEFAULT_SUBSCRIBER_DIR) -> list[InterestProfile]:
    root = Path(directory)
    if not root.exists():
        return []
    return [InterestProfile.from_json_file(path) for path in sorted(root.glob("*.json"))]


def is_subscription_subject(subject: str) -> bool:
    return subject.strip().casefold() == SUBSCRIBE_SUBJECT.casefold()


def _parse_semicolon_terms(body: str) -> list[str]:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    raw_terms = re.split(r"[;\n]+", normalized)
    terms: list[str] = []
    seen: set[str] = set()
    for raw_term in raw_terms:
        term = re.sub(r"\s+", " ", raw_term.strip())
        if not term:
            continue
        key = term.casefold()
        if key in seen:
            continue
        seen.add(key)
        terms.append(term)
    return terms


def _safe_profile_name(email: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", email)
