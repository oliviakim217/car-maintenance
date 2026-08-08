"""Project-wide constants shared across backend modules."""

import re
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent

TASK_ID_PATTERN = re.compile(r"^[a-z0-9_]{1,64}$")

VALID_APP_ENVS = ("dev", "prod")

ANTHROPIC_ODOMETER_PROMPT = (
    "Look at this car dashboard image. Find the odometer reading and return ONLY "
    "the number in kilometres as a plain integer — no units, commas, spaces, or "
    "other text. If you cannot read the odometer clearly, respond with the single "
    "word UNREADABLE."
)

ANTHROPIC_MAX_TOKENS_ODOMETER = 64

IMAGE_MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png":  [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
}
