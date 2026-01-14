### Week 1 — Lab (self-paced)

#### Goal
Ship a tiny API that you can explain end-to-end.

---

### Tasks
- Add endpoints:
  - `GET /todos` (list)
  - `DELETE /todos/{id}` (delete)
  - Optional: filtering by `title` substring
- Add consistent error handling:
  - `404` for missing Todo
  - `400` for invalid payload (or accept FastAPI default `422` and document it)
- Write a short explanation (1 page max):
  - “What happens from curl → response?”
  - “Where does business logic live?”

---

### Do / Don’t
- **Do**: keep route handlers thin (transport adapters)
- **Do**: keep domain/service logic framework-free
- **Don’t**: add a DB yet (Week 2 is SQL-first)

---

### Solution checklist (definition of done)
- `POST /todos` returns `201` and the created todo
- `GET /todos/{id}` returns `200` for existing and `404` for missing
- `GET /todos` returns a list (even if empty)
- `DELETE /todos/{id}` returns `204` for existing and `404` for missing
- Input validation errors return `400` (or `422`, documented)
- You can explain in 60 seconds:
  - where validation happens
  - where business logic lives
  - where persistence lives

---

### Expected smoke test (example)
Using `/docs` or curl, you can:
- create a todo
- fetch it by id
- list todos
- delete it
- verify fetching by id now returns 404

---

### Evidence artifact (for resume later)
- Screenshot/note: “Demo: created + listed + deleted todos”
- A short `ARCHITECTURE.md` note describing layers and decisions
