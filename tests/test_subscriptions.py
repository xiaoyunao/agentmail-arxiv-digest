from arxiv_digest.subscriptions import parse_subscription_request


def test_parse_subscription_request_with_lists():
    body = """
name: Galactic digest
categories:
  - astro-ph.GA
research_interests:
  - stellar streams
  - dwarf galaxies
favorite_authors:
  - Ting S. Li
max_papers: 5
summary_requirements: 详细中文总结
"""

    profile = parse_subscription_request(body, "user@example.com")

    assert profile.recipient == "user@example.com"
    assert profile.name == "Galactic digest"
    assert profile.research_interests == ("stellar streams", "dwarf galaxies")
    assert profile.favorite_authors == ("Ting S. Li",)
    assert profile.max_papers == 5
