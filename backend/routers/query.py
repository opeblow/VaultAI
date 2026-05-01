"""
VaultAI Query Router

This module provides endpoints for querying podcast content using AI.
Allows users to ask questions about their uploaded podcasts.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user, decode_token
from backend.models.schemas import User, Podcast, JobStatusEnum
from backend.models.schemas import QueryAskRequest, QueryAskResponse, ErrorResponse
from ml.pipelines.podcast_pipeline import PodcastPipeline

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/query",
    tags=["Query"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        429: {"model": ErrorResponse, "description": "Too Many Requests"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


def get_user_key(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        if payload and payload.get("sub"):
            return f"user:{payload.get('sub')}"
    return get_remote_address(request)


def get_pipeline() -> PodcastPipeline:
    from backend.routers.ingest import get_pipeline as ing_get_pipeline
    return ing_get_pipeline()


@router.post(
    "/ask",
    response_model=QueryAskResponse,
    summary="Ask a question about a podcast",
    description="Uses AI to answer questions about a specific podcast. Rate limited to 30 requests/hour per user."
)
@limiter.limit("30/hour", key_func=get_user_key)
def ask_question(
    request: Request,
    request_body: QueryAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        podcast = db.query(Podcast).filter(
            Podcast.id == request_body.podcast_id,
            Podcast.user_id == current_user.id
        ).first()
        
        if not podcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Podcast not found"
            )
        
        if podcast.status != JobStatusEnum.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Podcast is not yet processed. Please wait for processing to complete."
            )
        
        pipeline = get_pipeline()
        if pipeline is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ML Pipeline not available"
            )
        
        answer = pipeline.ask_ai(
            question=request_body.question
        )
        
        return QueryAskResponse(
            answer=answer,
            podcast_id=request_body.podcast_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )
        
    