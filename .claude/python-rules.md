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
   from typing import Optional

   # 2. Third-party
   import httpx
   import yaml
   from fastapi import FastAPI
   from pydantic import BaseModel

   # 3. Local
   from backend.config.config_loader import load_config
   from backend.modules.jira.client import JiraClient
```

## Type Hints

1. Required on all function parameters and return values.
2. Use `Optional[str]` for optional fields.
3. Use `from typing import Optional, List, Dict, Union` for complex types.

## Docstrings

1. Every module, class, and public function must have a docstring.
2. Default to one-line docstrings: `"""Validate the 8-digit staff ID format."""`
3. Use multi-line only for complex functions that need explanation:
```python
   def submit_story_request(story_input: CreateStoryInput, cfg: BssConfig) -> CreateStoryResponse:
       """
       Orchestrate the full story creation pipeline.

       Args:
           story_input: Validated form input from the user.
           cfg: Loaded application config.

       Returns:
           CreateStoryResponse with jira_issue_key and URL on success.

       Raises:
           JiraClientError: If the Jira API call fails after retries.
       """
```

## Functions

1. Single responsibility — one function does one thing.
2. Keep functions under 50 lines. Split if longer.
3. Use early returns to reduce nesting:
```python
   def _validate_staff_id(staff_id_raw: str) -> ValidationResult:
       if not staff_id_raw:
           return ValidationResult(is_valid=False, error_code="MISSING_STAFF_ID")
       if not staff_id_raw.isdigit():
           return ValidationResult(is_valid=False, error_code="STAFF_ID_NOT_NUMERIC")
       if len(staff_id_raw) != STAFF_ID_LENGTH:
           return ValidationResult(is_valid=False, error_code="INVALID_STAFF_ID_LENGTH")
       return ValidationResult(is_valid=True)
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
       jira_result = await jira_client.create_issue(bss_story_payload)
   except httpx.TimeoutException:
       logger.error("ERROR:create_issue error=timeout")
       raise
   except httpx.HTTPStatusError as exc:
       logger.error(f"ERROR:create_issue error=http_status http_status_code={exc.response.status_code}")
       raise
   except Exception as exc:
       logger.error(f"ERROR:create_issue error={exc}", exc_info=True)
       raise
```
2. Never use bare `except:`.
3. Always use `finally` for timing and guaranteed log markers.

## Async

1. FastAPI endpoint handlers must be `async def`.
2. Use `await` for all `httpx` calls — never use `requests` in async context.
   Using `requests` inside `async def` blocks the event loop and is a production bug.
3. Do not mix sync and async without explicit thread pool delegation (`run_in_executor`).

## Security

1. Never use `eval()` or `exec()` with any user input.
2. Validate and sanitize all inputs before processing.
3. Use parameterized queries if database calls are added.
4. Secrets always from environment variables via `python-dotenv`.

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

1. Always use f-strings: `f"Created issue {jira_issue_key} in {duration_ms}ms"`
2. Never use `%` formatting or `.format()`.

## Performance

1. Use generators for large datasets.
2. Write clear code first — optimize only if needed.
3. Use built-in functions when available: `sum()`, `max()`, `min()`, `any()`, `all()`

## Testing Support

1. Write testable code — keep functions pure (no side effects) where possible.
2. Use dependency injection for external services so they can be mocked in tests.
