from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .profiles import InterestProfile

DEFAULT_SUBSCRIBER_DIR = "subscribers"


def parse_subscription_request(body: str, sender_email: str) -> InterestProfile:
    data = _parse_simple_profile(body)
    recipient = str(data.get("email") or sender_email).strip()
    name = str(data.get("name") or recipient).strip()
    return InterestProfile(
        name=name,
        recipient=recipient,
        language=str(data.get("language", "zh")),
        include_categories=tuple(data.get("categories", ["astro-ph.GA"])),
        research_interests=tuple(data.get("research_interests", [])),
        must_keywords=tuple(data.get("must_keywords", [])),
        boost_keywords=tuple(data.get("boost_keywords", [])),
        exclude_keywords=tuple(data.get("exclude_keywords", [])),
        favorite_authors=tuple(data.get("favorite_authors", [])),
        max_papers=int(data.get("max_papers", 8)),
        min_score=int(data.get("min_score", 1)),
        recall_limit=int(data.get("recall_limit", 40)),
        ai_triage_threshold=float(data.get("ai_triage_threshold", 0.65)),
        summary_requirements=str(data.get("summary_requirements", "")),
        metadata={"source": "email-subscription"},
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


def _parse_simple_profile(body: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_key:
            data.setdefault(current_key, []).append(stripped[2:].strip())
            continue
        if ":" not in line:
            if current_key == "summary_requirements":
                data[current_key] = f"{data.get(current_key, '')}\n{stripped}".strip()
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        elif key in {"max_papers", "min_score", "recall_limit"}:
            data[key] = int(value)
        elif key == "ai_triage_threshold":
            data[key] = float(value)
        elif key == "summary_requirements":
            data[key] = value
        else:
            data[key] = value
    return data


def _safe_profile_name(email: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", email)
