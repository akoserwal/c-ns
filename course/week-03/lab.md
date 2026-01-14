### Week 3 — Lab (self-paced)

#### Goal
Refactor your Week 2 project into a clean architecture you can explain.

---

### Tasks
- Create a `MovieService` and move business rules there:
  - year validation (e.g., >= 1888)
  - title normalization (strip whitespace)
  - uniqueness strategy (service check + DB constraint)
- Create repositories responsible for SQLAlchemy:
  - `create_movie`
  - `get_movie`
  - `list_movies_with_genres` (join)
- Keep FastAPI router thin:
  - parse + validate request
  - call service
  - translate known errors into HTTP status codes

---

### Do / Don’t
- **Do**: keep domain/service framework-free (no FastAPI imports)
- **Do**: treat repositories as the only layer that “speaks SQLAlchemy”
- **Don’t**: pass raw Sessions into services
- **Don’t**: return ORM entities directly from endpoints

---

### Solution checklist (definition of done)
- Codebase has clear boundaries:
  - API layer contains request/response schemas + HTTP translation
  - Domain layer contains rules + domain errors
  - Infra layer contains SQLAlchemy + repositories
- Behavior is covered by tests:
  - 2–4 service tests using a fake repo
  - optional: 1–2 repository tests for a join query
- You can explain:
  - why services exist (rules + invariants)
  - why repositories exist (persistence seam)
  - where transactions are committed/rolled back

---

### Evidence artifacts
- `ARCHITECTURE.md`: boundaries + why you chose them
- A short “decision log” (bullets are fine):
  - what you moved out of routers
  - what invariants you enforced
  - what tradeoffs you made (speed vs simplicity)
