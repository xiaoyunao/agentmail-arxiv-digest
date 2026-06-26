from __future__ import annotations

from .profiles import InterestProfile
from .ranker import RankedPaper
from .summary import SummarizedPaper
from .triage import TriagedPaper


def render_markdown_digest(profile: InterestProfile, ranked: list[RankedPaper]) -> str:
    lines = _header(profile, len(ranked))
    if not ranked:
        lines.extend(["今天没有匹配该兴趣配置的文章。", ""])
        return "\n".join(lines)

    lines.extend(["## 候选文章", ""])
    for item in ranked:
        paper = item.paper
        lines.extend(
            [
                f"### {paper.title}",
                "",
                f"- arXiv: [{paper.arxiv_id}]({paper.url})",
                f"- Categories: {', '.join(paper.categories)}",
                f"- Authors: {paper.authors}",
                f"- Recall score: {item.score} ({', '.join(item.reasons)})",
            ]
        )
        _append_paper_body(lines, paper.abstract)
    return "\n".join(lines)


def render_triaged_markdown_digest(profile: InterestProfile, triaged: list[TriagedPaper]) -> str:
    lines = _header(profile, len(triaged))
    if not triaged:
        lines.extend(["今天没有匹配该兴趣配置的文章。", ""])
        return "\n".join(lines)

    lines.extend(["## AI 判读候选文章", ""])
    for item in triaged:
        ranked = item.ranked
        decision = item.decision
        paper = ranked.paper
        lines.extend(
            [
                f"### {paper.title}",
                "",
                f"- arXiv: [{paper.arxiv_id}]({paper.url})",
                f"- Categories: {', '.join(paper.categories)}",
                f"- Authors: {paper.authors}",
                f"- Recall score: {ranked.score} ({', '.join(ranked.reasons)})",
                f"- AI triage: {decision.action}, relevance={decision.relevance_score:.2f}",
                f"- Triage reason: {decision.reason}",
            ]
        )
        if decision.matched_interests:
            lines.append(f"- Matched interests: {', '.join(decision.matched_interests)}")
        if decision.concerns:
            lines.append(f"- Concerns: {', '.join(decision.concerns)}")
        _append_paper_body(lines, paper.abstract)
    return "\n".join(lines)


def render_summarized_markdown_digest(profile: InterestProfile, summarized: list[SummarizedPaper]) -> str:
    lines = _header(profile, len(summarized))
    if not summarized:
        lines.extend(["今天没有匹配该兴趣配置的文章。", ""])
        return "\n".join(lines)

    lines.extend(["## 精读总结", ""])
    for item in summarized:
        triaged = item.triaged
        ranked = triaged.ranked
        decision = triaged.decision
        paper = ranked.paper
        summary = item.summary
        cache_note = "cache hit" if item.cache_hit else "new"
        lines.extend(
            [
                f"### {paper.title}",
                "",
                f"- arXiv: [{paper.arxiv_id}]({paper.url})",
                f"- Categories: {', '.join(paper.categories)}",
                f"- Authors: {paper.authors}",
                f"- AI triage: {decision.action}, relevance={decision.relevance_score:.2f}",
                f"- Read priority: {summary.read_priority}",
                f"- Summary source: {cache_note}",
            ]
        )
        if summary.suggested_tags:
            lines.append(f"- Tags: {', '.join(summary.suggested_tags)}")
        lines.extend(
            [
                "",
                f"**一句话结论**：{summary.one_sentence_takeaway}",
                "",
                f"**为什么匹配**：{summary.why_matched}",
                "",
                "**背景与问题**",
                "",
                summary.background,
                "",
                "**数据与方法**",
                "",
                summary.method_data,
                "",
                "**主要结果**",
                "",
                summary.main_results,
                "",
                "**和用户方向的关系**",
                "",
                summary.relevance_to_profile,
                "",
                "**局限与注意事项**",
                "",
                summary.limitations,
                "",
            ]
        )
    return "\n".join(lines)


def _header(profile: InterestProfile, count: int) -> list[str]:
    lines = [
        f"# {profile.name} arXiv 每日摘要",
        "",
        f"收件人: {profile.recipient}",
        f"筛选结果: {count} 篇",
        "",
    ]
    if profile.summary_requirements:
        lines.extend(["## 用户要求", "", profile.summary_requirements.strip(), ""])
    return lines


def _append_paper_body(lines: list[str], abstract: str) -> None:
    lines.extend(
        [
            "",
            "英文摘要:",
            "",
            abstract,
            "",
            "中文详解占位:",
            "",
            "- 这里后续由 Codex 生成：背景、方法、数据、主要结果、与银河系/星流/矮星系的关系、值得精读的理由。",
            "",
        ]
    )
