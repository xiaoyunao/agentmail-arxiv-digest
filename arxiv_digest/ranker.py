from __future__ import annotations

from dataclasses import dataclass
import re

from .parser import ArxivPaper
from .profiles import InterestProfile


@dataclass(frozen=True)
class RankedPaper:
    paper: ArxivPaper
    score: int
    reasons: tuple[str, ...]


def rank_papers(papers: list[ArxivPaper], profile: InterestProfile) -> list[RankedPaper]:
    ranked: list[RankedPaper] = []
    include_categories = set(profile.include_categories)

    for paper in papers:
        text = paper.text_for_matching
        if include_categories and not include_categories.intersection(paper.categories):
            continue
        if any(_keyword_matches(text, keyword) for keyword in profile.exclude_keywords):
            continue

        score = 0
        reasons: list[str] = []

        for keyword in profile.must_keywords:
            if _keyword_matches(text, keyword):
                score += 3
                reasons.append(f"must:{keyword}")

        for keyword in profile.boost_keywords:
            if _keyword_matches(text, keyword):
                score += 1
                reasons.append(f"boost:{keyword}")

        if score >= profile.min_score:
            ranked.append(RankedPaper(paper=paper, score=score, reasons=tuple(reasons)))

    ranked.sort(key=lambda item: (-item.score, item.paper.arxiv_id))
    return ranked[: profile.max_papers]


def _keyword_matches(text: str, keyword: str) -> bool:
    normalized = keyword.strip().lower()
    if not normalized:
        return False
    pattern = re.escape(normalized)
    if re.fullmatch(r"[a-z0-9][a-z0-9\-\s]*", normalized):
        pattern = _keyword_plural_pattern(normalized)
        return re.search(pattern, text) is not None
    return normalized in text


def _keyword_plural_pattern(keyword: str) -> str:
    parts = keyword.split()
    last = parts[-1]
    if last.endswith("y") and len(last) > 1:
        parts[-1] = re.escape(last[:-1]) + r"(?:y|ies)"
    else:
        parts[-1] = re.escape(last) + "s?"
    pattern = r"\s+".join(re.escape(part) for part in parts[:-1] + [parts[-1]])
    pattern = pattern.replace(re.escape(parts[-1]), parts[-1])
    return rf"(?<![a-z0-9]){pattern}(?![a-z0-9])"
