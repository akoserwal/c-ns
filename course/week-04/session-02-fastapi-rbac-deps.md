### Week 4 / Session 2 — FastAPI RBAC via dependencies (clean and testable)

#### Goal
Implement authorization checks as reusable dependencies so endpoints stay thin.

---

### Why this matters (reasoning)
Authorization is a *cross-cutting concern*. If you sprinkle checks across endpoints, you will:
- miss checks on new endpoints
- implement inconsistent semantics (401 vs 403)
- create security regressions during refactors

Dependencies let you centralize enforcement and make it reusable and testable.

---

### Architecture diagram

```mermaid
flowchart TB
  Req[HTTP request] --> Auth[Extract + verify token]
  Auth --> P[Principal (subject + roles)]
  P --> Gate[require_role('admin')]
  Gate -->|allowed| Handler[Endpoint handler]
  Gate -->|forbidden| F[403]
  Auth -->|missing/invalid| U[401]
```

---

### Do / Don’t
- **Do**: build a `Principal` object from verified claims
- **Do**: enforce roles/scopes in a dependency, not scattered in handlers
- **Don’t**: call the IdP on every request if you can verify locally (JWT)
- **Don’t**: return different error messages that leak whether a user exists

#### Roles vs scopes (when to use which)
- **Roles**: coarse-grained grouping (“admin”, “billing-admin”)
- **Scopes**: capability labels tied to a client/API (“movies:read”, “movies:write”)

For APIs, scopes often map more directly to permissions. Roles are simpler for the first secure service.

---

### Common failure modes (and solutions)
- **Symptom**: auth checks depend on request body details and get duplicated
  - **Solution**: use a service method for “can user do X on resource Y?” and call it from router after loading the resource.
- **Symptom**: “admin” becomes a universal bypass
  - **Solution**: define explicit permissions, document them, and use least privilege.
- **Symptom**: every endpoint repeats `if role not in roles`
  - **Solution**: encapsulate in `require_role(...)` or `require_any_role(...)`.

---

### Practical session
Work through `rbac_deps_example.py` and extend it:
- Add a `viewer` role
- Add an endpoint that requires either `admin` or `editor`

Code:
- `course/code/week-04/rbac_deps_example.py`

---

### Solution pattern: “any-of” role checks
Most real APIs need “any-of” checks (admin OR editor).

Example shape:

```python
def require_any_role(*roles: str):
    def dep(p: Principal = Depends(get_current_user)) -> Principal:
        if not (p.roles & set(roles)):
            raise HTTPException(status_code=403, detail="forbidden")
        return p
    return dep
```

Use this to keep handlers clean and keep authorization logic consistent.
