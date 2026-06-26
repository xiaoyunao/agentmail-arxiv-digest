from __future__ import annotations

import json
import html
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
        + "。先宽松召回，再由 Codex 判断语义相关性；入选文章阅读全文后用中文科研笔记格式总结。"
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
dark matter; little red dot; stellar streams; dwarf galaxies

说明：
- 发件人邮箱就是接收日报的邮箱。
- 关键词只是召回线索，最终由 Codex 判断语义相关性。
- 无 arXiv daily 或无匹配文章时，当日不发空报告。
"""


def render_subscription_receipt_html(profile: InterestProfile) -> str:
    interests = "; ".join(profile.research_interests)
    escaped_interests = html.escape(interests)
    escaped_recipient = html.escape(profile.recipient)
    return f"""<!doctype html>
<html>
  <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; color:#111; line-height:1.55;">
    <h2 style="margin:0 0 16px;">dailyarxiv 订阅成功</h2>
    <p>你的 dailyarxiv 订阅已经生效。</p>
    <p>
      <strong>订阅邮箱：</strong>{escaped_recipient}<br>
      <strong>订阅方向：</strong>{escaped_interests}
    </p>
    <p>之后工作日如收到 arXiv astro-ph daily，系统会按你的方向筛选文章，并发送中文科研笔记式总结。</p>
    <h3>修改订阅</h3>
    <p>请继续用这个邮箱发送邮件到 <strong>dailyarxiv@agent.qq.com</strong>。</p>
    <p>
      <strong>标题：</strong>Subscribe to dailyarxiv<br>
      <strong>正文：</strong>用英文分号分隔方向、关键词、固定对象或作者名
    </p>
    <pre style="background:#f6f8fa; padding:12px; border-radius:6px; white-space:pre-wrap;">dark matter; little red dot; stellar streams; dwarf galaxies</pre>
    <ul>
      <li>发件人邮箱就是接收日报的邮箱。</li>
      <li>关键词只是召回线索，最终由 Codex 判断语义相关性。</li>
      <li>无 arXiv daily 或无匹配文章时，当日不发空报告。</li>
    </ul>
  </body>
</html>
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
    normalized = re.sub(r"<br\s*/?>", "\n", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"<[^>]+>", "", normalized)
    normalized = html.unescape(normalized).replace("\xa0", " ")
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
