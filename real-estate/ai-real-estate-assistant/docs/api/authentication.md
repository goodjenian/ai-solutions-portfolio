# Authentication

The API supports two authentication methods for different use cases.

## API Key Authentication

Used for backend services, general API access, and most endpoints.

### Headers

```http
X-API-Key: $API_KEY
```

### Configuration

Set your API key in the environment:

```bash
# Single API key
API_ACCESS_KEY=your_secret_key_here

# Multiple API keys (space-separated)
API_ACCESS_KEYS="key1 key2 key3"
```

### Security Features

- Constant-time comparison to prevent timing attacks
- Production safety checks (rejects default keys)
- Audit logging for all auth attempts
- Rate limiting on authentication endpoints

### Verification Endpoint

Check if your API key is valid:

```http
GET /api/v1/verify-auth
X-API-Key: $API_KEY
```

Response:
```json
{
  "message": "Authenticated successfully",
  "valid": true
}
```

### cURL Example

```bash
curl -X GET http://localhost:8000/api/v1/verify-auth \
  -H "X-API-Key: $API_KEY"
```

## JWT Authentication

Used for user-specific features like favorites, saved searches, and collections.

### Configuration

Enable JWT auth in environment:

```bash
AUTH_JWT_ENABLED=true
```

### Endpoints

#### Register

```http
POST /api/v1/auth/register
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

Password requirements:
- At least 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

Response (201 Created):
```json
{
  "access_token": "<YOUR_ACCESS_TOKEN>",
  "refresh_token": "<YOUR_REFRESH_TOKEN>",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "usr_123abc",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false,
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z",
    "last_login_at": null
  }
}
```

Cookies are also set:
- `access_token` (short-lived, HttpOnly)
- `refresh_token` (long-lived, HttpOnly, path-restricted)
- `csrf_token` (for double-submit pattern)

#### Login

```http
POST /api/v1/auth/login
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

Response (200 OK):
```json
{
  "access_token": "<YOUR_ACCESS_TOKEN>",
  "refresh_token": "<YOUR_REFRESH_TOKEN>",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "usr_123abc",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z",
    "last_login_at": "2024-01-15T12:00:00Z"
  }
}
```

**Account Lockout**: After 5 failed login attempts, accounts are temporarily locked (15 minutes). Admins can unlock accounts via `/api/v1/auth/admin/unlock-account`.

#### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <JWT_TOKEN>
```

Response (200 OK):
```json
{
  "id": "usr_123abc",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "role": "user",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login_at": "2024-01-15T12:00:00Z"
}
```

#### Refresh Token

```http
POST /api/v1/auth/refresh
```

Uses the `refresh_token` cookie. Returns new access and refresh tokens.

#### Logout

```http
POST /api/v1/auth/logout
```

Invalidates the refresh token and clears cookies.

### Email Verification

If `AUTH_EMAIL_VERIFICATION_ENABLED=true`, users must verify their email.

#### Resend Verification

```http
POST /api/v1/auth/resend-verification
```

Request body:
```json
{
  "email": "user@example.com"
}
```

#### Verify Email

```http
POST /api/v1/auth/verify-email
```

Request body:
```json
{
  "token": "verification-token-from-email"
}
```

### Password Reset

#### Request Reset

```http
POST /api/v1/auth/forgot-password
```

Request body:
```json
{
  "email": "user@example.com"
}
```

#### Reset Password

```http
POST /api/v1/auth/reset-password
```

Request body:
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass123"
}
```

### OAuth (Google, Apple)

Social login is supported via OAuth 2.0 / OpenID Connect.

#### Google OAuth Start

```http
GET /api/v1/auth/oauth/google
```

Response:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```

#### OAuth Callback

```http
GET /api/v1/auth/oauth/callback?code=...&state=...
```

Handles the OAuth callback and returns tokens.

## Session-based Email Auth

Alternative to JWT for simple email-based authentication.

### Configuration

```bash
AUTH_EMAIL_ENABLED=true
AUTH_CODE_TTL_MINUTES=15
SESSION_TTL_DAYS=7
```

### Request Code

```http
POST /api/v1/auth/request-code
```

Request body:
```json
{
  "email": "user@example.com"
}
```

Response (in development includes code):
```json
{
  "status": "code_sent",
  "code": "123456"  // Only in development
}
```

### Verify Code

```http
POST /api/v1/auth/verify-code
```

Request body:
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

Response:
```json
{
  "session_token": "sess_abc123...",
  "user_email": "user@example.com"
}
```

### Get Session

```http
GET /api/v1/auth/session
X-Session-Token: sess_abc123...
```

## Token Storage Best Practices

### Backend-to-Backend
- Store API keys in environment variables
- Rotate keys periodically
- Never expose keys in client-side code

### Frontend Applications
- Use the JWT with httpOnly cookies when possible
- If storing in memory/localStorage, implement CSRF protection
- Always use HTTPS in production
- Implement proper token refresh logic

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/register | 3 | 60s |
| POST /auth/login | 5 | 60s |
| POST /auth/forgot-password | 3 | 60s |
| POST /auth/resend-verification | 3 | 60s |
