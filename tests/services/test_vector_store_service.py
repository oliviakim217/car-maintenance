"""Tests for backend/services/vector_store_service.py.

Covers the local_file provider (the only vendor implemented so far) and the
provider-dispatch behavior that keeps callers vendor-agnostic.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from backend.services.vector_store_service import (
    VECTOR_STORE_PROVIDER_LOCAL_FILE,
    vector_store_search,
)


def _write_local_index(index_dir: Path, chunks: list[dict], embeddings: np.ndarray) -> tuple[Path, Path]:
    chunks_path = index_dir / "chunks.json"
    embeddings_path = index_dir / "embeddings.npy"
    with open(chunks_path, "w", encoding="utf-8") as chunks_file_handle:
        json.dump(chunks, chunks_file_handle)
    np.save(embeddings_path, embeddings)
    return chunks_path, embeddings_path


def test_vector_store_search_returns_top_k_ordered_by_similarity(tmp_path: Path) -> None:
    chunks = [
        {"page": 1, "text": "orthogonal to query"},
        {"page": 2, "text": "best match"},
        {"page": 3, "text": "second best match"},
    ]
    embeddings = np.array(
        [
            [0.0, 1.0],
            [1.0, 0.0],
            [0.7, 0.3],
        ]
    )
    chunks_path, embeddings_path = _write_local_index(tmp_path, chunks, embeddings)
    query_embedding = np.array([1.0, 0.0])

    top_chunks = vector_store_search(
        query_embedding=query_embedding,
        top_k=2,
        provider=VECTOR_STORE_PROVIDER_LOCAL_FILE,
        chunks_path=chunks_path,
        embeddings_path=embeddings_path,
    )

    assert [chunk["page"] for chunk in top_chunks] == [2, 3]


def test_vector_store_search_respects_top_k_smaller_than_index(tmp_path: Path) -> None:
    chunks = [{"page": i, "text": f"chunk {i}"} for i in range(5)]
    embeddings = np.eye(5)
    chunks_path, embeddings_path = _write_local_index(tmp_path, chunks, embeddings)
    query_embedding = embeddings[3]

    top_chunks = vector_store_search(
        query_embedding=query_embedding,
        top_k=1,
        provider=VECTOR_STORE_PROVIDER_LOCAL_FILE,
        chunks_path=chunks_path,
        embeddings_path=embeddings_path,
    )

    assert len(top_chunks) == 1
    assert top_chunks[0]["page"] == 3


def test_vector_store_search_top_k_larger_than_index_returns_all_chunks(tmp_path: Path) -> None:
    chunks = [{"page": 1, "text": "only chunk"}]
    embeddings = np.array([[1.0, 0.0]])
    chunks_path, embeddings_path = _write_local_index(tmp_path, chunks, embeddings)

    top_chunks = vector_store_search(
        query_embedding=np.array([1.0, 0.0]),
        top_k=10,
        provider=VECTOR_STORE_PROVIDER_LOCAL_FILE,
        chunks_path=chunks_path,
        embeddings_path=embeddings_path,
    )

    assert len(top_chunks) == 1


def test_vector_store_search_missing_index_raises_file_not_found(tmp_path: Path) -> None:
    missing_chunks_path = tmp_path / "chunks.json"
    missing_embeddings_path = tmp_path / "embeddings.npy"

    with pytest.raises(FileNotFoundError):
        vector_store_search(
            query_embedding=np.array([1.0, 0.0]),
            top_k=1,
            provider=VECTOR_STORE_PROVIDER_LOCAL_FILE,
            chunks_path=missing_chunks_path,
            embeddings_path=missing_embeddings_path,
        )


def test_vector_store_search_missing_embeddings_only_raises_file_not_found(tmp_path: Path) -> None:
    chunks_path = tmp_path / "chunks.json"
    with open(chunks_path, "w", encoding="utf-8") as chunks_file_handle:
        json.dump([{"page": 1, "text": "chunk"}], chunks_file_handle)
    missing_embeddings_path = tmp_path / "embeddings.npy"

    with pytest.raises(FileNotFoundError):
        vector_store_search(
            query_embedding=np.array([1.0, 0.0]),
            top_k=1,
            provider=VECTOR_STORE_PROVIDER_LOCAL_FILE,
            chunks_path=chunks_path,
            embeddings_path=missing_embeddings_path,
        )


def test_vector_store_search_unknown_provider_raises_value_error(tmp_path: Path) -> None:
    chunks_path, embeddings_path = _write_local_index(
        tmp_path, [{"page": 1, "text": "chunk"}], np.array([[1.0, 0.0]])
    )

    with pytest.raises(ValueError, match="Unknown vector_store provider"):
        vector_store_search(
            query_embedding=np.array([1.0, 0.0]),
            top_k=1,
            provider="pinecone",
            chunks_path=chunks_path,
            embeddings_path=embeddings_path,
        )
