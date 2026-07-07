# Dataset Collector Service

Owns public data source registration, dataset version metadata, and future download/normalization jobs.

Current version:

- FastAPI service
- PostgreSQL-backed catalog
- Seed CMS data sources
- Source registration/update endpoint
- Dataset version registration endpoint
- Raw file download endpoint
- SHA-256 checksum calculation
- Dataset status transitions
- Deterministic collection agent for starter CMS dataset proposals

Future version:

- Normalization pipelines
- Data quality checks

Expected environment:

```text
DATABASE_URL=postgresql+psycopg://healthcost:healthcost@localhost:5432/healthcost
COLLECTOR_STORAGE_DIR=data/raw
```

## Workflow

1. Register or confirm a data source.
2. Register a dataset version with `source_url`.
3. Download the dataset version.
4. The service stores the raw file, calculates checksum/byte count, and marks the version `downloaded`.
5. A future normalizer marks it `normalized`, `validated`, then `trainable`.

## Agent Workflow

The collection agent proposes datasets. It does not download by itself.

Create an agent run:

```http
POST /agent-runs
```

```json
{
  "goal": "cms_starter",
  "limit": 5
}
```

Inspect the proposals, then apply them:

```http
POST /agent-runs/{agent_run_id}/apply
```

Applying an agent run registers dataset versions with `requires_human_review_before_download=true`.

Current policy:

- deterministic starter proposals only
- allowlisted CMS domains
- no automatic downloads
- human review required before download

## API Shape

Register a dataset version:

```http
POST /dataset-versions
```

```json
{
  "source_id": "cms-provider-utilization",
  "name": "CMS provider utilization 2024",
  "source_url": "https://example.com/provider-2024.csv",
  "metadata": {
    "year": 2024
  }
}
```

Download it:

```http
POST /dataset-versions/{dataset_version_id}/download
```

```json
{
  "filename": "provider-2024.csv"
}
```

The response includes:

- `status`
- `raw_uri`
- `checksum_sha256`
- `metadata.byte_count`
- `metadata.downloaded_at`
