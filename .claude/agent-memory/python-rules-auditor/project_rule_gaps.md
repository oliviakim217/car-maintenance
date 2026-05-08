---
name: Recurring rule gaps
description: Topics the rule set is silent on or only partially covers — flag in audits until added
type: project
---

State as of 2026-05-07 (post-fix audit, second pass):

**Recently resolved (do NOT re-flag):**
- HTTPX timeouts mandated (CLAUDE.md Production §3)
- Logging filter for secrets (CLAUDE.md Logging §10–11)
- `extra="forbid"` on Pydantic models (CLAUDE.md Input Sanitization §6)
- Sync-in-async ban (CLAUDE.md Production §3, python-rules.md Async §3–4)
- pip-audit, ruff, mypy, pytest gates in pre-deploy skill

**Still missing or only partially covered:**

1. Retry/backoff strategy for external API calls — timeouts exist, but no retry policy (`tenacity`, exponential backoff, idempotency).
2. Hash-pinned `requirements.txt` — only "version ranges" required; supply-chain attacks not addressed; no `requirements.lock` or `pip-tools`/`uv pip compile`.
3. Pre-commit hooks — pre-deploy SKILL runs ruff/mypy/pip-audit but nothing prevents bad commits in the first place. No `.pre-commit-config.yaml`, no gitleaks/detect-secrets.
4. Test coverage threshold — pytest is run but no `--cov-fail-under=N`. `tests/` has only `test_data/`.
5. Graceful shutdown / FastAPI lifespan — no rule for `httpx.AsyncClient` lifecycle, signal handling, or in-flight request drain.
6. Async context propagation — no `contextvars` or request-ID correlation rule for structured logs.
7. Datetime handling — no rule mandating timezone-aware `datetime.now(tz=UTC)`; `date.today()` used in examples (locale-dependent).
8. Health vs readiness vs liveness — only `/health` mentioned; no `/ready` distinction; pre-deploy doesn't differentiate.
9. Logging format — JSON formatter not mandated for prod; only "must include timestamp/level/module/message".
10. Rate limiting pattern — referenced (`limiter.limit(...)`) but no rule defines the storage backend (in-memory vs Redis), per-IP vs per-session, or 429 response shape.
11. Dependency injection enforcement — rule says "use DI" but no concrete pattern (FastAPI `Depends`, factory functions, no module-level singletons).
12. Pydantic v2 details beyond `extra="forbid"` — no rule on `StrictStr`/`StrictInt`, `Annotated[..., Field(...)]`, `model_validator(mode="after")`.
13. Constants module location — naming-rules says "Defined in `constants.py` only" but doesn't specify where (per-module? `backend/utils/constants.py`?).
14. Function-length rule conflict potential — python-rules §Functions §2 caps at 50 lines, but no exemption for route handlers with try/except/finally boilerplate (the new-feature SKILL stub itself is ~25 lines and only contains a try/except/finally — real handlers will exceed 50).
15. `Annotated` / `Depends` discipline — Python 3.12 supports `Annotated[X, Depends(...)]` but rules don't specify it.
16. CORS / TrustedHost / security headers — no rule mandates middleware (CORS, HSTS, CSP).
17. Container/Docker rules — pre-deploy checks for non-root USER, but no rule about pinned base images, multi-stage builds, or `.dockerignore`.

**Why:** A junior dev or LLM following the existing rules verbatim still produces code without retries, without hash-pinned deps, without coverage gates, with naive datetime, and without graceful shutdown.

**How to apply:** Every audit should re-check whether each of the above has been added; mark as 🟢 Addition until then. If items 1–4 stay open after another fix cycle, escalate them as 🔴 because production exposure compounds.
