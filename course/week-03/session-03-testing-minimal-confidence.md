### Week 3 / Session 3 — Minimal testing for maximum confidence

#### Goal
Add the smallest number of tests that buy you the most confidence.

---

### Why this matters (reasoning)
Tests are not “for coverage”; they’re **risk reducers**.

In backend/platform work, the highest risks are:
- breaking a business rule silently
- changing a query shape and returning wrong data
- introducing authz regressions (Week 4)

So we test **behavior at stable boundaries** (services) and keep the test suite fast.

---

### Theory (must know)

#### What to test
- **Service rules** (business behavior) are high value
- Repository queries: test only tricky filters/joins you might break

#### What not to test (yet)
- FastAPI internals
- SQLAlchemy itself

#### Testing pyramid (tiny version)
- **Unit tests** (fast): service rules with fake repos
- **A few integration tests** (slower): repo queries against a real DB (optional)
- **Manual smoke tests**: `/docs` + curl for end-to-end confidence

---

### Do / Don’t
- **Do**: test behavior, not implementation details
- **Do**: use fake repos for service tests
- **Don’t**: aim for “100% coverage” as a goal

---

### Common failure modes (and solutions)
- **Symptom**: “Tests are flaky or slow.”
  - **Cause**: tests depend on network/real DB for everything.
  - **Solution**: use fake repos for service tests; keep integration tests minimal.
- **Symptom**: “Refactor broke behavior but tests didn’t catch it.”
  - **Cause**: tests assert implementation details rather than behavior.
  - **Solution**: assert outputs, exceptions, and state changes that matter to users.

---

### Practical session
Write 2–4 tests for service invariants using a fake repo.

Reference:
- `course/code/week-03/test_service_example.py`

