from arxiv_digest.ranker import _keyword_matches


def test_keyword_matching_uses_word_boundaries():
    text = "this extragalactic survey was designed for galaxies"

    assert not _keyword_matches(text, "Galactic")
    assert not _keyword_matches(text, "DESI")
    assert _keyword_matches(text, "galaxy")
