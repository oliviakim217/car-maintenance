---
description: Pre-deployment checklist for the car maintenance app. Run this before every docker build and push to Render to catch common mistakes.
allowed-tools: Bash Grep Read
version: "1.1.0"
last-updated: "2026-05-07"
usage: /pre-deploy
triggers: Before every docker build or Render deploy
---

Run each check below and report **PASS** or **FAIL** with a one-line reason. At the end, give an overall verdict: safe to deploy or blockers found.

## Checks

1. **No uncommitted changes** — run `git status`. Fail if any tracked files are modified but not committed.

2. **Branch is intentional** — run `git branch --show-current`. Warn if not on `main`; ask the user to confirm they meant to deploy from the current branch.

3. **render.yaml has no placeholders** — grep render.yaml for `YOUR_DOCKERHUB_USERNAME`. Fail if found.

4. **APP_ENV is not hardcoded to dev** — grep all Python files under `backend/` for the string `"dev"` near `APP_ENV`. Fail if APP_ENV is hardcoded to "dev" anywhere outside of a default= argument.

5. **No secrets in code or YAML** — grep for these high-confidence patterns in Python files and YAML configs. Fail if any match is found outside of `tests/` and comment lines:
   - Airtable PAT: `pat[A-Z0-9]{14,}\.[a-f0-9]{32,}`
   - Bearer token literal: `Bearer\s+[A-Za-z0-9._\-]{20,}`
   - Password assignment: `password\s*=\s*['"][^'"]{8,}['"]` (excluding lines containing `getenv` or `environ`)

6. **Health endpoint exists** — check that `GET /health` is defined in `backend/main.py`.

7. **Dockerfile has non-root USER** — check that the Dockerfile contains a `USER` instruction.

8. **configs/prod/ exists and has a config file** — confirm the prod config is present and not empty.

9. **Tests pass** — run `pytest -q`. Fail on any test failure or if zero tests are collected.

10. **Lint clean** — run `ruff check backend/`. Fail on any error.

11. **Type clean** — run `mypy --strict backend/`. Fail on any error.

12. **Dependency CVEs** — run `pip-audit -r requirements.txt`. Fail on any High or Critical advisory.
