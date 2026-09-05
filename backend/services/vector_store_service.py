"""Vector store service.

The only module in this app that knows which vector store provider is active.
Callers that need vector search (e.g. manual_qa_service) go through
vector_store_search() below — never through numpy, a vendor SDK, or a raw
file path directly. Swapping providers (e.g. local files -> Pinecone/Qdrant)
means adding a new provider branch here and changing vector_store.provider
in config; callers never change. See "Vendor-Swappable Capabilities" in
.claude/rules/scalability-rules.md.
"""

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

VECTOR_STORE_PROVIDER_LOCAL_FILE = "local_file"


def _vector_store_search_local_file(
    query_embedding: np.ndarray,
    top_k: int,
    chunks_path: Path,
    embeddings_path: Path,
) -> list[dict]:
    """Search a local chunks.json/embeddings.npy index by dot-product similarity."""
    if not chunks_path.exists() or not embeddings_path.exists():
        raise FileNotFoundError(
            f"Vector index not found at {chunks_path} — build it before searching"
        )
    with open(chunks_path, "r", encoding="utf-8") as chunks_file_handle:
        chunks = json.load(chunks_file_handle)
    embeddings = np.load(embeddings_path)
    scores = np.dot(embeddings, query_embedding)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [chunks[i] for i in top_indices]


def vector_store_search(
    query_embedding: np.ndarray,
    top_k: int,
    provider: str,
    chunks_path: Path,
    embeddings_path: Path,
) -> list[dict]:
    """
    Find the top_k chunks closest to query_embedding via the configured vector store.

    Args:
        query_embedding: Embedding vector for the search query.
        top_k: Number of closest chunks to return.
        provider: Active vector store provider (from cfg.vector_store.provider).
        chunks_path: Path to the chunk metadata file (local_file provider).
        embeddings_path: Path to the embeddings file (local_file provider).

    Returns:
        List of chunk dicts, ordered from most to least similar.

    Raises:
        FileNotFoundError: If the local_file index has not been built yet.
        ValueError: If provider is not a recognized vector store provider.
    """
    if provider == VECTOR_STORE_PROVIDER_LOCAL_FILE:
        return _vector_store_search_local_file(query_embedding, top_k, chunks_path, embeddings_path)
    raise ValueError(f"Unknown vector_store provider: {provider}")
