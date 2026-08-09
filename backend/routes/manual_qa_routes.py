"""Manual Q&A routes.

Accepts a natural-language question about the vehicle and returns an answer
grounded in the owner's manual, via the local RAG pipeline in
manual_qa_service.
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.config.config_loader import get_config
from backend.modules.manual_qa.manual_qa_service import ask_manual_question
from backend.modules.manual_qa.models import AskManualRequest, AskManualResponse
from backend.utils.auth import require_session
from backend.utils.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_session)])


@router.post("/api/manual/ask", response_model=AskManualResponse)
@limiter.limit(lambda: f"{get_config().rate_limiting.manual_qa_requests_per_minute}/minute")
async def api_post_manual_ask(request: Request, body: AskManualRequest) -> AskManualResponse:
    """Answer a question about the vehicle using the owner's manual.

    Args:
        body: JSON body with the user's question.

    Returns:
        AskManualResponse with the answer and cited source pages.
    """
    start_ms = time.monotonic()
    logger.info("BEGIN:api_post_manual_ask")
    try:
        cfg = get_config()
        return await ask_manual_question(body.question, cfg)
    except FileNotFoundError as exc:
        logger.error(
            "ERROR:api_post_manual_ask error_type=FileNotFoundError message=%s duration_ms=%d",
            str(exc)[:200],
            int((time.monotonic() - start_ms) * 1000),
        )
        raise HTTPException(status_code=503, detail="Manual index not built yet")
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.error(
            "ERROR:api_post_manual_ask error_type=%s message=%s duration_ms=%d",
            type(exc).__name__,
            str(exc)[:200],
            int((time.monotonic() - start_ms) * 1000),
        )
        raise HTTPException(status_code=500, detail="Failed to answer question")
    finally:
        logger.info(
            "END:api_post_manual_ask duration_ms=%d",
            int((time.monotonic() - start_ms) * 1000),
        )
