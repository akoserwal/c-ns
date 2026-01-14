### Week 5 — Lab Solution (reference)

#### Goal
Ship a reproducible local environment and document how to run and reason about it.

---

## Part A — Dockerize the API (solution)
Use the reference Week 5 app:
- `course/code/week-05/app.py` (exposes `/health` and checks DB with `SELECT 1`)

Reference Dockerfile:
- `course/code/week-05/Dockerfile.example`

Key points:
- install deps from `course/code/week-05/requirements.txt` (build context local)
- run with `uvicorn app:app`

---

## Part B — Compose API + DB (solution)
Reference compose:
- `course/code/week-05/docker-compose.example.yml`

Run it:

```bash
cd course/code/week-05
docker compose -f docker-compose.example.yml up --build
```

Verify:

```bash
curl -s http://127.0.0.1:8000/health
```

Expected:
- `{"ok":true}` (ordering of JSON keys may vary)

---

## Part C — README skeleton (solution)
Use this structure for your project README:

### 1) What is this?
- one paragraph: what service does

### 2) Architecture
- 5–10 bullets:
  - API layer
  - service layer
  - repository layer
  - DB
  - auth (if present)

### 3) Run locally
- prerequisites
- env vars
- `docker compose up --build`
- URLs (`/docs`, `/health`)

### 4) Security model (high-level)
- 401 vs 403 rules
- roles/scopes used
- token issuer/verifier

### 5) Tradeoffs
- what you optimized for
- what you would change in production (K8s, managed DB, secrets)

---

## Part D — “Production sketch” (solution guidance)
Write 6–10 bullets, for example:
- Deploy API as a **Kubernetes Deployment** behind a **Service**
- Store config in **ConfigMaps**, secrets in **Secrets** (or external secrets manager)
- Use **RDS** for Postgres, not a self-hosted DB pod
- Use **AWS IAM roles** for workload AWS access (no static keys)

