from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.services.file_validation import validate_audio_file
from backend.utils.rate_limit import limiter

router = APIRouter(tags=["Upload"])

@router.post(
    "/audio",
    response_model=dict,
    dependencies=[Depends(get_current_user), Depends(limiter)],
    responses={
        400: {"description": "Invalid file"},
        413: {"description": "File too large"},
    },
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def upload_audio(file: UploadFile, db: Session = Depends(get_db)):
    validate_audio_file(file)
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "success",
        "message": "Audio file uploaded and validated successfully",
    }
