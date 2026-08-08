"""Pydantic models for the dashboard scan feature."""

from pydantic import BaseModel, ConfigDict


class OdometerScanResult(BaseModel):
    """Response returned to the frontend after AI reads the dashboard image."""

    model_config = ConfigDict(extra="forbid")

    extracted_km: int
    message: str
