# ABSA Gemini Enricher

Aspect-Based Sentiment Analysis service using Google Gemini AI for Arabic business reviews.

## Purpose

Analyzes Arabic reviews to extract specific aspects (cleanliness, quality, staff, service, etc.) and their sentiment polarity (positive/negative/neutral).

## Features

- Gemini 2.5 Flash model optimized for Arabic
- Extracts 11 predefined aspects
- Handles Arabic dialects and sarcasm
- Returns structured JSON output
- CORS enabled for web apps

## Analyzed Aspects

1. النظافة - Cleanliness
2. الجودة - Quality (products/services/equipment)
3. الموظفين - Staff
4. خدمة العملاء - Customer service
5. الزحام - Crowding/waiting time
6. السعر - Price
7. الموقع - Location
8. الصيانة - Maintenance
9. المرافق - Amenities/facilities
10. التنوع - Variety/options
11. ساعات العمل - Operating hours

## API Usage

### Request

```bash
curl -X POST https://REGION-PROJECT.cloudfunctions.net/absa-gemini-enricher \
  -H "Content-Type: application/json" \
  -d '{"normalized_text": "المكان نظيف جداً بس الموظفين تعاملهم سيء"}'
```

### Response

```json
[
  {"aspect": "النظافة", "polarity": "إيجابي"},
  {"aspect": "الموظفين", "polarity": "سلبي"}
]
```

## Environment Variables

- `GEMINI_API_KEY` - Your Gemini API key (required)

## Deployment

```bash
gcloud functions deploy absa-gemini-enricher \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --region me-central2 \
  --set-env-vars GEMINI_API_KEY="${GEMINI_API_KEY}" \
  --timeout 180s \
  --memory 512MB
```

## Error Handling

Returns system messages for errors:
- `HTTP_XXX` - API errors
- `TIMEOUT` - Request timeout
- `JSON_ERROR` - Parsing failed
- `NO_CANDIDATES` - No Gemini response
- `INTERNAL_ERROR` - Server error
