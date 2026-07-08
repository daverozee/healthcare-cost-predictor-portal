# Trainer Service

Owns PyTorch training run orchestration and model artifact registration.

Current version:

- FastAPI service
- PostgreSQL-backed training run registry
- Real PyTorch training execution for downloaded CMS provider payment datasets
- Model artifact metadata

Future version:

- Background job queue
- PyTorch tabular model training
- Dataset catalog integration
- Artifact storage
- Promotion workflow for active models

Expected environment:

```text
DATABASE_URL=postgresql+psycopg://healthcost:healthcost@localhost:5432/healthcost
MODEL_STORAGE_DIR=models
TRAINING_SAMPLE_ROWS=200000
TRAINING_EPOCHS=5
```

## Training Behavior

`POST /training-runs/{run_id}/run-now` now:

1. Reads dataset versions referenced by the queued training run.
2. Selects a downloaded or trainable CSV containing `Tot_Mdcr_Pymt_Amt`.
3. Trains a PyTorch tabular regression model on `log1p(Tot_Mdcr_Pymt_Amt)`.
4. Saves:
   - `model.pt`
   - `preprocessor.joblib`
   - `metrics.json`
   - `feature_columns.json`
5. Records artifact URIs and metrics on the training run.

Default local settings intentionally train on a sample so service calls finish in a reasonable time. Set `TRAINING_SAMPLE_ROWS=0` to use the full file.
