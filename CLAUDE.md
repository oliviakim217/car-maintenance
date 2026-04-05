# Rules — Car Maintenance Project

@.claude/python-rules.md

## Progressive Disclosure

Task- and topic-specific instructions live in `.claude/` as separate files. Before starting work,
decide which files below are relevant to the task and read them. Do not read files that are not
relevant.

| File | When to read |
|------|--------------|
| `.claude/python-rules.md` | Any time you write or modify Python code |

## General

1. Always follow programming best practices.
2. Write code with production in mind at all times.
3. Think in layers — separate concerns: data, business logic, presentation.
4. Always validate inputs. Never trust data from the user or an external API.
5. Apply a ceiling to anything that can grow infinitely:
   - Log files must be rotated or deleted after a configured retention period.
   - API rate limiting must be enforced via config.
6. Code must work in both `dev` and `prod` environments.
7. Use GitHub for version control. Write meaningful commit messages.

## Production Considerations

1. **Error Handling**: Handle all errors gracefully. No unhandled exceptions that crash the app.
2. **Security**: No credentials, URLs, or secrets in code. Use environment variables.
3. **Performance**: No infinite loops. Handle timeouts. Avoid blocking calls in async context.
4. **Monitoring**: Log all important operations, errors, and durations.
5. **Reliability**: Handle edge cases, network failures, missing config, unexpected inputs.
6. **Scalability**: Adding a new feature should not require rewriting existing modules.
7. **Documentation**: Every module has a docstring explaining its purpose.

## Logging

1. Use Python's `logging` module only. Never use `print()`.
2. Log level controlled by `APP_LOG_LEVEL` environment variable. Default: `INFO`.
3. Log format must include: timestamp, log level, module name, message.
4. Use structured key=value pairs in messages: `task=oil_change status=due mileage=40000`
5. Required markers for all endpoint and external API operations:
   - `logger.info("BEGIN:<operation> <context key=value>")`
   - `logger.info("END:<operation> duration_ms=<ms>")`
   - `logger.error("ERROR:<operation> error=<message> duration_ms=<ms>")`
6. `END:` and `ERROR:` must be inside a `finally` block — they must always execute.
7. Always measure and log `duration_ms` for any external API call.
8. NEVER log: passwords, API tokens, Authorization headers, secrets, full payloads.
9. Log retention period must come from config — never hardcoded.

## Error Handling

1. Always use `try/except` for any I/O, network call, or file operation.
2. Catch specific exceptions first, then `Exception` as fallback.
3. Never expose internal error details (stack traces, system paths) in API responses.
4. Return a meaningful, user-safe error message in the standard response envelope.
5. Use `finally` blocks for cleanup and guaranteed logging.

## Validation Pipeline (non-negotiable order)

```
Receive Input → Pydantic Validation → SQL Injection Check → Business Validation →
Transform → Enrich → Call External API → Build Response
```

Never skip or reorder these stages.

## SQL Injection Prevention

1. **Never** interpolate user input directly into SQL strings.
2. Always use parameterized queries / prepared statements:
   ```python
   # Correct
   cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

   # Wrong
   cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
   ```
3. Reject any input containing SQL meta-characters (`'`, `"`, `;`, `--`, `/*`, `*/`, `xp_`, `UNION`, `DROP`, etc.) before it reaches the query layer.
4. Use an allowlist for dynamic identifiers (table/column names) — never build them from raw input.
5. Apply this check in the **Validation Pipeline** immediately after Pydantic validation, before any business logic.

## Config Files

1. Use YAML for all application config.
2. YAML data files live in `configs/dev/` or `configs/prod/` at the project root.
3. The Python module that reads YAML lives in `backend/config/config_loader.py`.
   These are two different things — do not confuse them.
4. Every config file must have a `version` field. Increment when the schema changes.
5. Environment is selected by `APP_ENV` env var — never hardcoded.
6. Business rules, field mappings, dropdown values → YAML config.
7. Credentials, secrets, URLs → `.env` file only. Never in YAML.

## Version Control

1. **Adding New Features or Fixing Bugs** — When you work on a new feature or bug, create a git branch first. Then work on changes in that branch for the remainder of the session.
2. **Branch Naming** — Use prefixes to identify branch purpose: `feature/`, `bugfix/`, `hotfix/`, `chore/`. Example: `feature/maintenance-reminders` or `bugfix/mileage-validation`.
3. **Branch from Latest** — Always pull the latest `main` before creating a new branch to avoid unnecessary merge conflicts.
4. **Atomic Commits** — Each commit should represent one logical change. Do not bundle unrelated changes in a single commit.
5. **Commit Messages** — Write meaningful commit messages in imperative mood. Example: `Add oil change reminder logic` not `stuff` or `changes`.
6. **Never Commit Secrets** — `.env` must never be committed. Confirm `.gitignore` includes `.env` before the first commit on any new branch.
7. **Merge via Pull Request** — Do not push directly to `main`. All changes must go through a pull request and be reviewed before merging.

## Testing

1. Test data goes in `tests/test_data/`. Use realistic but fake data.
2. Always test: happy path, missing fields, invalid formats, API failure/timeout, edge cases.
3. Code must be testable without modifying `backend/main.py`.
4. Use dependency injection so external clients (Excel) can be mocked.

## Project Structure

```
project-root/
├── backend/
│   ├── config/          # Config loaders (config_loader.py)
│   ├── modules/         # One sub-folder per feature/domain (e.g. auth/, billing/)
│   ├── routes/          # Route/endpoint definitions only — no business logic here
│   ├── services/        # Cross-cutting services (email, storage, external APIs)
│   └── utils/           # Shared helpers with no business logic
├── configs/
│   ├── dev/             # YAML config files for dev environment
│   └── prod/            # YAML config files for prod environment
├── backend/
│   └── main.py          # Entry point — wiring only, no business logic
├── tests/
│   └── test_data/
└── .env                 # Secrets and credentials only — never commit
```

### Structure Rules

1. **One module per domain.** Each feature lives in its own folder under `backend/modules/`. Adding a new feature must not touch existing modules.
2. **Routes are thin.** Route files only parse the request and call a service or module function. No business logic in routes.
3. **Config-driven by default.** Business rules, field mappings, toggle flags, dropdown values, limits, and thresholds belong in YAML config — not hardcoded in Python.
4. **Config controls behavior.** If a business rule might ever change, it goes in config. Code should read the value; it should never own the value.
5. **Environment separation is mandatory.** `configs/dev/` and `configs/prod/` are separate. Environment is selected by `APP_ENV` — never hardcoded.
6. **`backend/main.py` is wiring only.** It registers routes and starts the server. No logic, no config reading, no direct DB calls.
7. **Shared code goes in `utils/`.** If two modules need the same helper, it moves to `utils/` — not copy-pasted.
