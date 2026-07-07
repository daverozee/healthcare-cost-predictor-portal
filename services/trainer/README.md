# Trainer Service

Owns PyTorch training run orchestration and model artifact registration.

Current version:

- FastAPI service
- PostgreSQL-backed training run registry
- Simulated training execution
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
```
