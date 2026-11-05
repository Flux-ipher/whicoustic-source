"""
Voice Training API Endpoints (Stubbed due to missing mongo dependencies)

Provides REST API for voice training operations.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
import json

from .auth import get_current_user
# from app.models.mongo.user import User  # REMOVED
# from app.models.mongo.voice_sample import VoiceSample # REMOVED
# from app.services.voice_training_service import voice_training_service # REMOVED

from app.models.user import User # SQL Model
from app.models.voice import Voice # SQL Model

router = APIRouter()


class TrainingJobRequest(BaseModel):
    voice_name: str = Field(..., min_length=1, max_length=100)
    sample_ids: List[str] = Field(..., min_items=3, max_items=50)
    training_config: Optional[Dict[str, Any]] = None


class TrainingJobResponse(BaseModel):
    job_id: str
    message: str = "Training job started successfully"


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    voice_name: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result_model_id: Optional[str] = None
    error_message: Optional[str] = None
    config: Dict[str, Any]


@router.post("/start", response_model=TrainingJobResponse)
async def start_training(
    request: TrainingJobRequest,
    current_user: User = Depends(get_current_user)
):
    """Start a new voice training job"""
    raise HTTPException(
        status_code=501, 
        detail="Voice Training is currently disabled. This feature requires the MongoDB integration and training worker pipeline."
    )


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get training job status"""
    raise HTTPException(
        status_code=501, 
        detail="Voice Training is currently disabled. This feature requires the MongoDB integration and training worker pipeline."
    )


@router.post("/job/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a training job"""
    raise HTTPException(
        status_code=501, 
        detail="Voice Training is currently disabled. This feature requires the MongoDB integration and training worker pipeline."
    )


@router.get("/jobs")
async def list_training_jobs(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List user's training jobs"""
    raise HTTPException(
        status_code=501, 
        detail="Voice Training is currently disabled. This feature requires the MongoDB integration and training worker pipeline."
    )


@router.get("/samples/suitable")
async def get_suitable_samples(
    current_user: User = Depends(get_current_user)
):
    """Get voice samples suitable for training"""
    raise HTTPException(
        status_code=501, 
        detail="Voice Training is currently disabled. This feature requires the MongoDB integration and training worker pipeline."
    )


@router.post("/validate-samples")
async def validate_training_samples(
    sample_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """Validate samples for training"""
    raise HTTPException(
        status_code=501, 
        detail="Voice Training is currently disabled. This feature requires the MongoDB integration and training worker pipeline."
    )


@router.get("/stats")
async def get_training_stats(
    current_user: User = Depends(get_current_user)
):
    """Get training service statistics (admin only for now)"""
    raise HTTPException(
        status_code=501, 
        detail="Voice Training is currently disabled. This feature requires the MongoDB integration and training worker pipeline."
    )