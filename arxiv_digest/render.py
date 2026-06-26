from __future__ import annotations

from .profiles import InterestProfile
from .ranker import RankedPaper


def render_markdown_digest(profile: InterestProfile, ranked: list[RankedPaper]) -> str:
    lines = [
        f"# {profile.name} arXiv 每日摘要",
        "",
        f"收件人: {profile.recipient}",
        f"筛选结果: {len(ranked)} 篇",
        "",
    ]

    if profile.summary_requirements:
        lines.extend(["## 用户要求", "", profile.summary_requirements.strip(), ""])

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
                f"- Score: {item.score} ({', '.join(item.reasons)})",
                "",
                "英文摘要:",
                "",
                paper.abstract,
                "",
                "中文详解占位:",
                "",
                "- 这里后续由 GPT API 生成：背景、方法、数据、主要结果、与银河系/星流/矮星系的关系、值得精读的理由。",
                "",
            ]
        )
    return "\n".join(lines)
