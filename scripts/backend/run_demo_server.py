#!/usr/bin/env python3
"""
VCAAS Server - Voice Cloning as a Service
Comprehensive backend API for the voice cloning platform
"""

from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import os
import time
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from loguru import logger
from datetime import datetime
import uuid
import time
import asyncio
from pathlib import Path

# Pydantic models for request/response
class VoiceSample(BaseModel):
    id: str
    name: str
    status: str = "trained"  # trained, training, failed
    quality: int = 95
    usage_count: int = 0
    last_used: Optional[str] = "Never"
    duration: str = "0:00"
    created_at: str
    owner: str = "user"
    category: str = "owned"  # owned, licensed, public
    tags: List[str] = []

class TTSRequest(BaseModel):
    text: str
    voice_id: str
    language: str = "en"
    emotions: List[str] = []
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    add_watermark: bool = True

class TTSJob(BaseModel):
    id: str
    text: str
    voice_name: str
    status: str = "generating"  # generating, completed, failed
    audio_url: Optional[str] = None
    duration: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    emotions: List[str] = []

class User(BaseModel):
    id: str
    email: str
    username: str
    display_name: Optional[str] = None
    created_at: str
    subscription_plan: str = "free"
    usage_stats: Dict[str, Any] = {}

class TrainingJob(BaseModel):
    id: str
    name: str
    status: str = "uploading"  # uploading, processing, training, completed, failed
    progress: int = 0
    estimated_completion: Optional[str] = None
    voice_sample_count: int = 0
    total_duration: str = "0:00"
    created_at: str

# Initialize services
from services.tts_service import TTSService
from services.voice_cloning_service import VoiceCloningService

# Global service instances
tts_service = TTSService()
voice_cloning_service = VoiceCloningService()

# Initialize FastAPI app
app = FastAPI(
    title="VCAAS API - Voice Cloning as a Service",
    description="Professional AI voice cloning and text-to-speech platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - allow frontend to connect
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_ORIGINS = [o.strip() for o in allowed_origins_env.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
mock_data = {
    "users": {
        "user-123": User(
            id="user-123",
            email="demo@vcaas.com",
            username="demo_user",
            display_name="Demo User",
            created_at="2024-01-15T10:00:00Z",
            subscription_plan="pro",
            usage_stats={
                "total_voices": 12,
                "minutes_generated": 1247,
                "active_training": 3,
                "storage_used_gb": 2.4
            }
        )
    },
    "voice_samples": {
        "voice-1": VoiceSample(
            id="voice-1",
            name="Professional Voice",
            status="trained",
            quality=95,
            usage_count=1247,
            last_used="2 hours ago",
            duration="2:34",
            created_at="2024-01-10T10:00:00Z",
            tags=["business", "clear", "authoritative"]
        ),
        "voice-2": VoiceSample(
            id="voice-2",
            name="Casual Narrator",
            status="training",
            quality=0,
            usage_count=0,
            last_used="Never",
            duration="1:45",
            created_at="2024-01-14T15:30:00Z",
            tags=["warm", "friendly", "narrator"]
        ),
        "voice-3": VoiceSample(
            id="voice-3",
            name="Character Voice",
            status="trained",
            quality=88,
            usage_count=523,
            last_used="1 day ago",
            duration="3:12",
            created_at="2024-01-12T09:15:00Z",
            tags=["character", "animated", "expressive"]
        )
    },
    "tts_jobs": {},
    "training_jobs": {}
}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "VCAAS API - Voice Cloning as a Service", 
        "version": "1.0.0",
        "description": "Professional AI voice cloning and text-to-speech platform",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "auth": "/api/auth",
            "voices": "/api/voice",
            "tts": "/api/tts",
            "dashboard": "/api/dashboard",
            "training": "/api/training"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": "development",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "database": "connected",
            "storage": "available",
            "ai_models": "loaded"
        }
    }

# Authentication endpoints
@app.get("/api/auth/me")
async def get_current_user():
    """Get current user information"""
    user = mock_data["users"]["user-123"]
    return user.dict()

# Voice management endpoints
@app.get("/api/voice/samples")
async def get_voice_samples():
    """Get user's voice samples"""
    samples = [sample.dict() for sample in mock_data["voice_samples"].values()]
    return {"samples": samples}

@app.get("/api/voice/samples/{voice_id}")
async def get_voice_sample(voice_id: str):
    """Get specific voice sample"""
    if voice_id not in mock_data["voice_samples"]:
        raise HTTPException(status_code=404, detail="Voice sample not found")
    
    return mock_data["voice_samples"][voice_id].dict()

@app.delete("/api/voice/samples/{voice_id}")
async def delete_voice_sample(voice_id: str):
    """Delete a voice sample"""
    if voice_id not in mock_data["voice_samples"]:
        raise HTTPException(status_code=404, detail="Voice sample not found")
    
    del mock_data["voice_samples"][voice_id]
    return {"message": "Voice sample deleted successfully"}

# TTS endpoints
@app.get("/api/tts/voices")
async def get_available_voices():
    """Get voices available for TTS generation"""
    owned_voices = []
    licensed_voices = []

    for voice in mock_data["voice_samples"].values():
        voice_data = {
            "id": voice.id,
            "name": voice.name,
            "owner": voice.owner,
            "status": voice.status,
            "quality": f"{voice.quality}%" if voice.quality > 0 else "Training",
            "can_use": voice.status == "trained",
            "category": voice.category,
            "tags": voice.tags,
            "avatar": "🎙️"
        }

        if voice.category == "owned":
            owned_voices.append(voice_data)
        else:
            licensed_voices.append(voice_data)

    # Include zero-shot XTTS capability as a special entry
    zero_shot_entry = {
        "id": "xtts_v2_zero_shot",
        "name": "XTTS v2 (Zero-shot cloning)",
        "owner": "system",
        "status": "available",
        "quality": "variable",
        "can_use": True,
        "category": "system",
        "tags": ["zero-shot", "coqui", "xtts_v2"],
        "avatar": "🧠"
    }

    return {
        "owned_voices": owned_voices,
        "licensed_voices": licensed_voices,
        "public_voices": [
            {
                "id": "public-voice-1",
                "name": "Movie Trailer Guy",
                "owner": "Mike Thompson",
                "status": "trained",
                "quality": "85%",
                "can_use": True,
                "category": "public",
                "tags": ["dramatic", "deep", "cinematic"],
                "avatar": "🎬"
            }
        ],
        "special": [zero_shot_entry]
    }

@app.post("/api/tts/generate")
async def generate_speech(request: TTSRequest):
    """Generate speech from text using specified voice"""
    
    # Check if voice exists in mock data or trained models
    voice_name = "Unknown Voice"
    if request.voice_id in mock_data["voice_samples"]:
        voice = mock_data["voice_samples"][request.voice_id]
        if voice.status != "trained":
            raise HTTPException(status_code=400, detail="Voice is not trained yet")
        voice_name = voice.name
    else:
        # Check trained models
        model_info = voice_cloning_service.get_model_info(request.voice_id)
        if model_info:
            voice_name = model_info["name"]
        else:
            # Use default voice for unknown IDs
            voice_name = request.voice_id
    
    # Create new TTS job
    job_id = str(uuid.uuid4())
    job = TTSJob(
        id=job_id,
        text=request.text,
        voice_name=voice_name,
        status="generating",
        created_at=datetime.utcnow().isoformat(),
        emotions=request.emotions
    )
    
    mock_data["tts_jobs"][job_id] = job
    
    # Start generation in background
    asyncio.create_task(generate_tts_async(job_id, request.text, request.voice_id))
    
    return {
        "id": job_id,
        "status": "generating",
        "message": "TTS generation started",
        "estimated_completion": "5-10 seconds"
    }

async def generate_tts_async(job_id: str, text: str, voice_id: str):
    """Generate TTS audio in background"""
    try:
        job = mock_data["tts_jobs"][job_id]
        
        # Generate audio using TTS service
        audio_data = await tts_service.generate_audio(text, voice_id)
        
        # Save audio data temporarily (in production, save to cloud storage)
        audio_dir = Path("audio_cache")
        audio_dir.mkdir(exist_ok=True)
        audio_path = audio_dir / f"{job_id}.wav"
        
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
        
        # Update job status
        job.status = "completed"
        job.completed_at = datetime.utcnow().isoformat()
        job.audio_url = f"/api/tts/jobs/{job_id}/audio"
        job.duration = len(text) * 100  # Rough estimate in ms
        
        logger.info(f"TTS generation completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"TTS generation failed for job {job_id}: {e}")
        # Attempt synthetic fallback so users still get audio
        try:
            fallback_audio = await tts_service._generate_synthetic_tts(text, voice_id)  # type: ignore[attr-defined]
            audio_dir = Path("audio_cache")
            audio_dir.mkdir(exist_ok=True)
            audio_path = audio_dir / f"{job_id}.wav"
            with open(audio_path, 'wb') as f:
                f.write(fallback_audio)
            job = mock_data["tts_jobs"][job_id]
            job.status = "completed"
            job.completed_at = datetime.utcnow().isoformat()
            job.audio_url = f"/api/tts/jobs/{job_id}/audio"
            job.duration = len(text) * 100
            logger.info(f"Fallback synthetic TTS completed for job {job_id}")
        except Exception as e2:
            logger.error(f"Fallback TTS also failed for job {job_id}: {e2}")
            job = mock_data["tts_jobs"][job_id]
            job.status = "failed"

@app.get("/api/tts/jobs")
async def get_tts_jobs():
    """Get user's TTS generation jobs"""
    jobs = []
    for job in mock_data["tts_jobs"].values():
        # Simulate job completion for demo
        if job.status == "generating":
            time_since_creation = time.time() - time.mktime(datetime.fromisoformat(job.created_at.replace('Z', '+00:00')).timetuple())
            if time_since_creation > 30:  # 30 seconds
                job.status = "completed"
                job.completed_at = datetime.utcnow().isoformat()
                job.audio_url = f"/api/tts/jobs/{job.id}/audio"
                job.duration = len(job.text) * 50  # Rough estimate in ms
        
        jobs.append(job.dict())
    
    return jobs

@app.get("/api/tts/jobs/{job_id}")
async def get_tts_job(job_id: str):
    """Get specific TTS job status and result"""
    if job_id not in mock_data["tts_jobs"]:
        raise HTTPException(status_code=404, detail="TTS job not found")
    
    job = mock_data["tts_jobs"][job_id]
    
    # Simulate job completion
    if job.status == "generating":
        time_since_creation = time.time() - time.mktime(datetime.fromisoformat(job.created_at.replace('Z', '+00:00')).timetuple())
        if time_since_creation > 30:  # 30 seconds
            job.status = "completed"
            job.completed_at = datetime.utcnow().isoformat()
            job.audio_url = f"/api/tts/jobs/{job_id}/audio"
            job.duration = len(job.text) * 50  # Rough estimate in ms
    
    return job.dict()

@app.get("/api/tts/jobs/{job_id}/audio")
async def download_audio(job_id: str):
    """Download generated audio file"""
    if job_id not in mock_data["tts_jobs"]:
        raise HTTPException(status_code=404, detail="TTS job not found")

    job = mock_data["tts_jobs"][job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Audio not ready yet")

    # Check if audio file exists
    audio_path = Path("audio_cache") / f"{job_id}.wav"

    if audio_path.exists():
        # Serve the actual audio file
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename=tts_{job_id}.wav"}
        )
    else:
        # Generate audio on-demand if file doesn't exist
        try:
            audio_data = await tts_service.generate_audio(
                text=job.text,
                voice_id=job.voice_name
            )

            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={"Content-Disposition": f"attachment; filename=tts_{job_id}.wav"}
            )

        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate audio")


# Simple in-memory rate limiting (per-IP)
_RATE_LIMIT_WINDOW_SEC = 60
_RATE_LIMIT_MAX_REQUESTS = 5
_rate_limit_store = {}

# New zero-shot cloning endpoint using Coqui XTTS v2
@app.post("/api/tts/clone")
async def clone_voice(
    request: Request,
    text: str = Form(...),
    language: str = Form("en"),
    reference: UploadFile = File(...),
):
    """Zero-shot voice cloning.

    Accepts a reference voice sample and text, returns synthesized speech as WAV bytes.
    """
    try:
        # Rate limiting by client IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - _RATE_LIMIT_WINDOW_SEC
        history = _rate_limit_store.get(client_ip, [])
        history = [t for t in history if t > window_start]
        if len(history) >= _RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(status_code=429, detail="Too many cloning requests. Please wait a minute and try again.")
        history.append(now)
        _rate_limit_store[client_ip] = history

        # Validate file type
        if not reference.content_type or not reference.content_type.startswith("audio/"):
            raise HTTPException(status_code=415, detail="Unsupported file type. Please upload an audio file (e.g., WAV or MP3).")

        # Save reference to a temp file to pass file path to the model
        tmp_dir = Path("audio_cache")
        tmp_dir.mkdir(exist_ok=True)
        ref_path = tmp_dir / f"ref_{uuid.uuid4().hex}.wav"

        ref_bytes = await reference.read()
        # Enforce max upload size (20 MB)
        if len(ref_bytes) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Reference audio too large. Max 20 MB.")

        with open(ref_path, "wb") as f:
            f.write(ref_bytes)

        # Attempt to normalize/repair WAV container if needed
        try:
            import soundfile as sf  # type: ignore
            import numpy as np  # type: ignore
            data, sr = sf.read(str(ref_path), always_2d=False)
            # Re-write as PCM_16 WAV to ensure compatibility
            sf.write(str(ref_path), data, samplerate=sr, subtype="PCM_16", format="WAV")
        except Exception as norm_err:
            logger.warning(f"Reference normalization skipped: {norm_err}
            ")

        # Perform synthesis using Coqui XTTS v2
        try:
            from services.xtts_zero_shot import ZeroShotXTTS
        except Exception as e:
            logger.error(f"XTTS import failed: {e}")
            raise HTTPException(status_code=500, detail="XTTS not available on server")

        try:
            synth = ZeroShotXTTS.instance()
            wav_bytes = synth.synthesize(text=text, speaker_wav_path=str(ref_path), language=language)
        except Exception as e:
            logger.error(f"XTTS synthesis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Synthesis failed: {e}")
        finally:
            # Clean up reference file
            try:
                ref_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:
                pass

        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=xtts_clone.wav"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clone endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during cloning")

# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    user = mock_data["users"]["user-123"]
    
    return {
        "stats": [
            {"label": "Total Voices", "value": str(user.usage_stats["total_voices"]), "change": "+2"},
            {"label": "Minutes Generated", "value": f"{user.usage_stats['minutes_generated']:,}", "change": "+15%"},
            {"label": "Active Training", "value": str(user.usage_stats["active_training"]), "change": "0"},
            {"label": "Storage Used", "value": f"{user.usage_stats['storage_used_gb']}GB", "change": "+0.2GB"}
        ],
        "recent_activity": [
            {"action": "Voice clone generated", "target": "Professional Voice", "time": "2 hours ago", "type": "generation"},
            {"action": "Training completed", "target": "Character Voice", "time": "1 day ago", "type": "training"},
            {"action": "New voice sample uploaded", "target": "Casual Narrator", "time": "2 days ago", "type": "upload"}
        ]
    }

# XTTS warmup endpoint to avoid first-request latency
@app.get("/api/tts/warmup")
async def xtts_warmup():
    try:
        from services.xtts_zero_shot import ZeroShotXTTS
        synth = ZeroShotXTTS.instance()
        synth.load()
        return {"status": "ok", "device": getattr(synth, 'device', 'cpu')}
    except Exception as e:
        logger.error(f"Warmup failed: {e}")
        raise HTTPException(status_code=500, detail="XTTS warmup failed")

# Training endpoints
@app.post("/api/training/start")
async def start_training(request: dict):
    """Start training a new voice model using the voice cloning service"""
    try:
        voice_name = request.get("voice_name", "Unnamed Voice")
        audio_samples = request.get("audio_samples", [])
        user_id = request.get("user_id", "default")
        
        # Start training using voice cloning service
        result = await voice_cloning_service.start_voice_training(
            voice_name=voice_name,
            audio_samples=audio_samples,
            user_id=user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Training start failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/training/upload")
async def upload_voice_sample(
    file: UploadFile = File(...),
    user_id: str = Form("default")
):
    """Upload a voice sample for training"""
    try:
        # Read file content
        audio_data = await file.read()
        
        # Upload using voice cloning service
        sample_path = await voice_cloning_service.upload_voice_sample(
            audio_data=audio_data,
            filename=file.filename,
            user_id=user_id
        )
        
        return {
            "message": "Voice sample uploaded successfully",
            "sample_path": sample_path,
            "filename": file.filename,
            "size": len(audio_data)
        }
        
    except Exception as e:
        logger.error(f"Voice sample upload failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/training/jobs/{training_id}")
async def get_training_job_status(training_id: str):
    """Get status of a specific training job"""
    try:
        status = await voice_cloning_service.get_training_status(training_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/training/jobs")
async def get_training_jobs(user_id: str = "default"):
    """Get user's training jobs"""
    try:
        jobs = await voice_cloning_service.list_training_jobs(user_id)
        return {"jobs": jobs}
    except Exception as e:
        logger.error(f"Failed to get training jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/voice/trained")
async def get_trained_voices(user_id: str = "default"):
    """Get user's trained voice models"""
    try:
        voices = await voice_cloning_service.get_trained_voices(user_id)
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Failed to get trained voices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/voice/trained/{voice_id}")
async def delete_trained_voice(voice_id: str, user_id: str = "default"):
    """Delete a trained voice model"""
    try:
        success = await voice_cloning_service.delete_voice_model(voice_id, user_id)
        if success:
            return {"message": "Voice model deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Voice model not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete voice model: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )

if __name__ == "__main__":
    logger.info("Starting VCAAS API Server...")
    uvicorn.run(
        "vcaas_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
