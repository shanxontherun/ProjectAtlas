# Architecture Decisions

---

## ADR-001

### Decision

Use SQLite as the primary database.

### Reason

- Simple
- Fast
- Local-first
- Zero maintenance

### Future

SQLite → PostgreSQL

---

## ADR-002

### Decision

Use an Event-Driven Architecture.

### Reason

Departments should communicate through events instead of directly calling each other.

Benefits:

- Loose coupling
- Easy expansion
- Easier debugging

---

## ADR-003

### Decision

Use OmniRoute as the AI Gateway.

### Reason

All AI models are accessed through a single endpoint, allowing model changes without modifying workflows.