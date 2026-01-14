### Running the course code examples

All runnable snippets live under `course/code/`.

#### Setup (recommended)
From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Week 1 (FastAPI basics)
- In-memory Todo:
  - `python course/code/week-01/todo_inmemory.py`
  - docs: `http://127.0.0.1:8000/docs`
- DI Todo (service + repo):
  - `python course/code/week-01/todo_di.py`
  - docs: `http://127.0.0.1:8000/docs`

#### Week 2 (SQL-first, then SQLAlchemy)
- Raw SQL (SQLite in-memory):
  - `python course/code/week-02/raw_sql_movies.py`
- Schema reference:
  - `course/code/week-02/schema.sql`
- SQLAlchemy ORM mapping:
  - `python course/code/week-02/sqlalchemy_movies_orm.py`
- FastAPI DB dependency example:
  - `python course/code/week-02/fastapi_db_dependency.py`
  - `http://127.0.0.1:8002/health`

#### Week 3 (design + tests)
- Service/repo example:
  - `python course/code/week-03/service_repo_example.py`
- Tests:
  - `pytest -q course/code/week-03/test_service_example.py`

#### Week 4 (authz patterns)
- RBAC dependencies (mock auth):
  - `python course/code/week-04/rbac_deps_example.py`
  - `curl -H 'Authorization: Bearer admin' http://127.0.0.1:8004/admin`
- JWT verification sketch:
  - `python course/code/week-04/jwt_verify_sketch.py`

#### Week 5 (Docker + Compose)
In `course/code/week-05/`:
- Dockerfile example: `Dockerfile.example`
- Compose example: `docker-compose.example.yml`
- App: `app.py` (exposes `/health`)
- Local requirements (for container build context): `requirements.txt`

Run Compose:

```bash
cd course/code/week-05
docker compose -f docker-compose.example.yml up --build
```

Then:
- `http://127.0.0.1:8000/health`

