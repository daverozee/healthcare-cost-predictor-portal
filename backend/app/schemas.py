from pydantic import BaseModel, Field


class EstimateRequest(BaseModel):
    procedure_id: str = Field(..., examples=["mri_brain"])
    zip_code: str = Field(..., min_length=3, max_length=10, examples=["90210"])
    payer_type: str = Field("unknown", examples=["commercial"])
    site_of_care: str = Field("unknown", examples=["hospital_outpatient"])
    complexity: str = Field("typical", examples=["typical"])


class EstimateResponse(BaseModel):
    procedure_id: str
    procedure_name: str
    category: str
    point_estimate: float
    low_estimate: float
    high_estimate: float
    confidence: str
    factors: dict[str, float]
    caveats: list[str]


class ProcedureOption(BaseModel):
    id: str
    name: str
    category: str
    notes: str

