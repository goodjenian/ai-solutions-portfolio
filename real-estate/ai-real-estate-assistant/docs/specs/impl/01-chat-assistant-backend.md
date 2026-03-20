# Spec: Chat Assistant (MVP-01)

## 1. Overview

Implement the core backend Chat API with SSE streaming, provider routing, and session management.
This is the "Brain" of the application, handling user queries and routing them to the appropriate LLM provider.

## 2. Architecture

- **Endpoint**: `POST /api/v1/chat`
- **Protocol**: Server-Sent Events (SSE)
- **Framework**: FastAPI (`StreamingResponse`)

### Data Flow

1. User sends message -> `POST /api/v1/chat`
2. Middleware adds `X-Request-ID` (correlation ID)
3. Router selects provider (initially just OpenAI/Mock)
4. Service streams response chunks via SSE
5. Client receives chunks and updates UI

## 3. Requirements

### 3.1 Backend (FastAPI)

- [ ] **Request Model**:
  ```python
  class ChatRequest(BaseModel):
      message: str
      model_id: Optional[str] = "gpt-4o-mini"
      session_id: Optional[str]
  ```
- [ ] **Response Format** (SSE Data):
  ```json
  {"chunk": "Hello", "id": "req_123"}
  {"chunk": " world", "id": "req_123"}
  {"status": "done", "usage": {...}}
  ```
- [ ] **Provider Factory**:
  - Abstract Base Class `LLMProvider`
  - Implement `OpenAIProvider` (using async `openai` sdk)
  - Implement `MockProvider` (for testing, returns dummy stream)
- [ ] **Rate Limiting**:
  - Use `slowapi` or custom dependency
  - Limit: 10 requests/minute per IP for anonymous

### 3.2 Security

- [ ] **API Keys**: Load `OPENAI_API_KEY` from `.env`
- [ ] **Validation**: Reject empty messages
- [ ] **Sanitization**: Basic input cleaning

### 3.3 Testing

- [ ] Unit tests for `LLMProvider` factory
- [ ] Integration test for `/chat` endpoint (using Mock provider)

## 4. Implementation Steps

1. **Setup**: Add `openai`, `slowapi` to `requirements.txt` / `uv`.
2. **Core**: Create `api/v1/chat.py` and `services/llm/`.
3. **Provider**: Implement `MockProvider` first to test connection.
4. **Integration**: Connect `OpenAIProvider`.
5. **API**: Wire up FastAPI route with SSE.

## 5. Verification

- `curl -N -X POST http://localhost:8000/api/v1/chat ...` should stream text.
