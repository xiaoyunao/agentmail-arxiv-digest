from __future__ import annotations

import html

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


def render_summarized_html_digest(profile: InterestProfile, summarized: list[SummarizedPaper]) -> str:
    title = f"{profile.name} arXiv 每日摘要"
    parts = [
        "<!doctype html>",
        "<html>",
        "<body style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; color:#111; line-height:1.58; max-width:900px; margin:0 auto; padding:20px;\">",
        f"<h1 style=\"font-size:24px; margin:0 0 12px;\">{_e(title)}</h1>",
        f"<p style=\"margin:0 0 18px;\"><strong>收件人：</strong>{_e(profile.recipient)}<br><strong>筛选结果：</strong>{len(summarized)} 篇</p>",
    ]
    if profile.summary_requirements:
        parts.extend(
            [
                "<h2 style=\"font-size:18px; margin:24px 0 8px;\">用户要求</h2>",
                f"<p>{_e(profile.summary_requirements.strip())}</p>",
            ]
        )
    if not summarized:
        parts.append("<p>今天没有匹配该兴趣配置的文章。</p>")
        parts.extend(["</body>", "</html>"])
        return "\n".join(parts)

    parts.append("<h2 style=\"font-size:20px; margin:28px 0 12px;\">今日入选文章</h2>")
    for index, item in enumerate(summarized, start=1):
        triaged = item.triaged
        ranked = triaged.ranked
        decision = triaged.decision
        paper = ranked.paper
        summary = item.summary
        cache_note = "cache hit" if item.cache_hit else "new"
        parts.extend(
            [
                "<article style=\"border-top:1px solid #ddd; padding-top:18px; margin-top:22px;\">",
                f"<h2 style=\"font-size:19px; margin:0 0 10px;\">{index}. {_e(paper.title)}</h2>",
                "<table style=\"border-collapse:collapse; margin:8px 0 18px; width:100%;\">",
                _info_row("标题", paper.title),
                _info_row("arXiv", f'<a href="{_attr(paper.url)}">{_e(paper.arxiv_id)}</a>', raw_value=True),
                _info_row("作者", paper.authors),
                _info_row("领域", ", ".join(paper.categories)),
                _info_row("类型", summary.paper_type),
                _info_row("一句话主题", summary.topic_sentence),
                _info_row("阅读优先级", summary.read_priority),
                _info_row("AI 判读", f"{decision.action}, relevance={decision.relevance_score:.2f}"),
                _info_row("总结来源", cache_note),
                _info_row("匹配原因", summary.why_matched),
            ]
        )
        if summary.suggested_tags:
            parts.append(_info_row("标签", ", ".join(summary.suggested_tags)))
        parts.extend(
            [
                "</table>",
                _section("30 秒读懂", _html_bullets(summary.quick_takeaways or (summary.one_sentence_takeaway,))),
                _section("背景与科学问题", _paragraph(summary.background)),
                _section("方法与技术路线", _paragraph(summary.method_data)),
                _section("关键结果", _html_bullets(summary.key_results or (summary.main_results,))),
                _section("图表 / 全文阅读线索", _paragraph(summary.figure_guide)),
                _section("物理图像 / 直觉解释", _paragraph(summary.physical_picture)),
                _section("创新点与价值", _paragraph(summary.novelty_value)),
                _section("局限、假设与潜在问题", _paragraph(summary.limitations)),
                _section("和你研究的潜在关系", _paragraph(summary.relevance_to_profile)),
                _section("建议精读位置", _paragraph(summary.recommended_reading)),
                _section("英文摘要", _paragraph(paper.abstract)),
                "</article>",
            ]
        )
    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)


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


def _e(value: str) -> str:
    return html.escape(value, quote=False)


def _attr(value: str) -> str:
    return html.escape(value, quote=True)


def _info_row(label: str, value: str, *, raw_value: bool = False) -> str:
    rendered_value = value if raw_value else _e(value)
    return (
        "<tr>"
        f"<th style=\"text-align:left; vertical-align:top; width:110px; padding:4px 10px 4px 0; color:#555;\">{_e(label)}</th>"
        f"<td style=\"padding:4px 0;\">{rendered_value}</td>"
        "</tr>"
    )


def _section(title: str, body: str) -> str:
    return f"<h3 style=\"font-size:16px; margin:18px 0 6px;\">{_e(title)}</h3>{body}"


def _paragraph(value: str) -> str:
    return f"<p style=\"margin:0 0 10px;\">{_e(value)}</p>"


def _html_bullets(items: tuple[str, ...]) -> str:
    if not items:
        items = ("未说明。",)
    rendered = "\n".join(f"<li>{_e(item)}</li>" for item in items)
    return f"<ul style=\"margin:0 0 10px 20px; padding:0;\">{rendered}</ul>"
