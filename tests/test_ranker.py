from arxiv_digest.ranker import _keyword_matches
from arxiv_digest.triage import parse_triage_decision


def test_keyword_matching_uses_word_boundaries():
    text = "this extragalactic survey was designed for galaxies"

    assert not _keyword_matches(text, "Galactic")
    assert not _keyword_matches(text, "DESI")
    assert _keyword_matches(text, "galaxy")


def test_parse_triage_decision_validates_paper_id():
    raw = """{
      "arxiv_id": "2606.26218",
      "action": "full_read",
      "relevance_score": 0.91,
      "reason": "矮星系和暗物质动力学高度相关",
      "matched_interests": ["dwarf galaxies"],
      "concerns": []
    }"""

    decision = parse_triage_decision(raw, "2606.26218")

    assert decision.should_summarize
    assert decision.action == "full_read"
