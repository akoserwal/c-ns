### Week 1 — Lab Solution (reference)

#### Goal
Implement the missing endpoints and prove you can explain the request lifecycle.

---

## Reference approach (architecture)
- **Router/endpoints**: HTTP + translation only
- **Service**: business rules
- **Repo**: persistence (in-memory for Week 1)

You can implement this by extending the Week 1 DI example:
- `course/code/week-01/todo_di.py` (starter)

Or use the reference solution file:
- `course/code/week-01/todo_di_solution.py`

---

## Reference implementation (what to add)

### 1) `GET /todos` (list)
- Return all todos as a list.
- Optional filter: query param `q` performs substring match on `title`.

### 2) `DELETE /todos/{id}`
- If exists: delete and return `204 No Content`
- If missing: return `404`

### 3) (Optional) `PUT` and `PATCH`
- `PUT`: replace the title (full update)
- `PATCH`: update only provided fields

---

## Smoke test (solution)

Start the app:

```bash
python course/code/week-01/todo_di_solution.py
```

Create:

```bash
curl -s -X POST http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"buy milk"}'
```

List:

```bash
curl -s http://127.0.0.1:8000/todos
```

Delete (replace `<id>` with returned id):

```bash
curl -i -X DELETE http://127.0.0.1:8000/todos/<id>
```

Verify not found:

```bash
curl -i http://127.0.0.1:8000/todos/<id>
```

Expected:
- delete returns **204**
- get after delete returns **404**

---

## Explanation script (what “good” sounds like)
You should be able to say:
- “FastAPI routes the request to a handler, validates input into a Pydantic model, resolves dependencies (service/repo), then calls service logic. The repo persists state. The handler returns a response model (serialized to JSON). Known failures are translated into HTTP status codes.”

