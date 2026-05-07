---
description: Bootstrap a new feature module following project conventions. Creates the branch, module folder, service stub, and route stub.
allowed-tools: Read Bash Write Edit Glob
---

Bootstrap a new feature module for the car maintenance app.

The feature name is provided in ARGUMENTS below. If ARGUMENTS is empty, ask the user for the feature name before proceeding.

## Steps

### 1. Read project rules

Read `.claude/rules/scalability-rules.md` so you apply the correct conventions throughout.

### 2. Confirm the plan with the user

State what you are about to create — branch name, files — and ask the user to confirm before writing anything:

- Branch: `feature/<name>`
- `backend/modules/<name>/__init__.py`
- `backend/modules/<name>/<name>_service.py`
- `backend/modules/<name>/models.py` *(ask whether this is needed)*
- `backend/routes/<name>_routes.py`

Wait for confirmation before continuing.

### 3. Create the git branch

```
git checkout -b feature/<name>
```

Fail with a clear message if the branch already exists.

### 4. Create module files

**`backend/modules/<name>/__init__.py`** — empty file.

**`backend/modules/<name>/models.py`** (only if the user confirmed it's needed):

```python
"""Pydantic models for the <name> module."""

from pydantic import BaseModel


# TODO: define your domain models here
```

**`backend/modules/<name>/<name>_service.py`**:

```python
"""<Name> service module.

TODO: describe what this module does.
"""

import logging
import time
from typing import Dict

from backend.config.config_loader import get_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def example_operation() -> Dict:
    """TODO: replace with real operations.

    Returns:
        TODO

    Raises:
        Exception: If the operation fails.
    """
    start_ms = time.monotonic()
    logger.info("BEGIN:example_operation")
    try:
        cfg = get_config()
        # TODO: implement
        result: Dict = {}
        logger.info(
            f"END:example_operation duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        return result
    except Exception as exc:
        logger.error(
            f"ERROR:example_operation error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise
```

**`backend/routes/<name>_routes.py`**:

```python
"""<Name> API routes.

Thin route handlers — all business logic lives in <name>_service.
"""

import logging
import time
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from backend.modules.<name>.<name>_service import example_operation
from backend.utils.auth import require_session
from backend.utils.limiter import limiter
from backend.config.config_loader import get_config

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_session)])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ExampleRequestBody(BaseModel):
    """TODO: define request body fields."""

    model_config = ConfigDict(extra="forbid")

    # TODO: add fields, e.g.:
    # name: str = Field(max_length=100)


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.get("/api/<name>")
@limiter.limit(lambda: f"{get_config().rate_limiting.read_requests_per_minute}/minute")
async def get_<name>(request: Request) -> Dict:
    """TODO: describe what this endpoint returns."""
    start_ms = time.monotonic()
    logger.info("BEGIN:get_<name>")
    try:
        result = example_operation()
        return result
    except Exception as exc:
        logger.error(
            f"ERROR:get_<name> error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
        raise HTTPException(status_code=500, detail="Operation failed")
    finally:
        logger.info(
            f"END:get_<name> duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
```

### 5. Register the router

Read `backend/main.py`. Find the block where other routers are imported and included (look for lines like `from backend.routes.X import router as X_router` and `app.include_router(...)`).

Add the new router in the same style — import it and include it with `app.include_router(...)`.

### 6. Report what was done

List every file created or modified. Then print this checklist for the user:

```
Next steps:
- [ ] Replace example_operation() with real service functions
- [ ] Define your Pydantic request/response models
- [ ] Add any new config values to configs/dev/config.yaml and configs/prod/config.yaml
- [ ] Write tests in tests/ covering happy path, missing fields, and API failure
- [ ] Run the app locally and test your new endpoint
```

ARGUMENTS: {{ARGUMENTS}}
