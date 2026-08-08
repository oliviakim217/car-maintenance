"""Pydantic models for the manual Q&A feature."""

from pydantic import BaseModel, ConfigDict, Field


class AskManualRequest(BaseModel):
    """Request body for asking a question about the owner's manual."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=500)


class AskManualResponse(BaseModel):
    """Response containing the AI-generated answer and its source pages."""

    model_config = ConfigDict(extra="forbid")

    answer: str
    source_pages: list[int]
