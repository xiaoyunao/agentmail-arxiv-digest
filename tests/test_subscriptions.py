from arxiv_digest.subscriptions import (
    DEFAULT_ASTROPH_CATEGORIES,
    SUBSCRIBE_SUBJECT,
    is_subscription_subject,
    parse_subscription_request,
    render_subscription_receipt,
    subscription_receipt_subject,
)


def test_parse_subscription_request_with_semicolon_terms():
    body = "dark matter; little red dot; yunao xiao; dark matter"

    profile = parse_subscription_request(body, "user@example.com")

    assert profile.recipient == "user@example.com"
    assert profile.name == "user@example.com"
    assert profile.include_categories == DEFAULT_ASTROPH_CATEGORIES
    assert profile.research_interests == ("dark matter", "little red dot", "yunao xiao")
    assert profile.boost_keywords == ("dark matter", "little red dot", "yunao xiao")
    assert profile.favorite_authors == ("dark matter", "little red dot", "yunao xiao")
    assert profile.max_papers == 8
    assert "dark matter; little red dot; yunao xiao" in profile.summary_requirements


def test_subscription_subject_is_exact_case_insensitive():
    assert is_subscription_subject(SUBSCRIBE_SUBJECT)
    assert is_subscription_subject("subscribe to dailyarxiv")
    assert not is_subscription_subject("Subscribe dailyarxiv")


def test_subscription_receipt_documents_format():
    profile = parse_subscription_request("dark matter; stellar streams", "user@example.com")
    body = render_subscription_receipt(profile)

    assert subscription_receipt_subject() == "dailyarxiv 订阅成功"
    assert "user@example.com" in body
    assert "Subscribe to dailyarxiv" in body
    assert "dark matter; little red dot; yunao xiao" in body
