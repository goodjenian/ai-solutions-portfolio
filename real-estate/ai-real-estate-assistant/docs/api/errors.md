# Error Handling

## Error Response Format

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

For some endpoints, additional fields may be included:

```json
{
  "detail": "Error message",
  "field": "field_name",
  "code": "ERROR_CODE"
}
```

## HTTP Status Codes

### 2xx - Success

| Code | Description |
|------|-------------|
| 200 OK | Request succeeded |
| 201 Created | Resource created successfully |
| 204 No Content | Request succeeded, no content returned (e.g., DELETE) |

### 4xx - Client Errors

| Code | Description | Common Causes |
|------|-------------|---------------|
| 400 Bad Request | Invalid input | Malformed JSON, validation errors, invalid query parameters |
| 401 Unauthorized | Authentication required | Missing or invalid API key/JWT token |
| 403 Forbidden | Insufficient permissions | Valid auth but insufficient permissions, production misconfiguration |
| 404 Not Found | Resource not found | Invalid ID, resource doesn't exist |
| 409 Conflict | Resource conflict | Duplicate resource, state conflict |
| 413 Payload Too Large | Request too large | File upload exceeds size limit |
| 422 Unprocessable Entity | Semantic errors | Business logic validation failed |
| 423 Locked | Resource locked | Account temporarily locked (too many failed logins) |
| 429 Too Many Requests | Rate limit exceeded | Too many requests in time window |

### 5xx - Server Errors

| Code | Description | Common Causes |
|------|-------------|---------------|
| 500 Internal Server Error | Unexpected error | Unhandled exception, bug in code |
| 503 Service Unavailable | Service offline | Required dependency unavailable (vector store, database) |

## Common Error Scenarios

### Authentication Errors

#### Missing API Key

```http
GET /api/v1/search
X-API-Key: (missing)
```

Response (401):
```json
{
  "detail": "Invalid credentials"
}
```

#### Invalid API Key

```http
GET /api/v1/search
X-API-Key: invalid_key_example
```

Response (403):
```json
{
  "detail": "Invalid credentials"
}
```

#### Production Safety Check

Using default key in production:

Response (403):
```json
{
  "detail": "Invalid credentials"
}
```

Note: Actual log shows `auth_production_misconfig` event.

#### Account Locked

Too many failed login attempts:

Response (423):
```json
{
  "detail": "Account is temporarily locked. Try again in 15 minutes."
}
```

Headers:
```
Retry-After: 900
```

### Validation Errors

#### Missing Required Field

```http
POST /api/v1/search
{
  "query": ""
}
```

Response (400):
```json
{
  "detail": "Question must not be empty"
}
```

#### Invalid Enum Value

```http
POST /api/v1/search
{
  "sort_by": "invalid_field"
}
```

Response (422):
```json
{
  "detail": "Unprocessable entity"
}
```

#### Password Too Weak

```http
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "weak"
}
```

Response (422):
```json
{
  "detail": "Password must be at least 8 characters"
}
```

### Rate Limiting

#### Rate Limit Exceeded

```http
GET /api/v1/search
```

Response (429):
```json
{
  "detail": "Too many requests. Try again in 30s."
}
```

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705320600
Retry-After: 30
```

### Resource Not Found

#### Invalid Property ID

```http
GET /api/v1/market/price-history/invalid_id
```

Response (404):
```json
{
  "detail": "Property not found"
}
```

#### Invalid Favorite ID

```http
GET /api/v1/favorites/invalid_id
```

Response (404):
```json
{
  "detail": "Favorite not found"
}
```

### Conflict Errors

#### Duplicate Favorite

```http
POST /api/v1/favorites
{
  "property_id": "prop_123"
}
```

When already favorited:

Response (409):
```json
{
  "detail": "Property already in favorites"
}
```

#### Email Already Registered

```http
POST /api/v1/auth/register
{
  "email": "existing@example.com",
  "password": "SecurePass123"
}
```

Response (409):
```json
{
  "detail": "Email already registered"
}
```

### Service Unavailable

#### Vector Store Offline

```http
POST /api/v1/search
```

Response (503):
```json
{
  "detail": "Vector store is not available"
}
```

#### Database Offline

```http
GET /api/v1/favorites
```

Response (503):
```json
{
  "detail": "Database connection failed"
}
```

### File Upload Errors

#### File Too Large

```http
POST /api/v1/rag/upload
Content-Type: multipart/form-data
files: [15MB file]
```

Response (413):
```json
{
  "detail": "Upload payload too large",
  "max_total_bytes": 25000000,
  "total_bytes": 15728640
}
```

#### Too Many Files

```http
POST /api/v1/rag/upload
files: [12 files]
```

Response (400):
```json
{
  "detail": "Too many files (max 10)"
}
```

#### Unsupported File Type

```http
POST /api/v1/rag/upload
files: [file.exe]
```

Response (422):
```json
{
  "message": "No documents were indexed",
  "errors": ["file.exe: Unsupported document type"]
}
```

## Error Handling Best Practices

### Client-Side

1. **Always check HTTP status code** before parsing response body
2. **Handle rate limiting** using `Retry-After` header
3. **Exponentially back off** on 5xx errors
4. **Log error details** for debugging
5. **Display user-friendly messages** for common errors

### Example: JavaScript/TypeScript

```typescript
async function apiRequest(url: string, options: RequestInit) {
  const response = await fetch(url, options);

  // Handle rate limiting
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    const delay = retryAfter ? parseInt(retryAfter) * 1000 : 60000;
    await new Promise(resolve => setTimeout(resolve, delay));
    return apiRequest(url, options); // Retry
  }

  // Handle errors
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}

// Usage with error handling
try {
  const result = await apiRequest('/api/v1/search', {
    method: 'POST',
    headers: {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: 'apartments in Berlin' }),
  });
} catch (error) {
  if (error.message.includes('Invalid credentials')) {
    // Handle auth error
  } else if (error.message.includes('Too many requests')) {
    // Handle rate limiting
  } else {
    // Generic error handling
  }
}
```

### Example: Python

```python
import requests
import time

def api_request(url, **kwargs):
    while True:
        response = requests.post(url, **kwargs)

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue

        # Raise for other errors
        response.raise_for_status()
        return response.json()

# Usage
try:
    result = api_request(
        'http://localhost:8000/api/v1/search',
        headers={'X-API-Key': api_key},
        json={'query': 'apartments in Berlin'}
    )
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print('Authentication failed')
    elif e.response.status_code == 429:
        print('Rate limited')
    else:
        print(f'Error: {e.response.json()["detail"]}')
```

## Request ID for Debugging

Every request includes a unique request ID for tracing:

```http
X-Request-ID: req_abc123xyz
```

Include this ID when reporting bugs for faster debugging.

## Logging

On the backend, all errors are logged with:
- Request ID
- Error type
- Error message
- Stack trace (for 5xx errors)
- Relevant context (user ID, endpoint, etc.)

Example log entry:
```json
{
  "event": "auth_invalid_credentials",
  "request_id": "req_abc123",
  "path": "/api/v1/search",
  "method": "POST",
  "key_prefix": "test"
}
```
