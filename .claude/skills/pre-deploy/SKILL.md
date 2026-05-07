---
description: Pre-deployment checklist for the car maintenance app. Run this before every docker build and push to Render to catch common mistakes.
allowed-tools: Bash Grep Read
---

Run each check below and report **PASS** or **FAIL** with a one-line reason. At the end, give an overall verdict: safe to deploy or blockers found.

## Checks

1. **No uncommitted changes** — run `git status`. Fail if any tracked files are modified but not committed.

2. **Branch is intentional** — run `git branch --show-current`. Warn if not on `main`; ask the user to confirm they meant to deploy from the current branch.

3. **render.yaml has no placeholders** — grep render.yaml for `YOUR_DOCKERHUB_USERNAME`. Fail if found.

4. **APP_ENV is not hardcoded to dev** — grep all Python files under `backend/` for the string `"dev"` near `APP_ENV`. Fail if APP_ENV is hardcoded to "dev" anywhere outside of a default= argument.

5. **No secrets in code or YAML** — grep Python files and YAML configs for patterns like `pat`, `Bearer`, `password`, `secret` as literal string values (not env var reads). Fail if any are found.

6. **Health endpoint exists** — check that `GET /health` is defined in `backend/main.py`.

7. **Dockerfile has non-root USER** — check that the Dockerfile contains a `USER` instruction.

8. **configs/prod/ exists and has a config file** — confirm the prod config is present and not empty.
