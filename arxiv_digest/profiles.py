from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass(frozen=True)
class InterestProfile:
    name: str
    recipient: str
    language: str = "zh"
    include_categories: tuple[str, ...] = ("astro-ph.GA",)
    research_interests: tuple[str, ...] = ()
    must_keywords: tuple[str, ...] = ()
    boost_keywords: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    favorite_authors: tuple[str, ...] = ()
    max_papers: int = 8
    min_score: int = 1
    recall_limit: int = 40
    ai_triage_threshold: float = 0.65
    summary_requirements: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_json_file(cls, path: str | Path) -> "InterestProfile":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            name=data["name"],
            recipient=data["recipient"],
            language=data.get("language", "zh"),
            include_categories=tuple(data.get("include_categories", ["astro-ph.GA"])),
            research_interests=tuple(data.get("research_interests", [])),
            must_keywords=tuple(data.get("must_keywords", [])),
            boost_keywords=tuple(data.get("boost_keywords", [])),
            exclude_keywords=tuple(data.get("exclude_keywords", [])),
            favorite_authors=tuple(data.get("favorite_authors", [])),
            max_papers=int(data.get("max_papers", 8)),
            min_score=int(data.get("min_score", 1)),
            recall_limit=int(data.get("recall_limit", 40)),
            ai_triage_threshold=float(data.get("ai_triage_threshold", 0.65)),
            summary_requirements=data.get("summary_requirements", ""),
            metadata=data.get("metadata", {}),
        )
