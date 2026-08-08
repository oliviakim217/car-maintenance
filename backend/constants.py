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

MANUAL_QA_INDEX_DIR_PATH = PROJECT_ROOT_PATH / "data" / "manual_index"
MANUAL_QA_CHUNKS_PATH = MANUAL_QA_INDEX_DIR_PATH / "chunks.json"
MANUAL_QA_EMBEDDINGS_PATH = MANUAL_QA_INDEX_DIR_PATH / "embeddings.npy"
MANUAL_QA_SOURCE_PDF_PATH = PROJECT_ROOT_PATH / "reference" / "2021_mazda3_manual_en_optimized.pdf"

ANTHROPIC_MAX_TOKENS_MANUAL_QA = 512

ANTHROPIC_MANUAL_QA_SYSTEM_PROMPT = (
    "You answer questions about a 2021 Mazda 3 using ONLY the owner's manual "
    "excerpts provided below. Each excerpt is labelled with its page number. "
    "Cite the page number(s) you used in your answer, e.g. '(p. 42)'. If the "
    "excerpts do not contain enough information to answer, say so plainly — "
    "do not guess or use outside knowledge."
)
