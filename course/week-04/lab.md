### Week 4 — Lab (self-paced)

#### Goal
Secure your API and be able to explain the trust flow.

---

### Tasks
- Add authentication + authorization to your service:
  - protect at least 2 endpoints
  - implement at least 2 roles (e.g., `admin`, `user`)
  - correct `401` vs `403` behavior
- Write a short “trust narrative”:
  - who issues the token?
  - who verifies it?
  - what claims do you rely on (roles/scopes)?
  - what happens on expiry?

---

### Do / Don’t
- **Do**: default-deny (new endpoints should not be public by accident)
- **Do**: validate issuer/audience/expiry for JWTs
- **Don’t**: treat “decoded token” as “verified token”
- **Don’t**: implement authorization only in the UI

---

### Solution checklist (definition of done)
- Missing token → `401`
- Invalid token → `401`
- Valid token, missing role → `403`
- Valid token, correct role → `200`
- You can demonstrate with curl:
  - one success path
  - one 401 path
  - one 403 path

---

### Evidence artifacts (career-useful)
Create a `SECURITY.md` that includes:
- a trust diagram (mermaid is fine)
- role definitions and what each role can do
- example curl calls for 200/401/403
- tradeoffs you made (JWT vs session, roles vs scopes)
