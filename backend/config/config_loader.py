"""Config loader module.

Loads YAML configuration from configs/{APP_ENV}/config.yaml and exposes a
typed Pydantic model. Implements a singleton so the file is read only once.
"""

import logging
from functools import lru_cache
from typing import Optional

import yaml
from pydantic import BaseModel

from backend.constants import PROJECT_ROOT_PATH
from backend.utils.env_utils import get_required_app_env

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class VehicleConfig(BaseModel):
    """Vehicle identity and baseline mileage/date."""

    year: int
    make: str
    model: str
    initial_km: int
    initial_date: str


class MileageConfig(BaseModel):
    """Mileage estimation and due-soon buffer settings."""

    weekday_km: int
    weekend_km: int
    due_soon_buffer_km: int
    due_soon_buffer_days: int


class AirtableConfig(BaseModel):
    """Airtable table name settings."""

    tasks_table: str
    mileage_table: str
    maintenance_log_table: str


class LoggingConfig(BaseModel):
    """Logging settings."""

    level: str
    retention_days: int


class RateLimitingConfig(BaseModel):
    """Rate limiting thresholds for API endpoints."""

    write_requests_per_minute: int
    read_requests_per_minute: int


class DashboardScanConfig(BaseModel):
    """Dashboard photo scan settings."""

    max_image_size_mb: float
    allowed_types: list[str]
    min_km_plausible: int
    max_km_plausible: int
    model: str


class AppConfig(BaseModel):
    """Root application configuration model."""

    version: int
    vehicle: VehicleConfig
    mileage: MileageConfig
    airtable: AirtableConfig
    logging: LoggingConfig
    rate_limiting: RateLimitingConfig
    dashboard_scan: DashboardScanConfig


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and return the application config as a singleton.

    Reads APP_ENV from the environment (must be explicitly 'dev' or 'prod')
    and loads the corresponding YAML file from configs/{APP_ENV}/config.yaml.

    Returns:
        AppConfig: Parsed and validated application configuration.

    Raises:
        RuntimeError: If APP_ENV is unset or not a recognised environment.
        FileNotFoundError: If the config file does not exist.
        ValueError: If the YAML content fails Pydantic validation.
    """
    app_env = get_required_app_env()
    config_path = PROJECT_ROOT_PATH / "configs" / app_env / "config.yaml"

    logger.info(f"BEGIN:load_config env={app_env} path={config_path}")

    if not config_path.exists():
        logger.error(f"ERROR:load_config error=config file not found path={config_path} duration_ms=0")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            documents = list(yaml.safe_load_all(fh))
            raw = documents[-1]
        config = AppConfig(**raw)
        logger.info(f"END:load_config env={app_env} duration_ms=0")
        return config
    except yaml.YAMLError as exc:
        logger.error(
            "ERROR:load_config error_type=%s message=%s duration_ms=0",
            type(exc).__name__,
            str(exc)[:200],
        )
        raise
    except Exception as exc:
        logger.error(
            "ERROR:load_config error_type=%s message=%s duration_ms=0",
            type(exc).__name__,
            str(exc)[:200],
        )
        raise
