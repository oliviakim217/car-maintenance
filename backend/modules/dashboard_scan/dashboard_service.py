"""Dashboard scan service.

Orchestrates image validation and odometer extraction via vision_service.
"""

import logging

from backend.config.config_loader import AppConfig
from backend.modules.dashboard_scan.models import OdometerScanResult
from backend.services.vision_service import extract_odometer_from_image

logger = logging.getLogger(__name__)

_MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png":  [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
}


def _has_valid_magic_bytes(image_bytes: bytes, media_type: str) -> bool:
    """Return True if image_bytes starts with a known signature for media_type."""
    if media_type == "image/heic":
        # HEIC: 4-byte box size + b"ftyp" at offset 4
        return len(image_bytes) >= 12 and image_bytes[4:8] == b"ftyp"
    signatures = _MAGIC_SIGNATURES.get(media_type, [])
    return any(image_bytes.startswith(sig) for sig in signatures)


async def scan_dashboard_image(
    image_bytes: bytes,
    media_type: str,
    cfg: AppConfig,
) -> OdometerScanResult:
    """Validate the uploaded image and extract the odometer reading.

    Args:
        image_bytes: Raw image bytes from the upload.
        media_type: MIME type of the uploaded file.
        cfg: Application configuration.

    Returns:
        OdometerScanResult with extracted_km and a confirmation message.

    Raises:
        ValueError: If the image fails validation or the odometer is unreadable.
        Exception: On unexpected errors from the vision service.
    """
    cfg_scan = cfg.dashboard_scan

    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > cfg_scan.max_image_size_mb:
        raise ValueError(
            f"Image too large: {size_mb:.1f} MB (max {cfg_scan.max_image_size_mb} MB)"
        )

    if media_type not in cfg_scan.allowed_types:
        raise ValueError(
            f"Unsupported image type: {media_type!r}. "
            f"Allowed: {', '.join(sorted(cfg_scan.allowed_types))}"
        )

    if not _has_valid_magic_bytes(image_bytes, media_type):
        raise ValueError(
            f"File content does not match declared type {media_type!r}. "
            "Please upload a genuine JPEG, PNG, HEIC, or WebP image."
        )

    extracted_km = await extract_odometer_from_image(
        image_bytes=image_bytes,
        media_type=media_type,
        model=cfg_scan.model,
    )

    if not (cfg_scan.min_km_plausible <= extracted_km <= cfg_scan.max_km_plausible):
        raise ValueError(
            f"Extracted reading {extracted_km:,} km looks implausible. "
            "Please try a clearer photo or enter manually."
        )

    return OdometerScanResult(
        extracted_km=extracted_km,
        message=f"AI read {extracted_km:,} km from your dashboard.",
    )
