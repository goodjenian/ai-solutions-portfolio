# Request Flow

This document describes the complete request flow through the AI Real Estate Assistant system.

## Overview

The request flow follows this pattern:

```
User Browser -> Next.js Frontend -> API Proxy -> FastAPI Backend -> Query Analysis -> Processing -> Response
```

## Complete Request Flow Diagram

```mermaid
sequenceDiagram
    participant U as User Browser
    participant N as Next.js Frontend
    participant P as API Proxy
    participant F as FastAPI Backend
    participant Q as QueryAnalyzer
    participant H as HybridAgent
    participant R as RAG Chain
    participant T as Tool Agent
    participant V as ChromaDB
    participant L as LLM Provider

    U->>N: User submits query
    N->>P: POST /api/v1/chat
    P->>F: Forward with X-API-Key
    F->>F: Validate API Key

    alt API Key Valid
        F->>Q: Analyze query
        Q->>Q: Classify intent & complexity

        alt Simple Query (RAG-only)
            Q-->>H: Route to RAG
            H->>R: Execute RAG chain
            R->>V: Vector search
            V-->>R: Relevant documents
            R->>L: Generate answer
            L-->>R: LLM response
            R-->>H: Answer + sources
            H-->>F: Response

        else Complex Query (Agent + Tools)
            Q-->>H: Route to Agent
            H->>T: Execute tool agent
            T->>V: Get property context
            V-->>T: Property data
            T->>T: Select tools (calc/compare)
            T->>L: Execute tools + generate
            L-->>T: Tool results
            T-->>H: Answer + intermediate steps
            H-->>F: Response

        else Medium Query (Hybrid)
            Q-->>H: Route to Hybrid
            H->>R: Get RAG baseline
            R-->>H: Context from RAG
            H->>T: Enhance with tools
            T-->>H: Enhanced answer
            H-->>F: Response
        end

        F-->>P: JSON or SSE Stream
        P-->>N: Response
        N-->>U: Display result
    else API Key Invalid
        F-->>P: 401 Unauthorized
        P-->>N: Error
        N-->>U: Login prompt
    end
```

## Query Routing Logic

The `QueryAnalyzer` class determines the optimal processing strategy:

```mermaid
flowchart TD
    A[User Query] --> B{Analyze Intent}

    B -->|Simple Retrieval| C[RAG-only]
    B -->|Filtered Search| D{Has Filters?}
    B -->|Comparison| E[Tool Agent + Comparator]
    B -->|Calculation| F[Tool Agent + Calculator]
    B -->|Analysis| G[Tool Agent + Python Code]
    B -->|Recommendation| H[Hybrid: RAG + Agent]

    D -->|Yes| I[RAG with Filters]
    D -->|No| C

    C --> J[Direct RAG Chain]
    E --> K[Agent with Context]
    F --> K
    G --> K
    H --> L[Two-phase: RAG then Agent]
    I --> J

    J --> M[Response]
    K --> M
    L --> M

    style C fill:#90EE90
    style I fill:#90EE90
    style J fill:#90EE90
    style E fill:#FFB6C1
    style F fill:#FFB6C1
    style G fill:#FFB6C1
    style K fill:#FFB6C1
    style H fill:#FFE4B5
    style L fill:#FFE4B5
```

## API Endpoint Flows

### Chat Endpoint (`/api/v1/chat`)

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Router
    participant Agent
    participant LLM

    Client->>Proxy: POST /api/v1/chat
    Proxy->>Proxy: Inject X-API-Key
    Proxy->>Router: POST /api/v1/chat
    Router->>Router: Validate API Key
    Router->>Agent: Process query
    Agent->>Agent: Analyze query
    Agent->>LLM: Generate response

    alt Streaming Enabled
        LLM-->>Agent: Stream chunks
        Agent-->>Router: SSE events
        Router-->>Client: text/event-stream
    else Streaming Disabled
        LLM-->>Agent: Full response
        Agent-->>Router: JSON response
        Router-->>Client: application/json
    end
```

### Search Endpoint (`/api/v1/search`)

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant VectorStore
    participant ChromaDB

    Client->>Router: POST /api/v1/search
    Router->>Router: Extract filters
    Router->>VectorStore: search_with_filters()
    VectorStore->>ChromaDB: Hybrid query

    ChromaDB->>ChromaDB: Vector search
    ChromaDB->>ChromaDB: BM25 keyword search
    ChromaDB->>ChromaDB: Reciprocal Rank Fusion
    ChromaDB-->>VectorStore: Ranked results

    VectorStore-->>Router: Property list
    Router-->>Client: JSON response
```

## Frontend API Proxy Pattern

The frontend uses an API proxy to keep credentials server-side:

```mermaid
graph LR
    A[Browser] -->|No credentials| B[Next.js API Route]
    B -->|X-API-Key injected| C[FastAPI Backend]
    C -->|Response| B
    B -->|Clean response| A

    style B fill:#FFE4B5
    style C fill:#90EE90
```

**File**: `apps/web/src/app/api/v1/[...path]/route.ts`

## Streaming Response Flow

For real-time chat responses, the system uses Server-Sent Events:

```mermaid
sequenceDiagram
    participant Client
    participant Backend

    Client->>Backend: GET /api/v1/chat/stream
    Backend-->>Client: 200 OK text/event-stream

    loop For each token
        Backend-->>Client: data: {"content": "token"}
    end

    Backend-->>Client: data: {"meta": {"sources": [...]}}
    Backend-->>Client: data: [DONE]
```

## Error Handling Flow

```mermaid
flowchart TD
    A[Request Received] --> B{Validate API Key}
    B -->|Invalid| Z[401 Unauthorized]
    B -->|Valid| C{Parse Request}

    C -->|Invalid JSON| Y[400 Bad Request]
    C -->|Valid| D{Initialize LLM}

    D -->|Failure| X[503 Service Unavailable]
    D -->|Success| E{Process Query}

    E -->|LLM Error| W[500 Internal Error]
    E -->|Success| F[Return Response]

    style Z fill:#FFB6C1
    style Y fill:#FFB6C1
    style X fill:#FFB6C1
    style W fill:#FFB6C1
    style F fill:#90EE90
```

## Request State Management

Each request is tracked with:

1. **Request ID**: Unique identifier for tracing
2. **Audit Log**: All auth events logged
3. **Timing**: Request duration tracking
4. **Response Meta**: Sources, method used, intent

### Response Structure

```typescript
interface ChatResponse {
  answer: string;
  source_documents: Document[];
  method: 'rag' | 'agent' | 'hybrid' | 'web_search';
  intent: string;
  intermediate_steps?: any[];
  analysis?: QueryAnalysis;
}
```

## Performance Considerations

| Operation | Typical Latency | Optimization |
|-----------|-----------------|--------------|
| API Key Validation | < 5ms | Constant-time comparison |
| Query Analysis | < 10ms | Heuristic-based (no LLM) |
| Vector Search | 50-200ms | ChromaDB caching |
| RAG Generation | 1-3s | Streaming enabled |
| Tool Agent | 2-5s | Parallel tool execution |
