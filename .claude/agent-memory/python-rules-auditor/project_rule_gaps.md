---
name: Recurring rule gaps
description: Topics that the rule set is silent on as of 2026-05-07 — flag in audits until added
type: project
---

As of 2026-05-07 the rule set has no guidance on:

1. Pydantic v2 specifics (`extra='forbid'`, `model_config = ConfigDict(...)`, `@field_validator`, `Field(strip_whitespace=True)`, `StrictStr`/`StrictInt`)
2. HTTPX timeouts and retries — no rule mandates `httpx.Timeout(...)` or backoff for Airtable calls
3. Dependency security — no `pip-audit`, no hash-pinned `requirements.txt`, no Dependabot/Renovate
4. Secret scanning / pre-commit hooks (gitleaks, detect-secrets, ruff, mypy, black)
5. Test coverage threshold — `tests/` only contains `test_data/`, zero actual test files; no minimum coverage rule
6. Graceful shutdown for FastAPI (lifespan handler, `httpx.AsyncClient` lifecycle)
7. Async context propagation (`contextvars`, request IDs, structured logging correlation)
8. Datetime handling (timezone-aware `datetime`, `date.today()` vs `datetime.now(UTC)`)
9. Health vs readiness vs liveness probe distinction (only `/health` is mentioned)
10. Logging format details — rule says "must include timestamp, level, module, message" but doesn't mandate JSON for prod or specify the formatter

**Why:** A junior dev or LLM following the existing rules verbatim would still produce code with no timeouts, no retries, no tests, and unstructured logs.

**How to apply:** Every audit should re-check whether each of these has been added; mark as 🟢 Addition until then.
