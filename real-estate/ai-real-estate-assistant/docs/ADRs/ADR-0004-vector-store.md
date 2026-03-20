# ADR-0004: Vector Store — Chroma (Dev) → pgvector (Prod Option)

## Context
Project requires hybrid retrieval with persistence and geo filters.

## Decision
- Dev: ChromaDB local persist for simplicity.
- Prod option: pgvector on Neon/Supabase for managed persistence.
- Hybrid search remains with keyword + metadata filters + reranking.

## Consequences
- Quick local indexing; predictable dev.
- Managed DB option for scalability and backups.
