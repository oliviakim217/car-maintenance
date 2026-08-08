"""Vision service module.

Sends dashboard images to Claude Haiku for odometer reading extraction.
"""

import base64
import logging
import os
import time

import anthropic
import httpx

from backend.constants import ANTHROPIC_MAX_TOKENS_ODOMETER, ANTHROPIC_ODOMETER_PROMPT

logger = logging.getLogger(__name__)


async def extract_odometer_from_image(
    image_bytes: bytes,
    media_type: str,
    model: str,
) -> int:
    """Send a dashboard image to Claude and extract the odometer reading.

    Args:
        image_bytes: Raw image data.
        media_type: MIME type (e.g. "image/jpeg").
        model: Claude model ID to use.

    Returns:
        Odometer reading in km as an integer.

    Raises:
        ValueError: If the odometer cannot be read or the response is not a number.
        RuntimeError: If ANTHROPIC_API_KEY is not set.
        Exception: On API or network errors.
    """
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")

    start_ms = time.monotonic()
    logger.info("BEGIN:extract_odometer_from_image model=%s", model)
    try:
        anthropic_client = anthropic.AsyncAnthropic(
            api_key=anthropic_api_key,
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
        )
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        message = await anthropic_client.messages.create(
            model=model,
            max_tokens=ANTHROPIC_MAX_TOKENS_ODOMETER,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": ANTHROPIC_ODOMETER_PROMPT},
                    ],
                }
            ],
        )
        if not message.content or not hasattr(message.content[0], "text"):
            raise ValueError("Claude returned an empty response — please try again")
        raw_text = message.content[0].text.strip()
        if raw_text.upper() == "UNREADABLE":
            raise ValueError("Claude could not read the odometer from this image")
        extracted_km = int(raw_text.replace(",", "").replace(" ", ""))
        return extracted_km
    except ValueError:
        raise
    except Exception as exc:
        logger.error(
            "ERROR:extract_odometer_from_image error_type=%s message=%s duration_ms=%d",
            type(exc).__name__,
            str(exc)[:200],
            int((time.monotonic() - start_ms) * 1000),
        )
        raise
    finally:
        logger.info(
            "END:extract_odometer_from_image duration_ms=%d",
            int((time.monotonic() - start_ms) * 1000),
        )
