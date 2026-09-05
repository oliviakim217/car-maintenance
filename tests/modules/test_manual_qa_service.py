"""Tests for backend/modules/manual_qa/manual_qa_service.py's vector-store wiring.

Verifies _search_manual_chunks delegates to vector_store_search with the
right arguments rather than touching numpy or the index files directly.
"""

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from backend.modules.manual_qa import manual_qa_service


def test_search_manual_chunks_delegates_to_vector_store_search(tmp_path: Path) -> None:
    chunks_path = tmp_path / "chunks.json"
    embeddings_path = tmp_path / "embeddings.npy"
    with open(chunks_path, "w", encoding="utf-8") as chunks_file_handle:
        json.dump([{"page": 1, "text": "hello"}], chunks_file_handle)
    np.save(embeddings_path, np.array([[1.0, 0.0]]))

    fake_question_embedding = [np.array([1.0, 0.0])]

    with patch.object(
        manual_qa_service, "_get_embedding_model"
    ) as mock_get_embedding_model, patch.object(
        manual_qa_service, "MANUAL_QA_CHUNKS_PATH", chunks_path
    ), patch.object(
        manual_qa_service, "MANUAL_QA_EMBEDDINGS_PATH", embeddings_path
    ):
        mock_get_embedding_model.return_value.query_embed.return_value = fake_question_embedding

        result = manual_qa_service._search_manual_chunks(
            question="What oil does this car take?",
            embedding_model_name="fake-model",
            top_k=1,
            vector_store_provider="local_file",
        )

    assert result == [{"page": 1, "text": "hello"}]


def test_search_manual_chunks_unknown_provider_raises_value_error(tmp_path: Path) -> None:
    fake_question_embedding = [np.array([1.0, 0.0])]

    with patch.object(manual_qa_service, "_get_embedding_model") as mock_get_embedding_model:
        mock_get_embedding_model.return_value.query_embed.return_value = fake_question_embedding

        with pytest.raises(ValueError, match="Unknown vector_store provider"):
            manual_qa_service._search_manual_chunks(
                question="What oil does this car take?",
                embedding_model_name="fake-model",
                top_k=1,
                vector_store_provider="pinecone",
            )
