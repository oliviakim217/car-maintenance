---
applyTo: "**/*.py"
---

# Naming Conventions
# Version: 1.0.0

- Do NOT mix cases.

## Functions

1. Use `snake_case`. Functions are verbs or verb phrases.
2. FastAPI endpoint handlers: prefix with `api_`
   - `api_get_mileage()`, `api_post_mileage()`, `api_get_schedule()`
3. Airtable service functions: clean domain names, no `api_` prefix
   - `get_last_mileage_entry()`, `update_task_done()`, `append_maintenance_log()`
4. Internal/private functions: prefix with `_`
   - `_resolve_next_due_date()`, `_get_table()`, `_resolve_base_id()`
5. Service layer orchestrators: verb + noun
   - `get_current_km()`, `get_all_tasks()`, `mark_task_done()`
6. Domain prefixes for grouped functions:
   - `airtable_` — Airtable-related helpers
   - `mileage_` — odometer/mileage business logic
   - `schedule_` — task scheduling logic
   - `cfg_` — config value handling

## Variables

1. Use `snake_case`. Always descriptive — no `data`, `tmp`, `x`, `result`, `obj`.
2. Domain-specific naming:
   - `current_km` not `km`
   - `last_done_km` / `last_done_date`
   - `cfg_weekday_km`, `cfg_due_soon_buffer_km`
   - `env_airtable_token`, `env_app_env`
   - `task_id`, `task_name`, `task_status`
3. Booleans read like conditions: `is_valid`, `has_errors`, `is_never_done`, `is_prod_env`
4. Never shadow Python builtins: `list`, `dict`, `id`, `type`, `input`
5. Use `.get()` for safe dict access: `cfg_value = config_dict.get("key", "default")`
6. IMPORTANT: Do not use generic names. Be specific so that it's easy to maintain and is scalable. Consistency is key.

## Constants

1. `UPPER_CASE_SNAKE_CASE` only.
2. Defined in `constants.py` only — never inline in logic.
3. Examples: `KM_PER_MONTH_WEEKDAY = 10`, `DEFAULT_DUE_SOON_BUFFER_KM = 1000`

## Classes

1. `PascalCase`. Class names are nouns, not verbs.
2. Apply consistent suffixes:
   - `Config` — config models: `AppConfig`, `MileageConfig`, `AirtableConfig`
   - `Result` — computed output models: `TaskResult`
   - `Status` — enums: `TaskStatus`
3. Pydantic models reflect data shape, not behavior.
4. One class = one clear responsibility.

## Files and Modules

1. `snake_case` for all file names.
2. File name reflects the responsibility of its contents:
   - `airtable_service.py`, `schedule_service.py`, `mileage_service.py`, `config_loader.py`
3. No generic names: avoid `helpers.py`, `utils2.py`, `misc.py`

## Environment Variables

1. `UPPER_CASE` with project/service prefix to avoid collisions.
2. Airtable: `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID_DEV`, `AIRTABLE_BASE_ID_PROD`
3. App: `APP_ENV`, `APP_LOG_LEVEL`

## API and JSON Fields

1. Internal Python models: `snake_case`
2. Match external Airtable field names exactly — field names in code must match column names in Airtable.
3. Request/response schemas are explicit — no generic keys like `data` or `result` at the field level.
