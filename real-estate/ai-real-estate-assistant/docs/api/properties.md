# Property Search and AI Tools

## Property Search

Perform semantic property search with advanced filtering and geospatial queries.

### Search Properties

```http
POST /api/v1/search
```

**Authentication**: API Key required

### Request Body

```json
{
  "query": "2-bedroom apartment in Berlin under 500k",
  "limit": 10,
  "filters": {
    "city": "Berlin",
    "min_price": 100000,
    "max_price": 500000,
    "min_rooms": 2,
    "max_rooms": 3,
    "property_type": "apartment"
  },
  "alpha": 0.7,
  "lat": 52.52,
  "lon": 13.405,
  "radius_km": 10,
  "sort_by": "price",
  "sort_order": "asc"
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Natural language search query |
| `limit` | integer | No | Max results (1-50, default: 10) |
| `filters` | object | No | Metadata filters |
| `alpha` | float | No | Hybrid search weight (0=keyword, 1=vector, default: 0.7) |
| `lat` | float | No | Latitude for geo-search (-90 to 90) |
| `lon` | float | No | Longitude for geo-search (-180 to 180) |
| `radius_km` | float | No | Search radius in kilometers |
| `min_lat` | float | No | Bounding box minimum latitude |
| `max_lat` | float | No | Bounding box maximum latitude |
| `min_lon` | float | No | Bounding box minimum longitude |
| `max_lon` | float | No | Bounding box maximum longitude |
| `sort_by` | string | No | Field to sort by: `relevance`, `price`, `price_per_sqm`, `area_sqm`, `year_built` |
| `sort_order` | string | No | Sort order: `asc` or `desc` |

### Available Filters

| Filter | Type | Example |
|--------|------|---------|
| `city` | string | `"Berlin"` |
| `country` | string | `"Germany"` |
| `min_price` | float | `100000` |
| `max_price` | float | `500000` |
| `min_rooms` | float | `2` |
| `max_rooms` | float | `4` |
| `min_bathrooms` | float | `1` |
| `max_bathrooms` | float | `2` |
| `property_type` | string | `"apartment"`, `"house"` |
| `listing_type` | string | `"rent"`, `"sale"` |

### Response

```json
{
  "results": [
    {
      "property": {
        "id": "prop_123",
        "title": "Modern 2-Bedroom Apartment",
        "city": "Berlin",
        "country": "Germany",
        "price": 450000,
        "price_per_sqm": 6000,
        "rooms": 2,
        "bathrooms": 1,
        "area_sqm": 75,
        "property_type": "apartment",
        "listing_type": "sale",
        "latitude": 52.52,
        "longitude": 13.405,
        "year_built": 2020,
        "description": "Spacious apartment...",
        "images": ["https://example.com/image1.jpg"]
      },
      "score": 0.95
    }
  ],
  "count": 1
}
```

### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "apartment in Berlin",
    "limit": 5,
    "filters": {
      "max_price": 500000
    }
  }'
```

---

## Conversational AI (Chat)

AI-powered assistant for property inquiries using retrieval-augmented generation.

### Chat Endpoint

```http
POST /api/v1/chat
```

**Authentication**: API Key required

### Request Body

```json
{
  "message": "What 2-bedroom apartments are available in Berlin under 400k?",
  "session_id": "optional-session-id",
  "stream": false,
  "include_intermediate_steps": false
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User message/question |
| `session_id` | string | No | Conversation session ID (auto-generated if omitted) |
| `stream` | boolean | No | Enable Server-Sent Events streaming (default: false) |
| `include_intermediate_steps` | boolean | No | Include agent reasoning steps (default: false) |

### Response (Non-Streaming)

```json
{
  "response": "Based on the current listings, there are 3 apartments available...",
  "sources": [
    {
      "id": "prop_123",
      "title": "Modern Apartment",
      "snippet": "2 bedrooms, 75 sqm, recently renovated",
      "score": 0.92
    }
  ],
  "sources_truncated": false,
  "session_id": "sess_abc123",
  "intermediate_steps": null
}
```

### Response (Streaming)

When `stream=true`, returns Server-Sent Events:

```
data: {"content": "Based"}

data: {"content": " on the"}

data: {"content": " current listings"}

event: meta
data: {"sources": [...], "session_id": "sess_abc123"}

data: [DONE]
```

### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me properties in Berlin with 3 bedrooms"
  }'
```

---

## Retrieval Augmented Generation (RAG)

Upload documents and query them with AI-powered Q&A.

### Upload Documents

```http
POST /api/v1/rag/upload
```

**Authentication**: API Key required

### Request

```
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | file[] | Yes | Documents to upload (PDF, DOCX, TXT, MD) |

### Limits

- Max files: 10
- Max file size: 10 MB
- Max total size: 25 MB

### Response

```json
{
  "message": "Upload processed",
  "chunks_indexed": 42,
  "errors": []
}
```

### Reset Knowledge

```http
POST /api/v1/rag/reset
```

Response:
```json
{
  "message": "Knowledge cleared",
  "documents_removed": 42,
  "documents_remaining": 0
}
```

### Query Documents

```http
POST /api/v1/rag/qa
```

Request body:
```json
{
  "question": "What are the rental requirements?",
  "top_k": 5,
  "provider": "openai",
  "model": "gpt-4"
}
```

Response:
```json
{
  "answer": "Based on the documents, rental requirements include...",
  "citations": [
    {
      "source": "rental_agreement.pdf",
      "chunk_index": 3,
      "page_number": 2
    }
  ],
  "llm_used": true,
  "provider": "openai",
  "model": "gpt-4"
}
```

---

## Calculation Tools

### Mortgage Calculator

```http
POST /api/v1/tools/mortgage-calculator
```

Request body:
```json
{
  "property_price": 450000,
  "down_payment_percent": 20,
  "interest_rate": 4.5,
  "loan_years": 30
}
```

Response:
```json
{
  "monthly_payment": 1824.27,
  "total_payment": 656737.20,
  "total_interest": 346737.20,
  "loan_amount": 360000,
  "down_payment": 90000
}
```

### Total Cost of Ownership (TCO)

```http
POST /api/v1/tools/tco-calculator
```

Request body:
```json
{
  "property_price": 450000,
  "down_payment_percent": 20,
  "interest_rate": 4.5,
  "loan_years": 30,
  "monthly_hoa": 200,
  "annual_property_tax": 3000,
  "annual_insurance": 1200,
  "monthly_utilities": 250,
  "monthly_internet": 50,
  "monthly_parking": 100,
  "maintenance_percent": 1.0
}
```

Response:
```json
{
  "monthly_mortgage": 1824.27,
  "monthly_property_tax": 250,
  "monthly_insurance": 100,
  "monthly_hoa": 200,
  "monthly_utilities": 250,
  "monthly_internet": 50,
  "monthly_parking": 100,
  "monthly_maintenance": 375,
  "total_monthly_cost": 3149.27,
  "total_annual_cost": 37791.24,
  "total_30_year_cost": 1133737.20
}
```

### Investment Analysis

```http
POST /api/v1/tools/investment-analysis
```

Request body:
```json
{
  "property_price": 450000,
  "monthly_rent": 2500,
  "down_payment_percent": 20,
  "closing_costs": 15000,
  "renovation_costs": 10000,
  "interest_rate": 4.5,
  "loan_years": 30,
  "property_tax_monthly": 250,
  "insurance_monthly": 100,
  "hoa_monthly": 200,
  "maintenance_percent": 1.0,
  "vacancy_rate": 5.0,
  "management_percent": 8.0
}
```

Response:
```json
{
  "monthly_cash_flow": 283.67,
  "annual_cash_flow": 3404.04,
  "cash_on_cash_roi": 7.76,
  "cap_rate": 5.65,
  "gross_yield": 6.67,
  "net_yield": 5.48,
  "total_investment": 43875.00,
  "monthly_income": 2375.00,
  "monthly_expenses": 2091.33,
  "monthly_mortgage": 1824.27,
  "investment_score": 72.5,
  "score_breakdown": {
    "cash_flow": 75.0,
    "appreciation": 70.0,
    "location": 75.0
  }
}
```

### Compare Properties

```http
POST /api/v1/tools/compare-properties
```

Request body:
```json
{
  "property_ids": ["prop_123", "prop_456", "prop_789"]
}
```

Response:
```json
{
  "properties": [
    {
      "id": "prop_123",
      "price": 450000,
      "price_per_sqm": 6000,
      "city": "Berlin",
      "rooms": 3,
      "bathrooms": 2,
      "area_sqm": 75,
      "year_built": 2020,
      "property_type": "apartment"
    }
  ],
  "summary": {
    "count": 3,
    "min_price": 420000,
    "max_price": 500000,
    "price_difference": 80000
  }
}
```

### Price Analysis

```http
POST /api/v1/tools/price-analysis
```

Request body:
```json
{
  "query": "apartments in Berlin"
}
```

Response:
```json
{
  "query": "apartments in Berlin",
  "count": 42,
  "average_price": 475000,
  "median_price": 450000,
  "min_price": 250000,
  "max_price": 850000,
  "average_price_per_sqm": 6200,
  "median_price_per_sqm": 5800,
  "distribution_by_type": {
    "apartment": 38,
    "house": 4
  }
}
```

### Commute Time Analysis

```http
POST /api/v1/tools/commute-time
```

Request body:
```json
{
  "property_id": "prop_123",
  "destination_lat": 52.52,
  "destination_lon": 13.405,
  "mode": "transit",
  "destination_name": "Berlin Central Station",
  "departure_time": "2024-01-15T08:30:00"
}
```

Modes: `driving`, `walking`, `bicycling`, `transit`

Response:
```json
{
  "result": {
    "property_id": "prop_123",
    "origin_lat": 52.51,
    "origin_lon": 13.39,
    "destination_lat": 52.52,
    "destination_lon": 13.405,
    "destination_name": "Berlin Central Station",
    "duration_seconds": 1800,
    "duration_text": "30m",
    "distance_meters": 8500,
    "distance_text": "8.5km",
    "mode": "transit",
    "polyline": "encoded_polyline_here",
    "arrival_time": "2024-01-15T09:00:00",
    "departure_time": "2024-01-15T08:30:00"
  }
}
```

### Commute Ranking

```http
POST /api/v1/tools/commute-ranking
```

Request body:
```json
{
  "property_ids": "prop_123,prop_456,prop_789",
  "destination_lat": 52.52,
  "destination_lon": 13.405,
  "mode": "transit",
  "destination_name": "Berlin Central Station"
}
```

Response:
```json
{
  "destination_name": "Berlin Central Station",
  "destination_lat": 52.52,
  "destination_lon": 13.405,
  "mode": "transit",
  "rankings": [
    {
      "property_id": "prop_123",
      "duration_seconds": 1800,
      "duration_text": "30m"
    }
  ],
  "count": 3,
  "fastest_duration_seconds": 1500,
  "slowest_duration_seconds": 2400
}
```

### Neighborhood Quality

```http
POST /api/v1/tools/neighborhood-quality
```

Request body:
```json
{
  "property_id": "prop_123",
  "latitude": 52.52,
  "longitude": 13.405,
  "city": "Berlin",
  "neighborhood": "Mitte"
}
```

Response:
```json
{
  "property_id": "prop_123",
  "overall_score": 75.5,
  "safety_score": 80.0,
  "schools_score": 72.0,
  "amenities_score": 78.0,
  "walkability_score": 85.0,
  "green_space_score": 70.0,
  "score_breakdown": {
    "crime_rate": 80.0,
    "school_quality": 72.0,
    "public_transport": 90.0,
    "shops_restaurants": 75.0,
    "parks": 70.0
  },
  "data_sources": ["open_data", "public_records"],
  "latitude": 52.52,
  "longitude": 13.405,
  "city": "Berlin",
  "neighborhood": "Mitte"
}
```

---

## Administration

### Get Version

```http
GET /api/v1/admin/version
```

Response:
```json
{
  "version": "1.0.0",
  "environment": "production",
  "app_title": "AI Real Estate Assistant",
  "python_version": "3.12.0",
  "platform": "Linux-5.15.0-x86_64"
}
```

### Ingest Data

```http
POST /api/v1/admin/ingest
```

Request body:
```json
{
  "file_urls": ["https://example.com/properties.csv"],
  "sheet_name": "Sheet1",
  "header_row": 0,
  "source_name": "properties_2024"
}
```

Response:
```json
{
  "message": "Ingestion successful",
  "properties_processed": 1500,
  "errors": [],
  "source_type": "csv",
  "source_name": "properties_2024"
}
```

### Reindex Data

```http
POST /api/v1/admin/reindex
```

Request body:
```json
{
  "clear_existing": false
}
```

Response:
```json
{
  "message": "Reindexing successful",
  "count": 1500
}
```

### Health Check

```http
GET /api/v1/admin/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Data Export

### Export Properties

```http
POST /api/v1/export/properties
```

Request body:
```json
{
  "format": "csv",
  "property_ids": ["prop_123", "prop_456"],
  "search": {
    "query": "apartments in Berlin",
    "limit": 100
  },
  "columns": ["id", "title", "price", "city"],
  "include_header": true
}
```

Formats: `csv`, `json`, `markdown`, `excel`, `pdf`

Returns file download with appropriate content-type.

---

## List Available Tools

```http
GET /api/v1/tools
```

Response:
```json
[
  {
    "name": "mortgage-calculator",
    "description": "Calculate monthly mortgage payments"
  },
  {
    "name": "tco-calculator",
    "description": "Calculate total cost of ownership"
  },
  {
    "name": "investment-analysis",
    "description": "Analyze investment property returns"
  }
]
```
