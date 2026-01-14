### Week 5 — Lab (self-paced)

#### Goal
Make your project runnable by anyone and document the operational story.

---

### Tasks
- Dockerize your API:
  - build an image
  - run it locally
- Add Docker Compose for local dev:
  - API + DB (Postgres recommended)
  - verify the API works end-to-end
- Write a README that includes:
  - setup steps
  - environment variables
  - how auth works (high-level)
  - key tradeoffs you made

---

### Do / Don’t
- **Do**: keep config in environment variables
- **Do**: add a `.dockerignore`
- **Don’t**: commit secrets to git
- **Don’t**: treat Compose as production

---

### Solution checklist (definition of done)
- A new teammate can run:
  - `docker compose up --build`
  - hit `/health` successfully
- DB connectivity works (health check does a `SELECT 1`)
- README explains:
  - how to run locally (non-interactive, copy/paste)
  - how auth is enforced (401 vs 403, roles/scopes)
  - what would change in production (Kubernetes, managed DB, secrets)

---

### Evidence artifacts
- `README.md` with `docker compose up` instructions
- A short “production sketch”:
  - what would run in Kubernetes (Deployment/Service/Secret/ConfigMap)
  - what would be AWS-managed services (RDS, Secrets Manager, etc.)
