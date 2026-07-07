# Healthcare Cost Predictor Portal

A consumer-friendly healthcare cost prediction prototype.

This repository starts with:

- A FastAPI backend for cost estimates
- A static portal UI served by FastAPI
- A transparent placeholder estimator
- A roadmap for replacing the placeholder with public price-transparency data and ML models

The current estimator is not a production pricing model. It is a working product scaffold that lets us build the user experience, API contract, data pipeline, and evaluation workflow before connecting large CMS, hospital, and payer datasets.

## Run Locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Test

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

## API

`GET /api/procedures`

Returns supported starter procedures.

`POST /api/estimate`

Example request:

```json
{
  "procedure_id": "mri_brain",
  "zip_code": "90210",
  "payer_type": "commercial",
  "site_of_care": "independent_imaging_center",
  "complexity": "typical"
}
```

Example response:

```json
{
  "point_estimate": 1693.88,
  "low_estimate": 1287.35,
  "high_estimate": 2100.41,
  "confidence": "medium"
}
```

## Data Direction

The first real-data version should focus on narrow, shoppable procedures such as MRI, CT, colonoscopy, mammogram, and outpatient surgery. Long inpatient stays are important, but they are harder because severity, complications, and bundled services dominate final cost.

Candidate sources:

- Hospital Price Transparency machine-readable files
- Transparency in Coverage insurer machine-readable files
- CMS Medicare payment and utilization public use files
- CMS hospital outpatient and inpatient public use files
- CMS Care Compare quality data

See [docs/data-roadmap.md](docs/data-roadmap.md).

## Product Direction

The site should estimate ranges, not pretend false precision.

Useful output:

- Expected total cost range
- Typical local range
- Confidence level
- Key drivers of price
- Provider/facility comparison
- Quality and safety signals when available

## Privacy

The project should avoid collecting protected health information. For consumer-facing use, the first version should work with anonymous inputs such as procedure, ZIP code, payer type, and site of care.

