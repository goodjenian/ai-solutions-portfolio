# Market Analytics

Price history and market trend endpoints for property analytics.

**Authentication**: JWT required for all endpoints

---

## Price History

Get historical price data for a specific property.

### Get Property Price History

```http
GET /api/v1/market/price-history/{property_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `property_id` | string | Yes | Property ID to fetch history for |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Max snapshots (1-1000, default: 100) |

### Response

```json
{
  "property_id": "prop_123",
  "snapshots": [
    {
      "id": "snap_abc123",
      "property_id": "prop_123",
      "price": 450000,
      "price_per_sqm": 6000,
      "currency": "EUR",
      "source": "immobilienscout24",
      "recorded_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 42,
  "current_price": 450000,
  "first_recorded": "2023-06-01T10:00:00Z",
  "last_recorded": "2024-01-15T10:00:00Z",
  "price_change_percent": 5.25,
  "trend": "increasing"
}
```

### Trend Values

| Value | Description |
|-------|-------------|
| `increasing` | Price has risen by more than 2% |
| `decreasing` | Price has fallen by more than 2% |
| `stable` | Price change is within +/- 2% |
| `insufficient_data` | Not enough data points to determine trend |

### cURL Example

```bash
curl -X GET "http://localhost:8000/api/v1/market/price-history/prop_123?limit=50" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Market Trends

Get aggregate market trend data over time.

### Get Market Trends

```http
GET /api/v1/market/trends
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `city` | string | No | Filter by city |
| `district` | string | No | Filter by district |
| `interval` | string | No | `month`, `quarter`, `year` (default: `month`) |
| `months_back` | integer | No | Months of history (1-60, default: 12) |

### Response

```json
{
  "city": "Berlin",
  "district": null,
  "interval": "month",
  "data_points": [
    {
      "period": "2024-01",
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z",
      "average_price": 475000,
      "median_price": 450000,
      "volume": 1250,
      "avg_price_per_sqm": 6200
    },
    {
      "period": "2023-12",
      "start_date": "2023-12-01T00:00:00Z",
      "end_date": "2023-12-31T23:59:59Z",
      "average_price": 470000,
      "median_price": 445000,
      "volume": 1180,
      "avg_price_per_sqm": 6150
    }
  ],
  "trend_direction": "increasing",
  "change_percent": 5.25,
  "confidence": "high"
}
```

### Trend Direction Values

| Value | Description |
|-------|-------------|
| `increasing` | Market is trending upward |
| `decreasing` | Market is trending downward |
| `stable` | Market is stable |
| `insufficient_data` | Not enough data |

### Confidence Levels

| Level | Description |
|--------|-------------|
| `high` | 100+ data points |
| `medium` | 50-99 data points |
| `low` | Less than 50 data points |

### cURL Example

```bash
curl -X GET "http://localhost:8000/api/v1/market/trends?city=Berlin&interval=month&months_back=12" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Market Indicators

Get current market health indicators and district rankings.

### Get Market Indicators

```http
GET /api/v1/market/indicators
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `city` | string | No | Filter by city |

### Response

```json
{
  "city": "Berlin",
  "overall_trend": "rising",
  "avg_price_change_1m": 1.2,
  "avg_price_change_3m": 3.5,
  "avg_price_change_6m": 5.8,
  "avg_price_change_1y": 8.2,
  "total_listings": 15420,
  "new_listings_7d": 342,
  "price_drops_7d": 87,
  "hottest_districts": [
    {
      "name": "Mitte",
      "avg_price": 650000,
      "count": 2450
    },
    {
      "name": "Prenzlauer Berg",
      "avg_price": 580000,
      "count": 1820
    }
  ],
  "coldest_districts": [
    {
      "name": "Spandau",
      "avg_price": 320000,
      "count": 680
    },
    {
      "name": "Marzahn",
      "avg_price": 280000,
      "count": 420
    }
  ]
}
```

### Market Trend Types

| Value | Description |
|-------|-------------|
| `rising` | Average prices increasing |
| `falling` | Average prices decreasing |
| `stable` | Average prices stable |

### cURL Example

```bash
curl -X GET "http://localhost:8000/api/v1/market/indicators?city=Berlin" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Use Cases

### Property Price Tracking

Track price changes for a property over time:

```bash
curl -X GET "http://localhost:8000/api/v1/market/price-history/prop_123" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Market Analysis

Analyze market trends in a specific city:

```bash
curl -X GET "http://localhost:8000/api/v1/market/trends?city=Berlin&interval=quarter&months_back=24" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### District Comparison

Get hottest and coldest districts:

```bash
curl -X GET "http://localhost:8000/api/v1/market/indicators?city=Berlin" \
  -H "Authorization: Bearer $JWT_TOKEN"
```
