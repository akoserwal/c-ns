### Week 3 — Lab Solution (reference)

#### Goal
Refactor the Week 2 work into a clean, explainable architecture and add a minimal test suite.

---

## Target structure (solution)
Use this as a reference (adjust names as you like):

```text
app/
  api/
    routers/
      movies.py
    deps.py
    schemas.py
  domain/
    errors.py
    services/
      movies.py
    models/
      movie.py
  infra/
    db.py
    repositories/
      movies_sqlalchemy.py
tests/
  test_movie_service.py
```

---

## Boundary rules (solution)
- **api/**
  - owns HTTP status codes and translation
  - parses/validates request payloads
  - calls services
- **domain/**
  - owns business rules and invariants
  - defines domain exceptions (e.g., `MovieNotFound`, `InvalidMovieYear`)
- **infra/**
  - owns SQLAlchemy session + repository implementation
  - never raises `HTTPException` (raise domain/persistence errors only)

---

## Concrete “move this out of routers” list
Move these into `MovieService`:
- year validation (`>= 1888`)
- stripping/normalizing titles
- “already exists” checks (optionally; DB unique constraint is still required)

Move these into `MovieRepository`:
- `INSERT` / `SELECT`
- join queries for “movies with genres”

Routers should do:
- map `MovieNotFound` → 404
- map `MovieAlreadyExists` → 409
- map `InvalidMovieYear` → 400

---

## Tests (solution)

### Service tests (fake repo)
Use the Week 3 example as the blueprint:
- `course/code/week-03/test_service_example.py`

Minimum recommended tests:
- valid create works
- empty title rejected
- invalid year rejected
- not found raises domain error

### Repository tests (optional)
Only add if you have tricky joins.
Keep the number low (1–2 tests).

---

## “Definition of done” (solution)
You are done when:
- another engineer can find “where rules live” in 2 minutes
- your service layer can be tested without FastAPI
- you can explain where the transaction commits (repo vs service) and why

