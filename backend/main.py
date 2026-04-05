"""Car Maintenance Reminder — FastAPI application entry point.

Wires together all routes, serves the frontend template at GET /, and
starts uvicorn on port 8000 when executed directly.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Load .env before anything else so env vars are available during import
load_dotenv()

# ---------------------------------------------------------------------------
# Logging setup (must be configured before importing backend modules)
# ---------------------------------------------------------------------------

_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=_LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(module)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application imports (after dotenv + logging are initialised)
# ---------------------------------------------------------------------------

from backend.config.config_loader import get_config  # noqa: E402
from backend.routes.mileage_routes import router as mileage_router  # noqa: E402
from backend.routes.schedule_routes import router as schedule_router  # noqa: E402

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(_PROJECT_ROOT / "frontend" / "templates"))


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Runs startup tasks (config load) before the app begins accepting requests,
    and handles graceful shutdown afterwards.
    """
    start_ms = time.monotonic()
    logger.info("BEGIN:app_startup")
    try:
        get_config()
        logger.info(
            f"END:app_startup duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    except Exception as exc:
        logger.error(
            f"ERROR:app_startup error={exc} "
            f"duration_ms={int((time.monotonic() - start_ms) * 1000)}"
        )
    yield
    logger.info("END:app_shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Car Maintenance Reminder",
    description="Track and schedule maintenance for your Mazda 3.",
    version="1.0.0",
    lifespan=lifespan,
)

# Serve static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory=str(_PROJECT_ROOT / "frontend" / "static")), name="static")

# Mount routers
app.include_router(schedule_router)
app.include_router(mileage_router)


# ---------------------------------------------------------------------------
# Frontend route
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request) -> HTMLResponse:
    """Serve the main dashboard HTML template.

    Args:
        request: The incoming HTTP request (required by Jinja2).

    Returns:
        HTMLResponse rendering frontend/templates/dashboard.html.
    """
    return templates.TemplateResponse(request, "dashboard.html")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
