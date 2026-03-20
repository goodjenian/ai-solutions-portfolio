# ADR-0000: Architecture Decision Record Template

## Status

[Proposed | Accepted | Deprecated | Superseded]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

## Alternatives Considered

What other options were considered and why were they not chosen?

---

## Example Usage

```markdown
# ADR-0001: Use PostgreSQL for Production Database

## Status

Accepted

## Context

We are currently using SQLite for development, which is not suitable for production:
- No concurrent writes
- No connection pooling
- No replication support
- Data file stored locally

## Decision

We will use PostgreSQL for production deployments with:
- Connection pooling via PgBouncer
- Read replicas for scaling
- Managed service (AWS RDS or similar)

## Consequences

**Positive:**
- Production-ready database
- Horizontal scaling possible
- Better monitoring tools

**Negative:**
- Additional infrastructure cost
- Need to manage migrations (Alembic)
- Slightly more complex local setup

## Alternatives Considered

1. **MySQL**: Good option but less JSON support
2. **MongoDB**: Would require significant schema changes
3. **CockroachDB**: Interesting but overkill for current scale
```
