from app.data_seed import (
    COMPLEXITY_FACTORS,
    PAYER_FACTORS,
    PROCEDURES,
    SITE_FACTORS,
    ZIP_PREFIX_FACTORS,
)
from app.schemas import EstimateRequest, EstimateResponse, ProcedureOption


def list_procedures() -> list[ProcedureOption]:
    return [
        ProcedureOption(
            id=procedure_id,
            name=metadata["name"],
            category=metadata["category"],
            notes=metadata["notes"],
        )
        for procedure_id, metadata in PROCEDURES.items()
    ]


def _zip_factor(zip_code: str) -> float:
    first_digit = next((character for character in zip_code if character.isdigit()), "")
    return ZIP_PREFIX_FACTORS.get(first_digit, 1.0)


def _confidence(request: EstimateRequest) -> str:
    if request.payer_type == "unknown" or request.site_of_care == "unknown":
        return "low"
    if request.complexity in {"elevated", "high"}:
        return "medium"
    return "medium"


def estimate_cost(request: EstimateRequest) -> EstimateResponse:
    if request.procedure_id not in PROCEDURES:
        raise KeyError(f"Unknown procedure_id: {request.procedure_id}")

    procedure = PROCEDURES[request.procedure_id]
    base_cost = float(procedure["base_cost"])
    payer_factor = PAYER_FACTORS.get(request.payer_type, PAYER_FACTORS["unknown"])
    site_factor = SITE_FACTORS.get(request.site_of_care, SITE_FACTORS["unknown"])
    complexity_factor = COMPLEXITY_FACTORS.get(request.complexity, COMPLEXITY_FACTORS["typical"])
    geography_factor = _zip_factor(request.zip_code)

    point_estimate = base_cost * payer_factor * site_factor * complexity_factor * geography_factor
    range_width = 0.24 if _confidence(request) == "medium" else 0.38
    low_estimate = point_estimate * (1 - range_width)
    high_estimate = point_estimate * (1 + range_width)

    return EstimateResponse(
        procedure_id=request.procedure_id,
        procedure_name=procedure["name"],
        category=procedure["category"],
        point_estimate=round(point_estimate, 2),
        low_estimate=round(low_estimate, 2),
        high_estimate=round(high_estimate, 2),
        confidence=_confidence(request),
        factors={
            "base_cost": base_cost,
            "payer_factor": payer_factor,
            "site_factor": site_factor,
            "complexity_factor": complexity_factor,
            "geography_factor": geography_factor,
        },
        caveats=[
            "Prototype estimate only; not medical, financial, or billing advice.",
            "Final patient cost depends on plan benefits, deductible status, network status, bundled services, and clinical complexity.",
            "This starter uses transparent heuristic factors until public price-transparency and CMS data ingestion are added.",
        ],
    )

