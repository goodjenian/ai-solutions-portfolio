# Favorites, Collections, and Saved Searches

User-specific features for saving and organizing properties.

**Authentication**: JWT required for all endpoints

---

## Favorites

Save properties to a personal watchlist.

### Add to Favorites

```http
POST /api/v1/favorites
```

Request body:
```json
{
  "property_id": "prop_123",
  "collection_id": "coll_abc123",
  "notes": "Great location, near U-Bahn"
}
```

Response (201 Created):
```json
{
  "id": "fav_xyz789",
  "user_id": "usr_123abc",
  "property_id": "prop_123",
  "collection_id": "coll_abc123",
  "notes": "Great location, near U-Bahn",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### List Favorites

```http
GET /api/v1/favorites
```

Query parameters:
- `collection_id` (optional): Filter by collection
- `limit` (optional, default: 50, max: 100)
- `offset` (optional, default: 0)

Response:
```json
{
  "items": [
    {
      "id": "fav_xyz789",
      "user_id": "usr_123abc",
      "property_id": "prop_123",
      "collection_id": "coll_abc123",
      "notes": "Great location, near U-Bahn",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "property": {
        "id": "prop_123",
        "title": "Modern 2-Bedroom Apartment",
        "city": "Berlin",
        "price": 450000,
        "rooms": 2,
        "area_sqm": 75
      },
      "is_available": true
    }
  ],
  "total": 15,
  "unavailable_count": 0
}
```

### Check if Favorited

```http
GET /api/v1/favorites/check/{property_id}
```

Response:
```json
{
  "is_favorited": true,
  "favorite_id": "fav_xyz789",
  "collection_id": "coll_abc123",
  "notes": "Great location"
}
```

### Get All Favorite IDs

```http
GET /api/v1/favorites/ids
```

Response:
```json
["prop_123", "prop_456", "prop_789"]
```

Useful for bulk UI state updates (e.g., heart icons).

### Get Single Favorite

```http
GET /api/v1/favorites/{favorite_id}
```

Response (same structure as list item):
```json
{
  "id": "fav_xyz789",
  "user_id": "usr_123abc",
  "property_id": "prop_123",
  "collection_id": "coll_abc123",
  "notes": "Great location",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "property": { ... },
  "is_available": true
}
```

### Update Favorite

```http
PATCH /api/v1/favorites/{favorite_id}
```

Request body:
```json
{
  "collection_id": "coll_def456",
  "notes": "Updated notes"
}
```

Response:
```json
{
  "id": "fav_xyz789",
  "user_id": "usr_123abc",
  "property_id": "prop_123",
  "collection_id": "coll_def456",
  "notes": "Updated notes",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

### Delete Favorite

```http
DELETE /api/v1/favorites/{favorite_id}
```

Response: 204 No Content

### Delete Favorite by Property ID

```http
DELETE /api/v1/favorites/by-property/{property_id}
```

Response: 204 No Content

### Move Favorite to Collection

```http
POST /api/v1/favorites/{favorite_id}/move/{collection_id}
```

Response:
```json
{
  "id": "fav_xyz789",
  "user_id": "usr_123abc",
  "property_id": "prop_123",
  "collection_id": "coll_def456",
  "notes": "Great location",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

---

## Collections

Organize favorites into themed collections.

### Create Collection

```http
POST /api/v1/collections
```

Request body:
```json
{
  "name": "Apartments under 400k",
  "description": "Affordable options in good locations"
}
```

Response (201 Created):
```json
{
  "id": "coll_abc123",
  "user_id": "usr_123abc",
  "name": "Apartments under 400k",
  "description": "Affordable options in good locations",
  "is_default": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "favorite_count": 0
}
```

### List Collections

```http
GET /api/v1/collections
```

Response:
```json
{
  "items": [
    {
      "id": "coll_abc123",
      "user_id": "usr_123abc",
      "name": "Apartments under 400k",
      "description": "Affordable options",
      "is_default": false,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "favorite_count": 5
    },
    {
      "id": "coll_default",
      "user_id": "usr_123abc",
      "name": "All Favorites",
      "description": "Default collection",
      "is_default": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "favorite_count": 10
    }
  ],
  "total": 2
}
```

### Get or Create Default Collection

```http
GET /api/v1/collections/default
```

Creates a default collection if it doesn't exist.

Response: Same as single collection.

### Get Single Collection

```http
GET /api/v1/collections/{collection_id}
```

Response: Same as list item.

### Update Collection

```http
PUT /api/v1/collections/{collection_id}
```

Request body:
```json
{
  "name": "Updated name",
  "description": "Updated description"
}
```

Response: Updated collection object.

**Note**: Cannot modify `is_default` status.

### Delete Collection

```http
DELETE /api/v1/collections/{collection_id}
```

Response: 204 No Content

**Note**: Cannot delete the default collection. Favorites become uncategorized when collection is deleted.

---

## Saved Searches

Save search queries with alert settings for automatic notifications.

### Create Saved Search

```http
POST /api/v1/saved-searches
```

Request body:
```json
{
  "name": "2-bedroom apartments in Berlin",
  "description": "Looking for affordable 2-bed options",
  "filters": {
    "city": "Berlin",
    "min_rooms": 2,
    "max_rooms": 2,
    "max_price": 400000
  },
  "alert_frequency": "daily",
  "notify_on_new": true,
  "notify_on_price_drop": true
}
```

Response (201 Created):
```json
{
  "id": "search_abc123",
  "user_id": "usr_123abc",
  "name": "2-bedroom apartments in Berlin",
  "description": "Looking for affordable 2-bed options",
  "filters": {
    "city": "Berlin",
    "min_rooms": 2,
    "max_rooms": 2,
    "max_price": 400000
  },
  "alert_frequency": "daily",
  "is_active": true,
  "notify_on_new": true,
  "notify_on_price_drop": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_used_at": null,
  "use_count": 0
}
```

### Alert Frequency Options

| Value | Description |
|-------|-------------|
| `instant` | Immediate notification |
| `daily` | Daily digest |
| `weekly` | Weekly digest |
| `none` | No alerts |

### List Saved Searches

```http
GET /api/v1/saved-searches
```

Query parameters:
- `include_inactive` (optional, default: false): Include paused/disabled searches

Response:
```json
{
  "items": [
    {
      "id": "search_abc123",
      "user_id": "usr_123abc",
      "name": "2-bedroom apartments in Berlin",
      "description": "Looking for affordable 2-bed options",
      "filters": { ... },
      "alert_frequency": "daily",
      "is_active": true,
      "notify_on_new": true,
      "notify_on_price_drop": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "last_used_at": "2024-01-16T08:00:00Z",
      "use_count": 5
    }
  ],
  "total": 3
}
```

### Get Single Saved Search

```http
GET /api/v1/saved-searches/{search_id}
```

Response: Same as list item.

### Update Saved Search

```http
PATCH /api/v1/saved-searches/{search_id}
```

Request body (all fields optional):
```json
{
  "name": "Updated name",
  "filters": {
    "city": "Berlin",
    "min_rooms": 3
  },
  "alert_frequency": "weekly",
  "is_active": false,
  "notify_on_new": false,
  "notify_on_price_drop": true
}
```

Response: Updated saved search object.

### Delete Saved Search

```http
DELETE /api/v1/saved-searches/{search_id}
```

Response: 204 No Content

### Toggle Alert

```http
POST /api/v1/saved-searches/{search_id}/toggle-alert
```

Query parameters:
- `enabled` (optional, default: true): Enable or disable alerts

Response: Updated saved search object.

### Mark Search as Used

```http
POST /api/v1/saved-searches/{search_id}/use
```

Increments the `use_count` counter and updates `last_used_at`.

Response: Updated saved search object.

---

## cURL Examples

### Add property to favorites

```bash
curl -X POST http://localhost:8000/api/v1/favorites \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "prop_123",
    "notes": "Interested in this one"
  }'
```

### List all favorites

```bash
curl -X GET http://localhost:8000/api/v1/favorites \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Create a collection

```bash
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Favorites",
    "description": "Properties I'\''m interested in"
  }'
```

### Create saved search with alerts

```bash
curl -X POST http://localhost:8000/api/v1/saved-searches \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Berlin apartments under 400k",
    "filters": {
      "city": "Berlin",
      "max_price": 400000
    },
    "alert_frequency": "daily",
    "notify_on_new": true,
    "notify_on_price_drop": true
  }'
```

### Toggle saved search alerts

```bash
curl -X POST "http://localhost:8000/api/v1/saved-searches/search_abc123/toggle-alert?enabled=false" \
  -H "Authorization: Bearer $JWT_TOKEN"
```
