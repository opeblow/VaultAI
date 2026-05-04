"""
VaultAI Ingest Router

This module provides endpoints for uploading and processing podcast audio files.
Implements file upload with background ML processing tasks.
"""

import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.auth import get_current_user, decode_token
from backend.models.schemas import User, Podcast, Job, JobStatusEnum
from backend.models.schemas import PodcastUploadResponse, JobStatusResponse, ErrorResponse

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/ingest",
    tags=["Ingest"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Plan limit exceeded"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        413: {"model": ErrorResponse, "description": "Payload Too Large"},
        429: {"model": ErrorResponse, "description": "Too Many Requests"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)

pipeline = None

ALLOWED_EXTENSIONS = {".mp3", ".mpeg", ".wav", ".m4a", ".ogg", ".flac"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def get_user_key(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        if payload and payload.get("sub"):
            return f"user:{payload.get('sub')}"
    return get_remote_address(request)


def get_pipeline() -> "PodcastPipeline":
    global pipeline
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ML Pipeline not initialized"
        )
    return pipeline


def set_pipeline(p: "PodcastPipeline"):
    global pipeline
    pipeline = p


def process_podcast_background(
    job_id: int,
    podcast_id: int,
    file_path: str,
    user_id: int,
    title: str
):
    from backend.database import SessionLocal
    
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        
        if not job or not podcast:
            return
        
        try:
            p = get_pipeline()
            
            result = p.execute(
                user_id=str(user_id),
                podcast_id=str(podcast_id),
                audio_input_path=file_path
            )
            
            podcast.language = result.get("language", "unknown")
            podcast.duration = result.get("duration", 0.0)
            podcast.speaker_count = result.get("speaker_count", 0)
            podcast.summary = result.get("summary", "")
            podcast.vault_path = result.get("vault_path", podcast.vault_path)
            podcast.status = JobStatusEnum.COMPLETED.value
            
            job.status = JobStatusEnum.COMPLETED.value
            job.error = None
            
        except Exception as e:
            job.status = JobStatusEnum.FAILED.value
            job.error = str(e)
            podcast.status = JobStatusEnum.FAILED.value
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        
        db.commit()
        
    except Exception as e:
        db.rollback()
    finally:
        db.close()


@router.post(
    "/upload",
    response_model=PodcastUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload podcast audio file",
    description="Uploads an audio file and creates a processing job. The file is saved to storage and processed asynchronously."
)
@limiter.limit("10/hour", key_func=get_user_key)
async def upload_podcast(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to upload (mp3, wav, m4a, m4a, ogg, flac)"),
    title: str = Form(..., min_length=1, max_length=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from backend.config import check_plan_limit
        
        podcast_title = title.strip()
        if not podcast_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Podcast title is required"
            )
        
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed formats: {', '.join(ext[1:] for ext in ALLOWED_EXTENSIONS)}"
            )
        
        podcast_count = db.query(Podcast).filter(Podcast.user_id == current_user.id).count()
        
        if not check_plan_limit(current_user.plan, podcast_count):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You have reached your plan limit. Upgrade to upload more podcasts."
            )
        
        audio_dir = os.path.join(settings.STORAGE_PATH, "users", str(current_user.id), "audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(audio_dir, unique_filename)
        
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 100MB."
            )
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(content)
        
        podcast = Podcast(
            user_id=current_user.id,
            title=podcast_title,
            status=JobStatusEnum.PROCESSING.value,
            vault_path=file_path
        )
        db.add(podcast)
        db.flush()
        
        job = Job(
            user_id=current_user.id,
            podcast_id=podcast.id,
            status=JobStatusEnum.PROCESSING.value
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        db.refresh(podcast)
        
        background_tasks.add_task(
            process_podcast_background,
            job_id=job.id,
            podcast_id=podcast.id,
            file_path=file_path,
            user_id=current_user.id,
            title=podcast_title
        )
        
        return PodcastUploadResponse(
            job_id=job.id,
            status="processing"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Returns the status of a processing job."
)
def get_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            error=job.error
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )
