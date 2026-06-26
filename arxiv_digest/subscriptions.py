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


def subscription_receipt_subject() -> str:
    return "dailyarxiv 订阅成功"


def render_subscription_receipt(profile: InterestProfile) -> str:
    interests = "; ".join(profile.research_interests)
    return f"""你的 dailyarxiv 订阅已经生效。

订阅邮箱：{profile.recipient}
订阅方向：{interests}

之后工作日如收到 arXiv astro-ph daily，系统会按你的方向筛选文章，并发送中文科研笔记式总结。

修改订阅：
请继续用这个邮箱发送邮件到 dailyarxiv@agent.qq.com。
标题固定写：
Subscribe to dailyarxiv

正文用英文分号分隔方向、关键词、固定对象或作者名，例如：
dark matter; little red dot; yunao xiao; stellar streams; dwarf galaxies

说明：
- 发件人邮箱就是接收日报的邮箱。
- 关键词只是召回线索，最终会由 Codex 根据论文题目、作者、分类和摘要判断是否真正相关。
- 如果当天 arXiv 没有发送 astro-ph daily，或者没有匹配文章，就不会强行生成无内容总结。
"""


def save_profile(profile: InterestProfile, directory: str | Path = DEFAULT_SUBSCRIBER_DIR) -> Path:
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = profile_path(profile.recipient, target_dir)
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


def profile_path(email: str, directory: str | Path = DEFAULT_SUBSCRIBER_DIR) -> Path:
    return Path(directory) / f"{_safe_profile_name(email)}.json"


def should_send_subscription_receipt(profile: InterestProfile, directory: str | Path = DEFAULT_SUBSCRIBER_DIR) -> bool:
    path = profile_path(profile.recipient, directory)
    if not path.exists():
        return True
    existing = InterestProfile.from_json_file(path)
    return (
        existing.research_interests != profile.research_interests
        or existing.include_categories != profile.include_categories
        or existing.summary_requirements != profile.summary_requirements
    )


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
