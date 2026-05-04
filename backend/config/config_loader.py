"""Config loader module.

Loads YAML configuration from configs/{APP_ENV}/config.yaml and exposes a
typed Pydantic model. Implements a singleton so the file is read only once.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

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


class AppConfig(BaseModel):
    """Root application configuration model."""

    version: int
    vehicle: VehicleConfig
    mileage: MileageConfig
    airtable: AirtableConfig
    logging: LoggingConfig


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and return the application config as a singleton.

    Reads APP_ENV from the environment (default: 'dev') and loads the
    corresponding YAML file from configs/{APP_ENV}/config.yaml.

    Returns:
        AppConfig: Parsed and validated application configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the YAML content fails Pydantic validation.
    """
    app_env = os.getenv("APP_ENV", "dev")
    config_path = _PROJECT_ROOT / "configs" / app_env / "config.yaml"

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
        logger.error(f"ERROR:load_config error=yaml parse failed detail={exc} duration_ms=0")
        raise
    except Exception as exc:
        logger.error(f"ERROR:load_config error={exc} duration_ms=0")
        raise
