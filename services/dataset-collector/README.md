# Dataset Collector Service

Owns public data source registration, dataset version metadata, and future download/normalization jobs.

Current version:

- FastAPI service
- PostgreSQL-backed catalog
- Seed CMS data sources
- Dataset version registration endpoint

Future version:

- Background download jobs
- Checksum validation
- Normalization pipelines
- Data quality checks

Expected environment:

```text
DATABASE_URL=postgresql+psycopg://healthcost:healthcost@localhost:5432/healthcost
```
