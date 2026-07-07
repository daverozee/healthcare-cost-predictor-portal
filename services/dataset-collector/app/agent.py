from dataclasses import dataclass


ALLOWED_DOMAINS = {
    "data.cms.gov",
    "www.cms.gov",
}


@dataclass(frozen=True)
class DatasetProposal:
    source_id: str
    name: str
    source_url: str
    metadata: dict
    rationale: str

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "source_url": self.source_url,
            "metadata": self.metadata,
            "rationale": self.rationale,
        }


CMS_STARTER_PROPOSALS = [
    DatasetProposal(
        source_id="cms-provider-utilization",
        name="CMS Medicare Physician & Other Practitioners by Provider 2024",
        source_url="https://data.cms.gov/sites/default/files/2026-05/7323ba02-52e7-4a86-b2ce-ad210c25d9aa/MUP_PHY_R26_P05_V10_D24_Prov.csv",
        metadata={
            "year": 2024,
            "dataset_family": "medicare_provider_utilization",
            "grain": "provider",
            "recommended_use": "provider payment baseline and market intelligence",
        },
        rationale="Clean starter file already used by the prototype PyTorch provider-payment model.",
    ),
    DatasetProposal(
        source_id="cms-provider-utilization",
        name="CMS Medicare Physician & Other Practitioners by Provider and Service 2024",
        source_url="https://data.cms.gov/sites/default/files/2026-05/b5ebab5a-f490-418a-9bce-4b9f31419356/PHY_R26_P05_V10_D24_Prov_Svc.csv",
        metadata={
            "year": 2024,
            "dataset_family": "medicare_provider_utilization",
            "grain": "provider_service",
            "recommended_use": "procedure/service-level cost modeling",
        },
        rationale="Service-code detail is needed for consumer procedure cost prediction.",
    ),
]


class CollectionAgent:
    def propose(self, goal: str, limit: int = 5) -> tuple[dict, list[dict]]:
        normalized_goal = goal.strip().lower()
        policy = {
            "mode": "deterministic",
            "allowed_domains": sorted(ALLOWED_DOMAINS),
            "auto_download": False,
            "requires_human_review": True,
        }

        if normalized_goal in {"cms_starter", "starter", "provider_cost_starter"}:
            proposals = CMS_STARTER_PROPOSALS[:limit]
        else:
            proposals = []

        return policy, [proposal.to_dict() for proposal in proposals]


collection_agent = CollectionAgent()

