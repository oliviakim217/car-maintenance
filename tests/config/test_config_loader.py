"""Tests for backend/config/config_loader.py.

Verifies both real config files (configs/dev, configs/prod) still parse
against AppConfig now that vector_store is a required section.
"""

import pytest
from pydantic import ValidationError

from backend.config.config_loader import AppConfig, get_config


@pytest.mark.parametrize("app_env", ["dev", "prod"])
def test_get_config_loads_vector_store_section(monkeypatch: pytest.MonkeyPatch, app_env: str) -> None:
    monkeypatch.setenv("APP_ENV", app_env)
    get_config.cache_clear()

    cfg = get_config()

    assert isinstance(cfg, AppConfig)
    assert cfg.vector_store.provider == "local_file"


def test_app_config_missing_vector_store_section_raises() -> None:
    config_without_vector_store = {
        "version": 6,
        "vehicle": {
            "year": 2021,
            "make": "Mazda",
            "model": "3",
            "initial_km": 40000,
            "initial_date": "2026-01-01",
        },
        "mileage": {
            "weekday_km": 10,
            "weekend_km": 20,
            "due_soon_buffer_km": 1000,
            "due_soon_buffer_days": 14,
        },
        "airtable": {
            "tasks_table": "Tasks",
            "mileage_table": "Mileage",
            "maintenance_log_table": "MaintenanceLog",
        },
        "logging": {"level": "INFO", "retention_days": 30},
        "rate_limiting": {
            "write_requests_per_minute": 10,
            "read_requests_per_minute": 30,
            "login_requests_per_minute": 5,
            "manual_qa_requests_per_minute": 5,
        },
        "dashboard_scan": {
            "max_image_size_mb": 5.0,
            "allowed_types": ["image/jpeg"],
            "min_km_plausible": 0,
            "max_km_plausible": 999999,
            "model": "claude-haiku-4-5-20251001",
        },
        "manual_qa": {
            "embedding_model": "BAAI/bge-small-en-v1.5",
            "top_k_chunks": 5,
            "model": "claude-haiku-4-5-20251001",
        },
    }

    with pytest.raises(ValidationError):
        AppConfig(**config_without_vector_store)
