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

    lines.extend(["今日入选文章", "==========", ""])
    for index, item in enumerate(summarized, start=1):
        triaged = item.triaged
        ranked = triaged.ranked
        decision = triaged.decision
        paper = ranked.paper
        summary = item.summary
        cache_note = "cache hit" if item.cache_hit else "new"
        paper_info = [
            f"标题: {paper.title}",
            f"arXiv: {paper.arxiv_id}",
            f"链接: {paper.url}",
            f"作者: {paper.authors}",
            f"领域: {', '.join(paper.categories)}",
            f"类型: {summary.paper_type}",
            f"一句话主题: {summary.topic_sentence}",
            f"阅读优先级: {summary.read_priority}",
            f"AI 判读: {decision.action}, relevance={decision.relevance_score:.2f}",
            f"总结来源: {cache_note}",
            f"匹配原因: {summary.why_matched}",
        ]
        if summary.suggested_tags:
            paper_info.append(f"标签: {', '.join(summary.suggested_tags)}")
        lines.extend(
            [
                f"{index}. {paper.title}",
                "-" * min(72, max(12, len(f"{index}. {paper.title}"))),
                "",
                "论文信息",
                "",
                *paper_info,
                "",
                "30 秒读懂",
                "",
            ]
        )
        _append_bullets(lines, summary.quick_takeaways or (summary.one_sentence_takeaway,))
        lines.extend(
            [
                "",
                "背景与科学问题",
                "",
                summary.background,
                "",
                "方法与技术路线",
                "",
                summary.method_data,
                "",
                "关键结果",
                "",
            ]
        )
        _append_bullets(lines, summary.key_results or (summary.main_results,))
        lines.extend(
            [
                "",
                "图表 / 全文阅读线索",
                "",
                summary.figure_guide,
                "",
                "物理图像 / 直觉解释",
                "",
                summary.physical_picture,
                "",
                "创新点与价值",
                "",
                summary.novelty_value,
                "",
                "局限、假设与潜在问题",
                "",
                summary.limitations,
                "",
                "和你研究的潜在关系",
                "",
                summary.relevance_to_profile,
                "",
                "建议精读位置",
                "",
                summary.recommended_reading,
                "",
            ]
        )
        lines.extend(
            [
                "",
                "英文摘要",
                "",
                paper.abstract,
                "",
                "",
            ]
        )
    return "\n".join(lines)


def _header(profile: InterestProfile, count: int) -> list[str]:
    lines = [
        f"{profile.name} arXiv 每日摘要",
        "=" * min(72, max(12, len(f"{profile.name} arXiv 每日摘要"))),
        "",
        f"收件人: {profile.recipient}",
        f"筛选结果: {count} 篇",
        "",
    ]
    if profile.summary_requirements:
        lines.extend(["用户要求", "", profile.summary_requirements.strip(), ""])
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


def _append_bullets(lines: list[str], items: tuple[str, ...]) -> None:
    if not items:
        lines.append("- 未说明。")
        return
    for item in items:
        lines.append(f"- {item}")
