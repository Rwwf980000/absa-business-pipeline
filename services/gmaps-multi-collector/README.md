# Google Maps Multi-Branch Collector

Collects Google Maps reviews for multiple business locations and uploads to Cloud Storage.

## Purpose

Automated collection of reviews from multiple branches/locations of your business using the Google Maps Places API.

## Features

- Collects from multiple branches (configurable)
- Searches by business names (Arabic or English)
- Gets 5 most recent reviews per branch
- Exports to CSV with clean formatting
- Automatically uploads to Cloud Storage
- Error tracking per branch

## Configuration

Edit the `BRANCHES` array in `main.py` with your locations:

```python
BRANCHES = [
    {"id": 1, "name": "Branch 1 Name", "query": "Your Business Name Location City"},
    {"id": 2, "name": "Branch 2 Name", "query": "Your Business Name Location City"},
    # Add more branches as needed
]
```

### Examples:
- Restaurant: `{"id": 1, "name": "Restaurant - Mall", "query": "My Restaurant King Abdullah Mall Riyadh"}`
- Cafe: `{"id": 2, "name": "Coffee Shop - Downtown", "query": "Coffee Shop Downtown Dubai"}`
- Retail: `{"id": 3, "name": "Electronics Store", "query": "Electronics Store Main Street Jeddah"}`

## Environment Variables

- `GOOGLE_MAPS_API_KEY` - Google Maps API key (required)
- `BUCKET_NAME` - Cloud Storage bucket name (default: absa-reviews)

## API Usage

```bash
curl https://REGION-PROJECT.cloudfunctions.net/gmaps-multi-collector
```

### Response

```json
{
  "status": "success",
  "reviews_collected": 85,
  "branches_successful": 18,
  "branches_total": 20,
  "branches_failed": 2,
  "failed_branches": ["Branch A", "Branch B"],
  "file": "gmaps/reviews_all_branches_20250210_123456.csv"
}
```

## Deployment

```bash
gcloud functions deploy gmaps-multi-collector \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --region me-central2 \
  --set-env-vars GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY}",BUCKET_NAME="${BUCKET_NAME}" \
  --timeout 540s \
  --memory 512MB
```

## CSV Output Format

Columns:
- `data_source` - Always "gmaps"
- `branch_id` - Branch ID (1-20)
- `branch_name` - English branch name
- `place_name` - Arabic name from Google Maps
- `place_id` - Google Maps Place ID
- `address` - Full address
- `phone` - Phone number
- `overall_rating` - Place rating (1-5)
- `total_user_ratings` - Total ratings count
- `author_name` - Reviewer name
- `author_url` - Reviewer profile
- `rating` - Review rating (1-5)
- `raw_review` - Review text
- `time` - Unix timestamp
- `relative_time` - Human readable time
- `language` - Review language
- `collected_at` - Collection timestamp

## Files

- `main.py` - Collector function
- `branches_example.json` - Example branch configuration
- `requirements.txt` - Dependencies

## Notes

- Configure your branches in the BRANCHES array in main.py
- Searches using business names for accuracy
- Limited to 5 reviews per branch (API limitation)
- Text cleaned to remove newlines
- Saves to `gs://BUCKET/gmaps/` with timestamp
