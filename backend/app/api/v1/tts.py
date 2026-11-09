"""
Text-to-Speech synthesis endpoints for Whicoustic API v1.
Handles speech generation with watermarking and usage tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import os

from ...core.database import get_db
from ...services.tts_service import tts_service, TTSService
from ...core.watermark import WatermarkService
from ...services.license_service import LicenseService
from ...models.user import User
from ...models.voice import Voice
from ...models.usage_log import UsageLog, LicenseUsage
from ...core.database import SyncSessionLocal
from ...core.rate_limit import rate_limit_synthesis, rate_limit_cloning
from .auth import get_current_user, get_optional_current_user
from ...services.xtts_zero_shot import ZeroShotXTTS
from ...services.xtts_finetuned import FinetunedXTTS
from ...schemas.tts import (
    SynthesizeRequest,
    SynthesizeResponse,
    TTSJobResponse,
    TTSResponse,
    TTSRequest,
    TTSResultResponse,
    VoiceParams
)

router = APIRouter(prefix="/tts", tags=["text-to-speech"])


def log_usage(
    db: Optional[Session],
    user_id: str,
    voice_id: str,
    text_length: int,
    audio_duration: float = 0.0,
    watermark_id: Optional[str] = None,
    license_id: Optional[str] = None
):
    """Log synthesis usage in background."""
    local_session = False
    session = db
    try:
        if session is None or not session.is_active:
            session = SyncSessionLocal()
            local_session = True

        usage_log = UsageLog(
            user_id=user_id,
            voice_id=voice_id,
            text_length=text_length,
            audio_duration=audio_duration,
            watermark_id=watermark_id,
            license_id=license_id,
            created_at=datetime.utcnow()
        )
        session.add(usage_log)

        if license_id:
            lic_usage = LicenseUsage(
                license_id=license_id,
                user_id=user_id,
                voice_id=voice_id,
                text_length=text_length,
                audio_duration=audio_duration,
                watermark_id=watermark_id,
                used_at=datetime.utcnow()
            )
            session.add(lic_usage)

        session.commit()
    except Exception:
        if session:
            session.rollback()
    finally:
        if local_session and session:
            session.close()


@router.post("/synthesize", response_model=SynthesizeResponse, dependencies=[Depends(rate_limit_synthesis)])
async def synthesize_speech(
    request: SynthesizeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate speech from text using a cloned voice."""
    
    # Verify voice exists and belongs to user
    voice = db.query(Voice).filter(
        Voice.id == request.voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found"
        )
    
    if voice.status != 'ready':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice is not ready for synthesis"
        )
    
    # Validate license token if provided
    license_service = LicenseService(db)
    license_info = None
    
    if request.license_token:
        license_info = await license_service.validate_license_token(
            request.license_token,
            voice_id=request.voice_id
        )
        if not license_info:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired license token"
            )
    
    try:
        # Use shared TTS service
        # Generate unique job ID
        job_id = f"tts_{uuid.uuid4().hex[:12]}"
        
        # Prepare voice parameters
        voice_params = VoiceParams(
            speed=request.voice_params.speed if request.voice_params else 1.0,
            pitch=request.voice_params.pitch if request.voice_params else 0.0,
            emotion=request.voice_params.emotion if request.voice_params else "neutral"
        )
        
        # Generate speech
        audio_path = await tts_service.synthesize_text(
            text=request.text,
            voice_id=request.voice_id,
            speaker_embedding=voice.speaker_embedding,
            voice_params=voice_params,
            job_id=job_id
        )
        
        # Apply watermarking
        watermark_service = WatermarkService()
        watermark_id = f"wm_{uuid.uuid4().hex[:16]}"
        
        watermarked_audio_path = await watermark_service.embed_watermark(
            audio_path=audio_path,
            watermark_id=watermark_id,
            license_id=license_info['license_id'] if license_info else None,
            voice_id=request.voice_id,
            method='robust'
        )
        
        final_synth_file = watermarked_audio_path if os.path.exists(watermarked_audio_path) else audio_path
        
        # Register completed job in tts_service so download and status endpoints succeed
        tts_service._jobs[job_id] = {
            "job_id": job_id,
            "user_id": str(current_user.id),
            "voice_model_id": request.voice_id,
            "text": request.text,
            "output_format": "wav",
            "output_file": final_synth_file,
            "status": "completed",
            "progress": 100,
            "created_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "quality_score": 0.95,
            "actual_duration": max(1.0, len(request.text) * 0.08),
            "file_size_mb": round(os.path.getsize(final_synth_file) / (1024 * 1024), 3) if os.path.exists(final_synth_file) else 0.1,
        }
        
        # Upload synthesized audio to Google Drive storage adapter
        try:
            from app.services.google_drive_storage import get_google_drive_storage
            storage = get_google_drive_storage()
            await storage.upload_file(
                file_path=final_synth_file,
                file_name=f"synth_{job_id}_{request.voice_id}.wav",
                mime_type="audio/wav"
            )
        except Exception as drive_err:
            logger.warning(f"Could not upload synthesized audio to Google Drive: {drive_err}")
        
        # Log usage in background
        background_tasks.add_task(
            log_usage,
            db=db,
            user_id=current_user.id,
            voice_id=request.voice_id,
            text_length=len(request.text),
            audio_duration=0,  # Will be calculated in background
            watermark_id=watermark_id,
            license_id=license_info['license_id'] if license_info else None
        )
        
        return SynthesizeResponse(
            job_id=job_id,
            audio_url=f"/api/v1/tts/download/{job_id}",
            watermark_id=watermark_id,
            license_id=license_info['license_id'] if license_info else None,
            status="completed",
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(e)}"
        )


@router.post("/generate", response_model=TTSResponse)
async def generate_speech(
    request: TTSRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate speech from text using a voice model"""
    try:
        # Validate text content
        if not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        # Start TTS generation
        job_id = await tts_service.generate_speech(
            user_id=str(current_user.id),
            voice_model_id=request.voice_model_id,
            text=request.text,
            output_format=request.output_format,
            voice_settings=request.voice_settings
        )
        
        # Get job status for estimated values
        job_data = await tts_service.get_job_status(job_id)
        
        return TTSResponse(
            job_id=job_id,
            estimated_duration=job_data.get("estimated_duration", 0),
            estimated_cost=job_data.get("estimated_cost", 0)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start TTS generation"
        )


@router.get("/job/{job_id}", response_model=TTSJobResponse)
async def get_tts_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get TTS job status"""
    try:
        job_data = await tts_service.get_job_status(job_id)
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TTS job not found"
            )
        
        # Check ownership
        if job_data["user_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this TTS job"
            )
        
        return TTSJobResponse(**job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get TTS job status"
        )


@router.post("/job/{job_id}/cancel")
async def cancel_tts_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a TTS generation job"""
    try:
        success = await tts_service.cancel_job(
            job_id=job_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TTS job not found or cannot be cancelled"
            )
        
        return {"message": "TTS job cancelled successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel TTS job"
        )


@router.get("/job/{job_id}/result", response_model=TTSResultResponse)
async def get_tts_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get TTS job result information"""
    try:
        result = await tts_service.get_job_result(
            job_id=job_id,
            user_id=str(current_user.id)
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TTS job result not found or not ready"
            )
        
        return TTSResultResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get TTS result"
        )


@router.get("/download/{job_id}")
@router.get("/download/{job_id}/")
@router.get("/job/{job_id}/download")
@router.get("/job/{job_id}/download/")
async def download_tts_audio(
    job_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Download generated audio file with dual route support."""
    try:
        user_id_str = str(current_user.id) if current_user else None
        job = tts_service._jobs.get(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TTS job result not found or not ready"
            )

        if user_id_str and job.get("user_id") and job["user_id"] != user_id_str:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this TTS job output"
            )

        file_path = job.get("output_file")
        if not file_path or not os.path.exists(file_path):
            # Check if file can be resolved by storage adapter
            from app.services.google_drive_storage import get_google_drive_storage
            storage = get_google_drive_storage()
            candidate = storage._resolve_local_file_path(file_path or f"{job_id}.wav")
            if candidate and candidate.exists():
                file_path = str(candidate)
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Audio file not found on server or storage adapter"
                )
        
        # Get file extension for content type
        file_extension = os.path.splitext(file_path)[1].lower() or ".wav"
        content_type_map = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg"
        }
        
        media_type = content_type_map.get(file_extension, "audio/wav")
        filename = f"tts_{job_id}{file_extension}"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download audio file: {e}"
        )


@router.post("/clone", dependencies=[Depends(rate_limit_cloning)])
async def clone_speech(
    text: str = Form(...),
    language: str = Form("en"),
    reference: UploadFile = File(...),
    model_dir: Optional[str] = Form(None),
):
    """Zero-shot cloning via XTTS v2. Returns generated audio file."""
    # Basic validations
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if reference.size is not None and reference.size > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Reference audio too large (max 20MB)")
    if not reference.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
        raise HTTPException(status_code=415, detail="Unsupported file type (wav/mp3/m4a/flac)")

    # Save reference to temp
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(reference.filename)[1], delete=False) as tmp:
            ref_path = tmp.name
            tmp.write(await reference.read())

        # Use fine-tuned model if provided; else zero-shot
        if model_dir and os.path.isdir(model_dir):
            try:
                fxtts = FinetunedXTTS(model_dir)
                audio_bytes = fxtts.synthesize(text=text, speaker_wav_path=ref_path, language=language)
            except Exception:
                xtts = ZeroShotXTTS.instance()
                audio_bytes = xtts.synthesize(text=text, speaker_wav_path=ref_path, language=language)
        else:
            xtts = ZeroShotXTTS.instance()
            audio_bytes = xtts.synthesize(text=text, speaker_wav_path=ref_path, language=language)

        # Write output wav
        out_dir = os.path.join("data", "tts_outputs")
        os.makedirs(out_dir, exist_ok=True)
        job_id = f"xtts_{uuid.uuid4().hex[:12]}"
        out_path = os.path.join(out_dir, f"{job_id}.wav")
        with open(out_path, "wb") as f:
            f.write(audio_bytes)

        # Optional watermark embed (robust)
        try:
            wm = WatermarkService()
            out_path = await wm.embed_watermark(out_path, watermark_id=f"wm_{job_id}")
        except Exception:
            pass

        return FileResponse(out_path, media_type="audio/wav", filename=os.path.basename(out_path))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if 'ref_path' in locals() and os.path.exists(ref_path):
                os.unlink(ref_path)
        except Exception:
            pass


@router.post("/clone/warmup")
async def clone_warmup():
    """Preload XTTS model to avoid first-request latency."""
    try:
        ZeroShotXTTS.instance().load()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_tts_jobs(
    status_filter: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """List user's TTS jobs"""
    try:
        jobs = await tts_service.list_user_jobs(
            user_id=str(current_user.id),
            status_filter=status_filter,
            limit=min(limit, 100)  # Cap at 100
        )
        
        return {
            "jobs": jobs,
            "total": len(jobs)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list TTS jobs"
        )


@router.get("/models/available")
async def get_available_voice_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return user's voices as available models (SQL-backed)."""
    try:
        # List voices belonging to the user as available "models"
        voices = (
            db.query(Voice)
            .filter(Voice.user_id == current_user.id)
            .all()
        )
        available = [
            {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "model_type": "voice_clip",
                "quality_score": v.quality_score,
                "supported_languages": ["en"],
                "is_public": False,
                "is_owned": True,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in voices
        ]
        return {"models": available, "total": len(available)}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get available voice models")


@router.get("/models/{model_id}/info")
async def get_voice_model_info(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return info for a user's Voice row as model info."""
    try:
        v = (
            db.query(Voice)
            .filter(Voice.id == model_id, Voice.user_id == current_user.id)
            .first()
        )
        if not v:
            raise HTTPException(status_code=404, detail="Voice not found")
        return {
            "id": v.id,
            "name": v.name,
            "description": v.description,
            "model_type": "voice_clip",
            "model_version": None,
            "architecture": None,
            "quality_score": v.quality_score,
            "similarity_score": None,
            "naturalness_score": None,
            "supported_languages": ["en"],
            "sample_count": 1,
            "training_duration_minutes": 0,
            "model_size_mb": (v.file_size or 0) / (1024 * 1024),
            "is_public": False,
            "is_owned": True,
            "status": v.status,
            "deployment_status": "deployed" if v.status == "ready" else v.status,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "training_completed_at": None,
            "deployed_at": v.updated_at.isoformat() if v.updated_at else None,
            "usage_count": 0,
            "total_generation_time": 0,
            "tags": [],
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get voice model information")


@router.get("/stats")
async def get_tts_stats(
    current_user: User = Depends(get_current_user)
):
    """Get TTS service statistics"""
    try:
        # Get service stats
        service_stats = tts_service.get_service_stats()
        
        # Get user-specific stats
        user_jobs = await tts_service.list_user_jobs(str(current_user.id))
        user_stats = {
            "total_generations": len(user_jobs),
            "completed_generations": len([j for j in user_jobs if j["status"] == "completed"]),
            "failed_generations": len([j for j in user_jobs if j["status"] == "failed"]),
            "pending_generations": len([j for j in user_jobs if j["status"] in ["pending", "processing"]]),
            "total_characters": sum(len(j.get("text", "")) for j in user_jobs if j["status"] == "completed"),
            "total_duration": sum(j.get("actual_duration", 0) for j in user_jobs if j["status"] == "completed"),
            "average_quality": sum(j.get("quality_score", 0) for j in user_jobs if j["status"] == "completed" and j.get("quality_score")) / max(1, len([j for j in user_jobs if j["status"] == "completed" and j.get("quality_score")]))
        }
        
        return {
            "service_stats": service_stats,
            "user_stats": user_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get TTS stats"
        )


@router.post("/test")
async def test_tts_generation(
    current_user: User = Depends(get_current_user)
):
    """Smoke-test TTS with a synthetic job."""
    try:
        test_text = "Hello, this is a test of the text-to-speech system."
        job_id = await tts_service.generate_speech(
            user_id=str(current_user.id),
            voice_model_id="default",
            text=test_text,
            output_format="wav",
            voice_settings={}
        )
        return {"message": "Test TTS started", "job_id": job_id, "test_text": test_text}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to start test generation")
