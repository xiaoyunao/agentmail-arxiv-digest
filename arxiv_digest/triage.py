from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Literal

from .profiles import InterestProfile
from .ranker import RankedPaper

TriageAction = Literal["skip", "short", "full_read"]


@dataclass(frozen=True)
class TriageDecision:
    arxiv_id: str
    action: TriageAction
    relevance_score: float
    reason: str
    matched_interests: tuple[str, ...]
    concerns: tuple[str, ...] = ()

    @property
    def should_summarize(self) -> bool:
        return self.action in {"short", "full_read"}


@dataclass(frozen=True)
class TriagedPaper:
    ranked: RankedPaper
    decision: TriageDecision


TRIAGE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "arxiv_id": {"type": "string"},
        "action": {"type": "string", "enum": ["skip", "short", "full_read"]},
        "relevance_score": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
        "matched_interests": {"type": "array", "items": {"type": "string"}},
        "concerns": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "arxiv_id",
        "action",
        "relevance_score",
        "reason",
        "matched_interests",
        "concerns",
    ],
}


def build_triage_prompt(profile: InterestProfile, ranked: RankedPaper) -> str:
    paper = ranked.paper
    return f"""你是天文学论文订阅系统的相关性判读器。你的任务不是总结论文，而是判断这篇 arXiv 文章是否值得交给后续模型精读并为该用户生成中文总结。

判读原则：
- 用户给出的关键词、作者名、兴趣点只是线索，不是死板规则。
- 如果文章没有显式关键词，但科学问题、样本、方法或对象明显符合用户兴趣，也应该推荐。
- 如果只是泛泛出现词语，比如 galactic scales、halo model、survey design，但不符合用户真正方向，应跳过。
- 对用户特别关注方向相关的文章，倾向于 full_read。
- 对边缘相关但可能有参考价值的文章，选择 short。
- 对不相关文章，选择 skip。

用户 profile:
- 名称: {profile.name}
- 语言: {profile.language}
- arXiv 分类范围: {", ".join(profile.include_categories)}
- 研究兴趣: {", ".join(profile.research_interests) or "未填写"}
- 关键词线索: {", ".join(profile.must_keywords + profile.boost_keywords) or "未填写"}
- 关注作者: {", ".join(profile.favorite_authors) or "未填写"}
- 排除线索: {", ".join(profile.exclude_keywords) or "未填写"}
- 详细要求: {profile.summary_requirements or "未填写"}

规则召回信号:
- score: {ranked.score}
- reasons: {", ".join(ranked.reasons) or "none"}

论文:
- arXiv: {paper.arxiv_id}
- Title: {paper.title}
- Authors: {paper.authors}
- Categories: {", ".join(paper.categories)}
- Comments: {paper.comments or "none"}
- Abstract: {paper.abstract}
- URL: {paper.url}

只输出 JSON，字段必须符合：
{{
  "arxiv_id": "{paper.arxiv_id}",
  "action": "skip|short|full_read",
  "relevance_score": 0.0,
  "reason": "用中文简短解释为什么适合或不适合",
  "matched_interests": ["匹配到的真实兴趣点"],
  "concerns": ["不确定性或边缘原因"]
}}
"""


def parse_triage_decision(raw_json: str, expected_arxiv_id: str) -> TriageDecision:
    data = json.loads(raw_json)
    action = data["action"]
    if action not in {"skip", "short", "full_read"}:
        raise ValueError(f"invalid triage action: {action}")
    if data["arxiv_id"] != expected_arxiv_id:
        raise ValueError(f"triage arxiv_id mismatch: {data['arxiv_id']} != {expected_arxiv_id}")
    return TriageDecision(
        arxiv_id=data["arxiv_id"],
        action=action,
        relevance_score=float(data["relevance_score"]),
        reason=data["reason"],
        matched_interests=tuple(data.get("matched_interests", [])),
        concerns=tuple(data.get("concerns", [])),
    )


def heuristic_triage(profile: InterestProfile, ranked: RankedPaper) -> TriageDecision:
    """Deterministic fallback for local tests and runs without an API key."""
    if ranked.score >= max(profile.min_score * 2, 6):
        action: TriageAction = "full_read"
        relevance = 0.8
    elif ranked.score >= profile.min_score:
        action = "short"
        relevance = 0.6
    else:
        action = "skip"
        relevance = 0.25

    return TriageDecision(
        arxiv_id=ranked.paper.arxiv_id,
        action=action,
        relevance_score=relevance,
        reason="本地启发式判读：基于规则召回分数和匹配信号，供未配置 GPT API 时测试流程。",
        matched_interests=ranked.reasons,
    )


def select_triaged(profile: InterestProfile, triaged: list[TriagedPaper]) -> list[TriagedPaper]:
    selected = [
        item for item in triaged
        if item.decision.should_summarize and item.decision.relevance_score >= profile.ai_triage_threshold
    ]
    selected.sort(key=lambda item: (-item.decision.relevance_score, -item.ranked.score, item.ranked.paper.arxiv_id))
    return selected[: profile.max_papers]


def triage_with_heuristics(profile: InterestProfile, ranked: list[RankedPaper]) -> list[TriagedPaper]:
    return select_triaged(
        profile,
        [TriagedPaper(item, heuristic_triage(profile, item)) for item in ranked],
    )
