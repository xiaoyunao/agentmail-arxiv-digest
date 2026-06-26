from arxiv_digest.cache import SummaryCache, summary_cache_key
from arxiv_digest.mail import _loads_json_with_tips
from arxiv_digest.profiles import InterestProfile
from arxiv_digest.summary import parse_paper_summary


def test_summary_cache_round_trip(tmp_path):
    profile = InterestProfile(name="test", recipient="user@example.com")
    cache = SummaryCache(tmp_path / "cache.sqlite3")
    key = summary_cache_key(
        arxiv_id="2606.26218",
        profile=profile,
        model="codex",
        prompt_version="summary-v1",
    )
    payload = {
        "arxiv_id": "2606.26218",
        "one_sentence_takeaway": "一句话",
        "why_matched": "匹配",
        "background": "背景",
        "method_data": "方法",
        "main_results": "结果",
        "relevance_to_profile": "关系",
        "limitations": "局限",
        "read_priority": "high",
        "suggested_tags": ["dwarf"],
    }

    cache.put(
        key,
        arxiv_id="2606.26218",
        profile_hash="abc",
        model="codex",
        prompt_version="summary-v1",
        payload=payload,
    )

    assert cache.get(key) == payload


def test_parse_paper_summary_validates_id():
    summary = parse_paper_summary(
        """{
          "arxiv_id": "2606.26218",
          "one_sentence_takeaway": "一句话",
          "why_matched": "匹配",
          "background": "背景",
          "method_data": "方法",
          "main_results": "结果",
          "relevance_to_profile": "关系",
          "limitations": "局限",
          "read_priority": "high",
          "suggested_tags": ["dwarf"]
        }""",
        "2606.26218",
    )

    assert summary.read_priority == "high"


def test_loads_json_with_tips_ignores_tip_lines():
    parsed = _loads_json_with_tips('tip: hello\n{"ok": true, "data": {"x": 1}}\ntip: bye')

    assert parsed["data"]["x"] == 1
