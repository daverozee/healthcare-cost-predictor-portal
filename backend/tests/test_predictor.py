from app.predictor import estimate_cost
from app.schemas import EstimateRequest


def test_estimate_returns_positive_range():
    response = estimate_cost(
        EstimateRequest(
            procedure_id="mri_brain",
            zip_code="90210",
            payer_type="commercial",
            site_of_care="independent_imaging_center",
            complexity="typical",
        )
    )

    assert response.low_estimate > 0
    assert response.low_estimate < response.point_estimate < response.high_estimate
    assert response.factors["geography_factor"] > 1


def test_unknown_payer_has_low_confidence():
    response = estimate_cost(
        EstimateRequest(
            procedure_id="urgent_care_visit",
            zip_code="37203",
            payer_type="unknown",
            site_of_care="unknown",
            complexity="typical",
        )
    )

    assert response.confidence == "low"

