from arxiv_digest.parser import ArxivPaper
from arxiv_digest.profiles import InterestProfile
from arxiv_digest.ranker import RankedPaper
from arxiv_digest.render import render_summarized_html_digest, render_summarized_markdown_digest
from arxiv_digest.summary import PaperSummary, SummarizedPaper
from arxiv_digest.triage import TriageDecision, TriagedPaper


def test_summarized_digest_is_plain_email_text():
    paper = ArxivPaper(
        arxiv_id="2606.26218",
        date="Fri, 26 Jun 2026",
        size="123kb",
        title="A Galactic Stream Test",
        authors="A. Author",
        categories=("astro-ph.GA",),
        abstract="We study a stellar stream.",
        url="https://arxiv.org/abs/2606.26218",
    )
    ranked = RankedPaper(paper=paper, score=9, reasons=("interest:stellar streams",))
    triaged = TriagedPaper(
        ranked=ranked,
        decision=TriageDecision(
            arxiv_id="2606.26218",
            action="full_read",
            relevance_score=0.92,
            reason="matches",
            matched_interests=("stellar streams",),
        ),
    )
    summary = PaperSummary(
        arxiv_id="2606.26218",
        paper_type="观测",
        topic_sentence="研究银河系星流。",
        one_sentence_takeaway="这是一篇星流论文。",
        why_matched="符合星流兴趣。",
        quick_takeaways=("要点一", "要点二"),
        background="背景",
        method_data="方法",
        key_results=("结果一",),
        main_results="主要结果",
        figure_guide="图表线索",
        physical_picture="物理图像",
        novelty_value="价值",
        relevance_to_profile="关系",
        limitations="局限",
        recommended_reading="读方法和结果。",
        follow_up_questions=("不应出现在邮件里",),
        read_priority="must_read",
        suggested_tags=("stellar streams",),
    )

    body = render_summarized_markdown_digest(
        InterestProfile(name="user@example.com", recipient="user@example.com"),
        [SummarizedPaper(triaged=triaged, summary=summary)],
    )

    assert "# " not in body
    assert "**" not in body
    assert "<details>" not in body
    assert "[2606.26218]" not in body
    assert "可继续追问" not in body
    assert "不应出现在邮件里" not in body
    assert "链接: https://arxiv.org/abs/2606.26218" in body


def test_summarized_digest_has_html_email_formatting():
    paper = ArxivPaper(
        arxiv_id="2606.26218",
        date="Fri, 26 Jun 2026",
        size="123kb",
        title="A <Galactic> Stream Test",
        authors="A. Author",
        categories=("astro-ph.GA",),
        abstract="We study a stellar stream.",
        url="https://arxiv.org/abs/2606.26218",
    )
    ranked = RankedPaper(paper=paper, score=9, reasons=("interest:stellar streams",))
    triaged = TriagedPaper(
        ranked=ranked,
        decision=TriageDecision(
            arxiv_id="2606.26218",
            action="full_read",
            relevance_score=0.92,
            reason="matches",
            matched_interests=("stellar streams",),
        ),
    )
    summary = PaperSummary(
        arxiv_id="2606.26218",
        paper_type="观测",
        topic_sentence="研究银河系星流。",
        one_sentence_takeaway="这是一篇星流论文。",
        why_matched="符合星流兴趣。",
        quick_takeaways=("要点一", "要点二"),
        background="背景",
        method_data="方法",
        key_results=("结果一",),
        main_results="主要结果",
        figure_guide="图表线索",
        physical_picture="物理图像",
        novelty_value="价值",
        relevance_to_profile="关系",
        limitations="局限",
        recommended_reading="读方法和结果。",
        follow_up_questions=("不应出现在邮件里",),
        read_priority="must_read",
        suggested_tags=("stellar streams",),
    )

    body = render_summarized_html_digest(
        InterestProfile(name="user@example.com", recipient="user@example.com"),
        [SummarizedPaper(triaged=triaged, summary=summary)],
    )

    assert "<h1" in body
    assert "<h2" in body
    assert "<strong>收件人：" in body
    assert "<ul" in body
    assert '<a href="https://arxiv.org/abs/2606.26218">2606.26218</a>' in body
    assert "A &lt;Galactic&gt; Stream Test" in body
    assert "###" not in body
    assert "**" not in body
    assert "可继续追问" not in body
    assert "不应出现在邮件里" not in body
