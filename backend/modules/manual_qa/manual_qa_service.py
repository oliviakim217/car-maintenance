"""Manual Q&A service module.

Answers natural-language questions about the vehicle using a small local RAG
pipeline: embeds the question, finds the closest excerpts from the owner's
manual (pre-indexed offline by scripts/build_manual_index.py), and asks
Claude to answer using only those excerpts.
"""

import asyncio
import logging
import os
import time
from functools import lru_cache

import anthropic
import httpx
from fastembed import TextEmbedding

from backend.constants import (
    ANTHROPIC_MANUAL_QA_SYSTEM_PROMPT,
    ANTHROPIC_MAX_TOKENS_MANUAL_QA,
    MANUAL_QA_CHUNKS_PATH,
    MANUAL_QA_EMBEDDINGS_PATH,
)
from backend.modules.manual_qa.models import AskManualResponse
from backend.services.vector_store_service import vector_store_search

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_embedding_model(embedding_model_name: str) -> TextEmbedding:
    """Load and cache the local embedding model (downloads on first use)."""
    return TextEmbedding(model_name=embedding_model_name)


def _search_manual_chunks(
    question: str, embedding_model_name: str, top_k: int, vector_store_provider: str
) -> list[dict]:
    """Find the top_k manual chunks most relevant to the question.

    Synchronous and CPU-bound (embedding + vector search) — must be called
    via asyncio.to_thread from async code, never awaited directly.

    Raises:
        FileNotFoundError: If the manual index has not been built yet.
    """
    embedding_model = _get_embedding_model(embedding_model_name)
    question_embedding = list(embedding_model.query_embed(question))[0]
    return vector_store_search(
        query_embedding=question_embedding,
        top_k=top_k,
        provider=vector_store_provider,
        chunks_path=MANUAL_QA_CHUNKS_PATH,
        embeddings_path=MANUAL_QA_EMBEDDINGS_PATH,
    )


async def ask_manual_question(question: str, cfg) -> AskManualResponse:
    """Answer a question about the vehicle using the owner's manual.

    Args:
        question: The user's natural-language question.
        cfg: AppConfig instance (for manual_qa settings).

    Returns:
        AskManualResponse with the answer and the source page numbers used.

    Raises:
        FileNotFoundError: If the manual index has not been built yet.
        RuntimeError: If ANTHROPIC_API_KEY is not set.
        ValueError: If Claude returns an empty response.
        Exception: On API or network errors.
    """
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")

    start_ms = time.monotonic()
    logger.info("BEGIN:ask_manual_question")
    try:
        relevant_chunks = await asyncio.to_thread(
            _search_manual_chunks,
            question,
            cfg.manual_qa.embedding_model,
            cfg.manual_qa.top_k_chunks,
            cfg.vector_store.provider,
        )
        excerpts_text = "\n\n".join(
            f"[Page {chunk['page']}]\n{chunk['text']}" for chunk in relevant_chunks
        )
        source_pages = sorted({chunk["page"] for chunk in relevant_chunks})

        anthropic_client = anthropic.AsyncAnthropic(
            api_key=anthropic_api_key,
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
        )
        message = await anthropic_client.messages.create(
            model=cfg.manual_qa.model,
            max_tokens=ANTHROPIC_MAX_TOKENS_MANUAL_QA,
            system=ANTHROPIC_MANUAL_QA_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Manual excerpts:\n\n{excerpts_text}\n\nQuestion: {question}",
                }
            ],
        )
        if not message.content or not hasattr(message.content[0], "text"):
            raise ValueError("Claude returned an empty response — please try again")
        answer = message.content[0].text.strip()

        logger.info(
            "END:ask_manual_question source_pages=%s duration_ms=%d",
            source_pages,
            int((time.monotonic() - start_ms) * 1000),
        )
        return AskManualResponse(answer=answer, source_pages=source_pages)
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as exc:
        logger.error(
            "ERROR:ask_manual_question error_type=%s message=%s duration_ms=%d",
            type(exc).__name__,
            str(exc)[:200],
            int((time.monotonic() - start_ms) * 1000),
        )
        raise
