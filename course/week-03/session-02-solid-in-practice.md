### Week 3 / Session 2 — SOLID in practice (SRP + Dependency Inversion)

#### Goal
Make refactoring decisions using two principles that actually matter day-to-day:
- **SRP** (Single Responsibility)
- **DIP** (Dependency Inversion)

---

### Why this matters (reasoning)
SOLID is often taught as theory. Here we use it as a practical debugging and refactoring tool:
- SRP reduces the number of reasons a file changes → fewer accidental regressions
- DIP makes it easy to test and to swap integrations (DB, Keycloak, external APIs)

If you can apply SRP+DIP, you can ship backend/platform work confidently without cargo-cult patterns.

---

### Theory (only what you will use)

#### SRP (one reason to change)
Ask: “If this changes, how many things break?”
- If the answer is “a lot”, the module is doing too much.

Common SRP smells:
- router knows DB schema details
- repository performs business validation
- service raises `HTTPException`

#### DIP (depend on abstractions)
The service should not care *which* DB you use; it should depend on a repository interface.

```mermaid
flowchart LR
  SVC[Service] -->|depends on| I[Repo Interface]
  SQLA[SQLAlchemy Repo] -->|implements| I
  FAKE[Fake Repo (tests)] -->|implements| I
```

---

### Do / Don’t
- **Do**: define a tiny repository interface (Protocol)
- **Do**: enforce invariants in the service
- **Don’t**: let ORM models leak into API responses
- **Don’t**: over-engineer (interfaces should be small and real)

#### “Lightweight repository” guidance (what good looks like)
- Repos should expose **operations the domain needs**, not generic CRUD of every table.
- Prefer methods like `get_movie_with_genres(movie_id)` over “here’s the Session, good luck”.

---

### Common failure modes (and solutions)
- **Symptom**: “I added an interface but now everything is abstract and confusing.”
  - **Cause**: interface designed before the real needs existed.
  - **Solution**: shrink interfaces to the 2–5 methods the service actually uses.
- **Symptom**: “Service depends on SQLAlchemy models and can’t be tested.”
  - **Cause**: repo boundary isn’t real; ORM leaked into domain.
  - **Solution**: return simple domain objects (dataclasses) or primitives from repos.

---

### Practical session
Implement:
- `MovieRepo` protocol
- `MovieService` that validates business rules
- `SqlAlchemyMovieRepo` and a `FakeMovieRepo` for tests

Reference example code:
- `course/code/week-03/service_repo_example.py`

