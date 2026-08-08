"""Dashboard scan routes.

Accepts a dashboard photo upload and returns the AI-extracted odometer reading.
Saving is handled by the existing POST /api/mileage endpoint after user confirmation.
"""

import logging
import time

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.config.config_loader import get_config
from backend.modules.dashboard_scan.dashboard_scan_service import scan_dashboard_image
from backend.modules.dashboard_scan.models import OdometerScanResult
from backend.utils.auth import require_session
from backend.utils.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_session)])


@router.post("/api/dashboard/upload", response_model=OdometerScanResult)
@limiter.limit(lambda: f"{get_config().rate_limiting.write_requests_per_minute}/minute")
async def api_upload_dashboard_photo(
    request: Request,
    file: UploadFile = File(...),
) -> OdometerScanResult:
    """Accept a dashboard photo and return the AI-extracted odometer reading.

    The reading is NOT saved here — the frontend shows it to the user for
    confirmation, then calls POST /api/mileage to persist it.

    Args:
        file: Uploaded image file (JPEG, PNG, HEIC, or WebP).

    Returns:
        OdometerScanResult with extracted_km and a confirmation message.
    """
    start_ms = time.monotonic()
    safe_content_type = (file.content_type or "")[:128]
    logger.info("BEGIN:api_upload_dashboard_photo content_type=%s", safe_content_type)
    try:
        cfg = get_config()
        max_read_bytes = int(cfg.dashboard_scan.max_image_size_mb * 1024 * 1024) + 1
        image_bytes = await file.read(max_read_bytes)
        if len(image_bytes) == max_read_bytes:
            raise ValueError(f"Image too large (max {cfg.dashboard_scan.max_image_size_mb} MB)")
        media_type = file.content_type or "application/octet-stream"
        result = await scan_dashboard_image(
            image_bytes=image_bytes,
            media_type=media_type,
            cfg=cfg,
        )
        return result
    except ValueError as exc:
        logger.error(
            "ERROR:api_upload_dashboard_photo error_type=ValueError message=%s duration_ms=%d",
            str(exc)[:200],
            int((time.monotonic() - start_ms) * 1000),
        )
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(
            "ERROR:api_upload_dashboard_photo error_type=%s message=%s duration_ms=%d",
            type(exc).__name__,
            str(exc)[:200],
            int((time.monotonic() - start_ms) * 1000),
        )
        raise HTTPException(status_code=500, detail="Failed to analyse image")
    finally:
        logger.info(
            "END:api_upload_dashboard_photo duration_ms=%d",
            int((time.monotonic() - start_ms) * 1000),
        )
