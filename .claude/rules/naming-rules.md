---
applyTo: "**/*.py"
---

# Naming Conventions
# Version: 2.0.0

- Do NOT mix cases.

## Core Principle: Explicit, Specific, Descriptive

Every name must answer three questions:
- **What domain or service does it belong to?** (prefix)
- **What is it?** (noun for variables/classes, verb for functions)
- **What does it represent specifically?** (no abbreviations, no generics)

If you can move the name into a different module without it looking out of place, it is too generic. Rename it.

---

## External Service Prefix Contract

Every external service or cloud provider gets a dedicated prefix. That prefix is applied
consistently across functions, variables, env vars, config classes, and files.

**Adding a new service = add a row to this table before writing any code.**

| Service              | Python prefix  | Env var prefix  | Config class      | File pattern                     |
|----------------------|---------------|-----------------|-------------------|----------------------------------|
| Airtable             | `airtable_`   | `AIRTABLE_`     | `AirtableConfig`  | `airtable_service.py`            |
| Anthropic (Claude)   | `anthropic_`  | `ANTHROPIC_`    | `AnthropicConfig` | `vision_service.py`              |
| SMTP / Email         | `smtp_`       | `SMTP_`         | `SmtpConfig`      | `email_service.py`               |
| GCP (if added)       | `gcp_`        | `GCP_`          | `GcpConfig`       | `gcp_<feature>_service.py`       |
| AWS (if added)       | `aws_`        | `AWS_`          | `AwsConfig`       | `aws_<feature>_service.py`       |
| Stripe (if added)    | `stripe_`     | `STRIPE_`       | `StripeConfig`    | `stripe_payment_service.py`      |

Rules:
1. No service-specific variable, function, env var, or config class may exist without a matching prefix from this table.
2. When adding a new external service, add a row to this table first.
3. Service client instances must be named `<prefix>_client`:
   - `airtable_client`, `anthropic_client`, `gcp_storage_client`, `aws_s3_client`
4. Service config variables must use the typed Pydantic model or be named `<prefix>_config`:
   - `airtable_config`, `gcp_config`

---

## Functions

1. Use `snake_case`. Functions are verbs or verb phrases.
2. FastAPI endpoint handlers: prefix with `api_`
   - `api_get_mileage()`, `api_post_mileage()`, `api_get_schedule()`, `api_upload_dashboard_photo()`
3. Service functions: use the service prefix from the External Service Prefix Contract
   - Airtable: `get_last_mileage_entry()`, `update_task_done()`, `append_maintenance_log()`
   - Anthropic: `extract_odometer_from_image()`
   - GCP (example): `gcp_upload_receipt_image()`, `gcp_download_config_file()`
   - AWS (example): `aws_send_push_notification()`, `aws_fetch_secret_value()`
4. Internal/private functions: prefix with `_`
   - `_resolve_next_due_date()`, `_get_table()`, `_resolve_base_id()`, `_has_valid_magic_bytes()`
5. Service layer orchestrators: verb + noun, domain-scoped
   - `get_current_km()`, `get_all_tasks()`, `mark_task_done()`, `scan_dashboard_image()`
6. Domain prefixes for grouped helpers:
   - `airtable_` — Airtable-related helpers
   - `mileage_` — odometer/mileage business logic
   - `schedule_` — task scheduling logic
   - `cfg_` — config value handling
   - `gcp_` — GCP helpers (when added)
   - `aws_` — AWS helpers (when added)

---

## Variables

1. Use `snake_case`. Always descriptive.
2. **Banned generic names** — never use these, no exceptions:
   `data`, `tmp`, `x`, `result`, `obj`, `val`, `item`, `record`, `entry`,
   `response`, `client`, `config`, `handler`, `helper`, `manager`, `info`, `payload`
3. Domain-specific naming:
   - `current_km` not `km`
   - `last_done_km` / `last_done_date`
   - `cfg_weekday_km`, `cfg_due_soon_buffer_km`
   - `task_id`, `task_name`, `task_status`
   - `extracted_km`, `image_bytes`, `media_type`
4. Service client variables: `<service>_client`
   - `airtable_client`, `anthropic_client`, `gcp_storage_client`, `aws_s3_client`
5. Env var reads: name the variable after what it holds, with service prefix
   - `airtable_token = os.getenv("AIRTABLE_TOKEN")` — not `token` or `api_token`
   - `anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")` — not `key` or `api_key`
   - `gcp_project_id = os.getenv("GCP_PROJECT_ID")` — not `project_id`
6. Booleans read like conditions: `is_valid`, `has_errors`, `is_never_done`, `is_prod_env`, `is_mobile_device`
7. Never shadow Python builtins: `list`, `dict`, `id`, `type`, `input`, `filter`, `map`
8. Use `.get()` for safe dict access: `cfg_value = config_dict.get("key", "default")`

---

## Constants

1. `UPPER_CASE_SNAKE_CASE` only.
2. Defined in `constants.py` only — never inline in logic.
3. Prefix constants by domain:
   - `KM_PER_MONTH_WEEKDAY = 10`
   - `DEFAULT_DUE_SOON_BUFFER_KM = 1000`
   - `ANTHROPIC_MAX_TOKENS_ODOMETER = 64`
   - `GCP_MAX_UPLOAD_RETRIES = 3` (example, if added)
   - `AWS_S3_PRESIGNED_URL_TTL_SECONDS = 3600` (example, if added)

---

## Classes

1. `PascalCase`. Class names are nouns, not verbs.
2. Apply consistent suffixes:
   - `Config` — config models: `AppConfig`, `MileageConfig`, `AirtableConfig`, `AnthropicConfig`, `GcpConfig`, `AwsConfig`
   - `Result` — computed output models: `TaskResult`, `OdometerScanResult`
   - `Status` — enums: `TaskStatus`
   - `Request` / `Response` — API schema models where the distinction adds clarity
3. Pydantic models reflect data shape, not behavior.
4. One class = one clear responsibility.
5. **Banned generic class names**: `Manager`, `Handler`, `Helper`, `Processor`, `Wrapper`, `Util`
   (unless it is literally a Python base class, in which case prefix with `Base`: `BaseService`)

---

## Files and Modules

1. `snake_case` for all file names.
2. File name reflects the single responsibility of its contents:
   - `airtable_service.py`, `schedule_service.py`, `mileage_service.py`, `config_loader.py`
   - New external service files follow: `<service>_service.py` or `<service>_<feature>_service.py`
     - `gcp_storage_service.py`, `aws_s3_service.py`, `stripe_payment_service.py`
3. **Banned generic file names**: `helpers.py`, `utils2.py`, `misc.py`, `common.py`, `base.py`, `shared.py`

---

## Environment Variables

1. `UPPER_CASE` with service prefix — every env var must be prefixed with its service name.
2. The only unprefixed vars are `APP_*` (application-level settings).
3. **Never use bare names**: `TOKEN`, `KEY`, `SECRET`, `PASSWORD` without a service prefix are banned.
4. Current and planned vars by service:

   | Service   | Variables |
   |-----------|-----------|
   | App       | `APP_ENV`, `APP_LOG_LEVEL`, `APP_PASSWORD`, `APP_HOST` |
   | Airtable  | `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID_DEV`, `AIRTABLE_BASE_ID_PROD` |
   | Anthropic | `ANTHROPIC_API_KEY` |
   | SMTP      | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` |
   | GCP       | `GCP_PROJECT_ID`, `GCP_SERVICE_ACCOUNT_KEY_PATH` |
   | AWS       | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |

---

## API and JSON Fields

1. Internal Python models: `snake_case`
2. Match external service field names exactly — field names in code must match column names in
   Airtable (or field names in any external API response). Never rename or abbreviate.
3. Request/response schemas are explicit — no generic keys like `data`, `result`, `payload`,
   or `info` at the field level.
