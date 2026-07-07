from app.agent import ALLOWED_DOMAINS, collection_agent


def test_agent_proposes_cms_starter_datasets():
    policy, proposals = collection_agent.propose("cms_starter")

    assert policy["requires_human_review"] is True
    assert policy["auto_download"] is False
    assert "data.cms.gov" in ALLOWED_DOMAINS
    assert len(proposals) >= 2
    assert proposals[0]["source_id"] == "cms-provider-utilization"
    assert proposals[0]["source_url"].startswith("https://data.cms.gov/")


def test_agent_returns_no_proposals_for_unknown_goal():
    _, proposals = collection_agent.propose("unknown")

    assert proposals == []

