"""
VaultAI Vaults Router

This module provides endpoints for listing and managing user's podcast vault.
All endpoints require JWT authentication and users can only access their own data.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.auth import get_current_user
from backend.models.schemas import User, Podcast
from backend.models.schemas import (
    PodcastListResponse,
    PodcastListItem,
    PodcastSummaryResponse,
    ErrorResponse
)

router = APIRouter(
    prefix="/vaults",
    tags=["Vaults"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


@router.get(
    "/",
    response_model=PodcastListResponse,
    summary="List all podcasts",
    description="Returns a list of all podcasts for the authenticated user."
)
def list_podcasts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    podcasts = db.query(Podcast).filter(
        Podcast.user_id == current_user.id
    ).order_by(Podcast.created_at.desc()).all()
    
    podcast_list = [
        PodcastListItem(
            id=p.id,
            title=p.title,
            language=p.language,
            speaker_count=p.speaker_count,
            summary=p.summary,
            status=p.status,
            created_at=p.created_at
        )
        for p in podcasts
    ]
    
    return PodcastListResponse(podcasts=podcast_list)


@router.get(
    "/{podcast_id}/summary",
    response_model=PodcastSummaryResponse,
    summary="Get podcast summary details",
    description="Returns detailed summary information for a specific podcast."
)
def get_podcast_summary(
    podcast_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    podcast = db.query(Podcast).filter(
        Podcast.id == podcast_id,
        Podcast.user_id == current_user.id
    ).first()
    
    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )
    
    return PodcastSummaryResponse(
        summary=podcast.summary,
        speakers=podcast.speaker_count,
        language=podcast.language,
        duration=podcast.duration
    )