# Data Roadmap

## Goal

Build a consumer-friendly cost predictor that estimates realistic healthcare price ranges for common services.

The product should answer:

- What might this cost near me?
- How much does the cost vary by facility or site of care?
- How confident is the estimate?
- What factors could make my final bill different?

## Phase 1: Procedure-Level Prototype

Start with a small set of shoppable services:

- MRI brain
- CT abdomen/pelvis
- Screening colonoscopy
- Screening mammogram
- Urgent care visit
- Knee arthroscopy

Model target:

- Estimated total allowed amount or negotiated amount

Inputs:

- Procedure code or normalized procedure group
- ZIP/geography
- Payer category
- Facility/site of care
- Complexity bucket

## Phase 2: Public Data Ingestion

Hospital Price Transparency files:

- Standard charges
- Discounted cash prices
- Payer-specific negotiated rates
- Minimum and maximum negotiated charges

Transparency in Coverage files:

- In-network negotiated rates
- Out-of-network allowed amounts
- Payer/provider/service combinations

CMS files:

- Medicare payment and utilization public use files
- Hospital inpatient/outpatient public use files
- Provider and facility identifiers

## Phase 3: Data Normalization

Key work:

- Normalize procedure codes and descriptions
- Match facilities and NPIs
- Map hospitals to geography
- Identify site of care
- Remove impossible or placeholder prices
- Create service bundles where consumers experience one episode of care

## Phase 4: Model Strategy

Start with interpretable baselines:

- Median by service/geography/site
- Quantile regression
- Gradient boosted trees

Then add PyTorch where it helps:

- Embeddings for procedure, payer, provider, and geography
- Multi-task prediction for low/median/high cost
- Uncertainty estimation
- Text normalization for messy procedure descriptions

## Phase 5: Evaluation

Metrics:

- Median absolute error
- Mean absolute percentage error by procedure group
- Prediction interval coverage
- Error by geography
- Error by payer type
- Error by site of care

Consumer-facing estimates should show ranges and confidence, not a single exact dollar claim.

## HIPAA Boundary

HIPAA protects identifiable patient health information. The first versions should avoid collecting patient identifiers, diagnoses, dates of service, claim numbers, member IDs, or detailed clinical histories.

Use public, aggregated, de-identified, or price-transparency data sources until there is a clear compliance plan for anything more sensitive.

