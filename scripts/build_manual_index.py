"""Build script — extract, chunk, and embed the owner's manual for RAG Q&A.

Reads the PDF at reference/2021_mazda3_manual_en_optimized.pdf, extracts text
page by page (skipping pages with no extractable text — usually diagrams),
embeds each page as one chunk using the configured local embedding model, and
writes the result to data/manual_index/ for manual_qa_service.py to load at
runtime.

Usage
-----
    APP_ENV=dev python scripts/build_manual_index.py

Re-run this whenever the source PDF changes. It is safe to re-run — it
always rebuilds both output files from scratch.

Prerequisites
-------------
- requirements.txt installed (pypdf, fastembed, numpy)
- reference/2021_mazda3_manual_en_optimized.pdf must exist
"""

import json
import logging
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: resolve project root and load .env before any other imports
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

import numpy as np  # noqa: E402
from fastembed import TextEmbedding  # noqa: E402
from pypdf import PdfReader  # noqa: E402

from backend.config.config_loader import get_config  # noqa: E402
from backend.constants import (  # noqa: E402
    MANUAL_QA_CHUNKS_PATH,
    MANUAL_QA_EMBEDDINGS_PATH,
    MANUAL_QA_INDEX_DIR_PATH,
    MANUAL_QA_SOURCE_PDF_PATH,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s %(message)s",
)
logger = logging.getLogger(__name__)

MIN_CHUNK_TEXT_LENGTH = 20


def _extract_page_chunks(pdf_path: Path) -> list[dict]:
    """Extract one text chunk per PDF page, skipping near-empty pages.

    Args:
        pdf_path: Path to the source PDF file.

    Returns:
        List of {"page": int, "text": str} dicts, one per non-empty page.
    """
    reader = PdfReader(str(pdf_path))
    chunks = []
    for page_index, page in enumerate(reader.pages):
        text = page.extract_text().strip()
        if len(text) < MIN_CHUNK_TEXT_LENGTH:
            continue
        chunks.append({"page": page_index + 1, "text": text})
    return chunks


def main() -> None:
    """Build the manual chunk index and write it to data/manual_index/."""
    start_ms = time.monotonic()
    logger.info("BEGIN:build_manual_index source=%s", MANUAL_QA_SOURCE_PDF_PATH)

    if not MANUAL_QA_SOURCE_PDF_PATH.exists():
        raise FileNotFoundError(f"Manual PDF not found: {MANUAL_QA_SOURCE_PDF_PATH}")

    cfg = get_config()

    logger.info("Extracting text from PDF pages...")
    chunks = _extract_page_chunks(MANUAL_QA_SOURCE_PDF_PATH)
    logger.info("Extracted %d non-empty page chunks", len(chunks))

    logger.info("Loading embedding model: %s", cfg.manual_qa.embedding_model)
    embedding_model = TextEmbedding(model_name=cfg.manual_qa.embedding_model)

    logger.info("Generating embeddings for %d chunks...", len(chunks))
    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = np.array(list(embedding_model.passage_embed(chunk_texts, batch_size=16)))

    MANUAL_QA_INDEX_DIR_PATH.mkdir(parents=True, exist_ok=True)

    with open(MANUAL_QA_CHUNKS_PATH, "w", encoding="utf-8") as chunks_file_handle:
        json.dump(chunks, chunks_file_handle, ensure_ascii=False, indent=2)

    np.save(MANUAL_QA_EMBEDDINGS_PATH, embeddings)

    logger.info(
        "END:build_manual_index chunks=%d embedding_shape=%s duration_ms=%d",
        len(chunks),
        embeddings.shape,
        int((time.monotonic() - start_ms) * 1000),
    )


if __name__ == "__main__":
    main()
