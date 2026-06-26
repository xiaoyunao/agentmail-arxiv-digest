from arxiv_digest.parser import parse_daily_email


SAMPLE = r"""
------------------------------------------------------------------------------
\\
arXiv:2606.26218
Date: Wed, 24 Jun 2026 18:00:00 GMT   (4487kb)

Title: Dark Matter in Draco and Bo\"otes I: Hints of a Core in an Ultra-Faint
  Dwarf from Simulation-Based Inference
Authors: Tri Nguyen, Lina Necib, Ting S. Li
Categories: astro-ph.GA astro-ph.HE
Comments: 33 + 8 pages, 13 + 8 figures, 5 tables, submitted to MNRAS
\\
  The density profiles of dwarf spheroidal galaxies are among the most
sensitive probes of dark matter physics, yet extracting them from noisy
stellar kinematics remains a fundamental obstacle.
\\ ( https://arxiv.org/abs/2606.26218 ,  4487kb)
------------------------------------------------------------------------------
"""


def test_parse_daily_email_extracts_wrapped_fields():
    papers = parse_daily_email(SAMPLE)

    assert len(papers) == 1
    paper = papers[0]
    assert paper.arxiv_id == "2606.26218"
    assert paper.title.startswith("Dark Matter in Draco")
    assert "Ultra-Faint Dwarf" in paper.title
    assert paper.authors == "Tri Nguyen, Lina Necib, Ting S. Li"
    assert paper.categories == ("astro-ph.GA", "astro-ph.HE")
    assert paper.url == "https://arxiv.org/abs/2606.26218"
    assert "dwarf spheroidal galaxies" in paper.abstract
