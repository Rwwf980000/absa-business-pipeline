# ABSA Orchestrator

Pipeline orchestrator that reads reviews from Cloud Storage, processes them through the ABSA enricher, and loads results to BigQuery.

## Purpose

Central coordinator for the ABSA pipeline. Handles data ingestion, deduplication, normalization, enrichment, and BigQuery loading.

## Features

- Multi-source support (Google Maps, Twitter, Manual CSV)
- Automatic deduplication using review IDs
- Parallel processing with configurable workers
- BigQuery partitioned tables
- Automated analytical views creation
- Arabic text normalization

## Workflow

1. Reads latest CSV from Cloud Storage
2. Creates unique review IDs (MD5 hash)
3. Filters out already processed reviews
4. Normalizes Arabic text
5. Calls Gemini enricher in parallel
6. Loads results to BigQuery
7. Updates analytical views

## Environment Variables

- `PROJECT_ID` - GCP Project ID
- `BUCKET_NAME` - Cloud Storage bucket
- `BQ_DATASET` - BigQuery dataset name
- `BQ_TABLE_RAW` - Table name for raw reviews
- `HANDLER_URL` - URL of gemini enricher function
- `MAX_WORKERS` - Number of parallel workers (default: 2)

## API Usage

### Process All Sources

```bash
curl https://REGION-PROJECT.cloudfunctions.net/absa-orchestrator
```

### Process Specific Source

```bash
# Google Maps only
curl "https://REGION-PROJECT.cloudfunctions.net/absa-orchestrator?source=gmaps"

# Twitter only
curl "https://REGION-PROJECT.cloudfunctions.net/absa-orchestrator?source=twitter"

# Manual CSV only
curl "https://REGION-PROJECT.cloudfunctions.net/absa-orchestrator?source=manual"
```

### Response

```json
{
  "status": "success",
  "timestamp": "2025-02-10T13:45:00",
  "details": {
    "gmaps": {"status": "success", "records": 85},
    "twitter": {"status": "no_new_data"},
    "manual": {"status": "success", "records": 12}
  }
}
```

## Deployment

```bash
gcloud functions deploy absa-orchestrator \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --region me-central2 \
  --set-env-vars PROJECT_ID="${PROJECT_ID}",BUCKET_NAME="${BUCKET_NAME}",BQ_DATASET="${BQ_DATASET}",BQ_TABLE_RAW="${BQ_TABLE_RAW}",HANDLER_URL="${HANDLER_URL}",MAX_WORKERS="${MAX_WORKERS}" \
  --timeout 540s \
  --memory 2GB
```

## BigQuery Views

Auto-created views:
- `reviews_parsed` - Flattened aspect data
- `aspect_summary` - Aspect distribution
- `sentiment_by_source` - Sentiment stats
- `daily_processing_stats` - Daily metrics
- `top_aspects_by_place` - Top aspects per location
- `negative_feedback` - Negative reviews
- `rating_vs_sentiment` - Rating correlation

## Cloud Storage Structure

```
gs://BUCKET_NAME/
├── gmaps/
│   └── fitness_time_all_branches_YYYYMMDD_HHMMSS.csv
├── twitter/
│   └── tweets_YYYYMMDD_HHMMSS.csv
└── manual/
    └── manual_reviews_YYYYMMDD_HHMMSS.csv
```

## Files

- `main.py` - Main orchestrator function
- `bigquery_manager.py` - BigQuery utilities
- `requirements.txt` - Dependencies
