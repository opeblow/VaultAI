"""
VaultAI Query Router

This module provides endpoints for querying podcast content using AI.
Allows users to ask questions about their uploaded podcasts.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend.models.schemas import User, Podcast, JobStatusEnum
from backend.models.schemas import QueryAskRequest, QueryAskResponse, ErrorResponse
from ml.pipelines.podcast_pipeline import PodcastPipeline

router = APIRouter(
    prefix="/query",
    tags=["Query"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


def get_pipeline() -> PodcastPipeline:
    from backend.routers.ingest import get_pipeline as ing_get_pipeline
    return ing_get_pipeline()


@router.post(
    "/ask",
    response_model=QueryAskResponse,
    summary="Ask a question about a podcast",
    description="Uses AI to answer questions about a specific podcast."
)
def ask_question(
    request: QueryAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    podcast = db.query(Podcast).filter(
        Podcast.id == request.podcast_id,
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
    
    try:
        pipeline = get_pipeline()
        if pipeline is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ML Pipeline not available"
            )
        
        answer = pipeline.ask_ai(
            question=request.question
        )
        
        return QueryAskResponse(
            answer=answer,
            podcast_id=request.podcast_id
        )
        
    except Exception as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query:{str(e)}"
        )
        
    