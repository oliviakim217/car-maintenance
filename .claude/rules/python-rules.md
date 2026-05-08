# Python Rules

## Code Style (PEP 8)

1. Indentation: 4 spaces. Never tabs.
2. Line length: 100 characters maximum. No exceptions.
3. Two blank lines between top-level functions and classes.
4. One blank line between methods inside a class.
5. Imports in this order, each group separated by a blank line:
```python
   # 1. Standard library
   import os
   import time
   from dataclasses import dataclass
   from datetime import date

   # 2. Third-party
   import httpx
   import yaml
   from fastapi import FastAPI
   from pydantic import BaseModel

   # 3. Local
   from backend.config.config_loader import get_config
   from backend.services.airtable_service import get_last_mileage_entry
```

## Type Hints

1. Required on all function parameters and return values.
2. This project runs Python 3.12. Use built-in generic types and `|` union syntax — do NOT import
   deprecated aliases from `typing`:
   - `str | None` instead of `Optional[str]`
   - `list[str]` instead of `List[str]`
   - `dict[str, int]` instead of `Dict[str, int]`
   - `str | int` instead of `Union[str, int]`
3. Only import from `typing` for constructs not available as builtins: `TypeVar`, `Protocol`,
   `overload`, `TYPE_CHECKING`, `Annotated`, `Literal`.

## Docstrings

1. Every module, class, and public function must have a docstring.
2. Default to one-line docstrings: `"""Validate the 8-digit staff ID format."""`
3. Use multi-line only for complex functions that need explanation:
```python
   def compute_status(task: dict, current_km: int, current_date: date, cfg: AppConfig) -> TaskResult:
       """
       Compute scheduling status for a single maintenance task.

       Args:
           task: Task dict with fields from the Airtable Tasks table.
           current_km: Current estimated odometer reading in km.
           current_date: Today's date.
           cfg: Loaded application config.

       Returns:
           TaskResult with status, next due km/date, and remaining km/days.

       Raises:
           ValueError: If required task fields are missing or malformed.
       """
```

## Functions

1. Single responsibility — one function does one thing.
2. Keep functions under 50 lines. Split if longer.
3. Use early returns to reduce nesting:
```python
   def add_manual_reading(km: int, reading_date: date) -> None:
       if km <= 0:
           raise ValueError(f"km must be a positive integer, got {km}")
       if reading_date > date.today():
           raise ValueError(f"reading_date cannot be in the future: {reading_date}")
       cfg = get_config()
       add_mileage_entry(cfg.airtable.mileage_table, km, reading_date)
```

## Code Structure

1. **Fail first**: Always handle the failure/guard case first. The success path must be the last branch.
   ```python
   # Correct
   if not condition:
       return error_response(...)
   # ... success logic last

   # Wrong
   if condition:
       # success logic
   else:
       return error_response(...)
   ```
2. This applies to all conditionals: validations, permission checks, missing data, and business rule violations.

## Error Handling

1. Catch specific exceptions first, then `Exception`:
```python
   try:
       record = table.first(sort=["-date"])
   except httpx.TimeoutException:
       logger.error("ERROR:get_last_mileage_entry error=timeout")
       raise
   except httpx.HTTPStatusError as exc:
       logger.error(f"ERROR:get_last_mileage_entry error=http_status status={exc.response.status_code}")
       raise
   except Exception as exc:
       logger.error("ERROR:get_last_mileage_entry error_type=%s message=%s",
                    type(exc).__name__, str(exc)[:200])
       raise
```
2. Never use bare `except:`.
3. Always use `finally` for timing and guaranteed log markers.

## Async

1. FastAPI endpoint handlers must be `async def`.
2. The `requests` library MUST NOT be imported anywhere in `backend/`. Use `httpx` (async client in routes/services, sync client only in `scripts/`).
3. `await` every `httpx` call. Mixing sync and async without `asyncio.to_thread` is a production bug — it blocks the event loop and stalls all concurrent requests.
4. Do not mix sync and async without explicit thread pool delegation (`asyncio.to_thread`).

## Security

1. Never use `eval()` or `exec()` with any user input.
2. Validate and sanitize all inputs before processing.
3. **Airtable formula injection**: never f-string user input into a `formula=` argument. Field names used in formulas come from an allowlist defined in YAML config. Use `pyairtable.formulas.match()` or `EQ()` builders rather than raw string interpolation.
4. Never use `eval()`, `exec()`, `pickle.loads`, `yaml.load` (use `yaml.safe_load`), or `shell=True` in `subprocess`.
5. Secrets always from environment variables via `python-dotenv`.

## Virtual Environment and Dependencies

1. Always use a virtual environment: `python -m venv venv`
2. Pin all dependencies with version ranges in `requirements.txt`.
3. Never commit the `venv/` folder.

## Context Managers

1. Always use `with` for file operations:
```python
   with open(cfg_config_path, "r") as yaml_file_handle:
       cfg_raw = yaml.safe_load(yaml_file_handle)
```

## String Formatting

1. Use f-strings everywhere except in `logger.*` calls.
2. In `logger.*` calls, use `%`-style placeholders — the format string is only evaluated when the log level is active:
   - GOOD: `logger.info("BEGIN:op task_id=%s", task_id)`
   - BAD: `logger.info(f"BEGIN:op task_id={task_id}")`
3. Never use `%` formatting or `.format()` outside `logger.*` calls.

## Performance

1. Use generators for large datasets.
2. Write clear code first — optimize only if needed.
3. Use built-in functions when available: `sum()`, `max()`, `min()`, `any()`, `all()`

## Testing Support

1. Write testable code — keep functions pure (no side effects) where possible.
2. Use dependency injection for external services so they can be mocked in tests.
