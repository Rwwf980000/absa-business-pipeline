# ABSA Business Reviews Analysis Pipeline

Complete pipeline for collecting, enriching, and analyzing business reviews using Aspect-Based Sentiment Analysis (ABSA) with Google Gemini AI.

## 📁 Project Structure

```
absa-fitness-pipeline/
├── services/
│   ├── gmaps-multi-collector/      # Google Maps review collector
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── fitness_time_branches.json
│   │   └── README.md
│   │
│   ├── absa-gemini-enricher/       # Gemini AI sentiment analyzer
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   └── absa-orchestrator/          # Pipeline orchestrator
│       ├── main.py
│       ├── bigquery_manager.py
│       ├── requirements.txt
│       └── README.md
│
├── tests/                          # Test files
│   ├── test_collector.py
│   ├── test_enricher.py
│   ├── test_orchestrator.py
│   └── README.md
│
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## 🎯 Overview

This system processes business reviews through three Cloud Functions:

1. **gmaps-multi-collector**: Collects reviews from Google Maps for multiple business locations
2. **absa-gemini-enricher**: Analyzes reviews using Gemini AI to extract aspects and sentiment
3. **absa-orchestrator**: Orchestrates the pipeline, processes data, and loads to BigQuery

### Data Flow

```
Google Maps Reviews
        ↓
[gmaps-multi-collector] → CSV → Cloud Storage
        ↓
[absa-orchestrator] → reads CSV → normalizes text
        ↓
[absa-gemini-enricher] → ABSA analysis
        ↓
[absa-orchestrator] → BigQuery tables & views
        ↓
Analysis Dashboard
```

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project
- Google Maps API key (Places API enabled)
- Gemini API key
- Cloud Storage bucket
- BigQuery dataset

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd absa-fitness-pipeline

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Configure Environment Variables

Edit `.env` with your values:

```bash
# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Gemini AI API
GEMINI_API_KEY=your_gemini_api_key

# Google Cloud Project
PROJECT_ID=your-gcp-project-id
BUCKET_NAME=your-bucket-name
BQ_DATASET=your-dataset-name
BQ_TABLE_RAW=your-table-name

# URLs (update after deploying functions)
HANDLER_URL=https://REGION-PROJECT.cloudfunctions.net/absa-gemini-enricher

# Processing
MAX_WORKERS=2
```

### 3. Deploy Services

Deploy in this order:

```bash
# 1. Deploy Gemini Enricher (needed by orchestrator)
cd services/absa-gemini-enricher
gcloud functions deploy absa-gemini-enricher \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --region me-central2 \
  --set-env-vars GEMINI_API_KEY="${GEMINI_API_KEY}" \
  --timeout 180s \
  --memory 512MB

# Note the function URL and update HANDLER_URL in .env

# 2. Deploy Google Maps Collector
cd ../gmaps-multi-collector
gcloud functions deploy gmaps-multi-collector \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --region me-central2 \
  --set-env-vars GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY}",BUCKET_NAME="${BUCKET_NAME}" \
  --timeout 540s \
  --memory 512MB

# 3. Deploy Orchestrator
cd ../absa-orchestrator
gcloud functions deploy absa-orchestrator \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --region me-central2 \
  --set-env-vars PROJECT_ID="${PROJECT_ID}",BUCKET_NAME="${BUCKET_NAME}",BQ_DATASET="${BQ_DATASET}",BQ_TABLE_RAW="${BQ_TABLE_RAW}",HANDLER_URL="${HANDLER_URL}",MAX_WORKERS="${MAX_WORKERS}" \
  --timeout 540s \
  --memory 2GB
```

### 4. Run the Pipeline

```bash
# Step 1: Collect reviews from Google Maps
curl https://REGION-PROJECT.cloudfunctions.net/gmaps-multi-collector

# Step 2: Process and analyze reviews
curl https://REGION-PROJECT.cloudfunctions.net/absa-orchestrator

# Or process specific source
curl "https://REGION-PROJECT.cloudfunctions.net/absa-orchestrator?source=gmaps"
```

## 📊 Services Details

### gmaps-multi-collector
- Collects reviews from multiple business branches/locations
- Searches by business names (Arabic or English)
- Saves to Cloud Storage as CSV
- See `services/gmaps-multi-collector/README.md`

### absa-gemini-enricher
- Analyzes Arabic text using Gemini 2.5 Flash
- Extracts 11 aspects (cleanliness, quality, staff, service, etc.)
- Assigns sentiment polarity (positive/negative/neutral)
- Handles Arabic dialects and sarcasm
- See `services/absa-gemini-enricher/README.md`

### absa-orchestrator
- Reads data from Cloud Storage
- Deduplicates reviews
- Normalizes Arabic text
- Calls enricher for ABSA analysis
- Loads to BigQuery with automatic views
- See `services/absa-orchestrator/README.md`

## 🧪 Testing

```bash
cd tests

# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific service tests
pytest test_collector.py
pytest test_enricher.py
pytest test_orchestrator.py

# Run with coverage
pytest --cov=services --cov-report=html
```

See `tests/README.md` for testing documentation.

## 📈 BigQuery Views

The orchestrator automatically creates these analytical views:

- `reviews_parsed` - Flattened aspect-level data
- `aspect_summary` - Aspect mentions by source and polarity
- `sentiment_by_source` - Sentiment distribution per data source
- `daily_processing_stats` - Daily processing metrics
- `top_aspects_by_place` - Top aspects per location
- `negative_feedback` - All negative sentiment reviews
- `rating_vs_sentiment` - Correlation between ratings and sentiment

### Example Query

```sql
-- Top negative aspects across all branches
SELECT 
  aspect,
  COUNT(*) as mentions,
  COUNT(DISTINCT place_name) as branches_affected
FROM `PROJECT.DATASET.reviews_parsed`
WHERE polarity = 'سلبي'
GROUP BY aspect
ORDER BY mentions DESC
LIMIT 10;
```

## 🔒 Security

- **Never commit `.env`** - Contains sensitive API keys
- All secrets use environment variables
- `.gitignore` blocks sensitive files
- Use `.env.example` as a template only

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | `AIza...` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIza...` |
| `PROJECT_ID` | GCP Project ID | `my-project-123` |
| `BUCKET_NAME` | Cloud Storage bucket | `absa-reviews` |
| `BQ_DATASET` | BigQuery dataset | `absa_analysis` |
| `BQ_TABLE_RAW` | BigQuery table name | `reviews_all_sources` |
| `HANDLER_URL` | Enricher function URL | `https://...` |
| `MAX_WORKERS` | Parallel workers | `2` |

## 🐛 Troubleshooting

### Collector Issues
- **No reviews found**: Check branch names match Google Maps
- **API quota exceeded**: Increase quota or reduce frequency

### Enricher Issues
- **Timeout errors**: Reviews too long, increase timeout
- **Invalid JSON**: Gemini response parsing failed, check prompt

### Orchestrator Issues
- **Duplicates**: Check review_id generation
- **BigQuery errors**: Verify permissions and schema
- **Processing slow**: Increase MAX_WORKERS (max 5 recommended)

## 📚 Additional Resources

- [Google Maps Places API](https://developers.google.com/maps/documentation/places/web-service)
- [Google Gemini API](https://ai.google.dev/docs)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Cloud Functions Documentation](https://cloud.google.com/functions/docs)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Submit a pull request

## 📄 License

[Your License Here]

## 👥 Authors

[Your Name/Team]

## 🔄 Version History

- v1.0.0 - Initial release
  - Google Maps collector
  - Gemini ABSA enricher
  - BigQuery orchestrator
