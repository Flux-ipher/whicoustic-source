"""
Production TTS API with Real Inference Engine Integration
High-performance voice synthesis endpoints for VCaaS platform
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import uuid
import io
import json
import logging
from datetime import datetime
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user
from services.tts_inference_engine import TTSInferenceEngine, SynthesisRequest, SynthesisResult
from app.models.user import User
from app.models.usage_log import UsageLog
from pydantic import BaseModel, Field

# Initialize TTS inference engine
VOICE_REGISTRY_PATH = "../models/vcaas_voice_registry/voice_registry.json"
tts_engine = TTSInferenceEngine(VOICE_REGISTRY_PATH)

logger = logging.getLogger(__name__)

class ProductionTTSRequest(BaseModel):
    """Production TTS synthesis request"""
    text: str = Field(..., min_length=1, max_length=1000, description="Text to synthesize")
    voice_id: str = Field(..., description="Voice ID from registry")
    output_format: str = Field(default="wav", regex="^(wav|mp3|flac)$", description="Audio output format")
    sample_rate: int = Field(default=22050, ge=8000, le=48000, description="Audio sample rate")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
    pitch_shift: float = Field(default=0.0, ge=-12.0, le=12.0, description="Pitch shift in semitones")
    emotion: str = Field(default="neutral", description="Emotional tone")
    quality: str = Field(default="high", regex="^(draft|standard|high|premium)$", description="Synthesis quality")

class ProductionTTSResponse(BaseModel):
    """Production TTS synthesis response"""
    success: bool
    job_id: str
    audio_duration: float
    processing_time: float
    voice_id: str
    voice_name: str
    quality_score: float
    metadata: Dict[str, Any]

class VoiceInfoResponse(BaseModel):
    """Voice information response"""
    id: str
    name: str
    description: str
    language: str
    gender: str
    accent: str
    quality_score: float
    quality_tier: str
    commercial_use: bool
    sample_audio_url: Optional[str] = None

class TTSStatsResponse(BaseModel):
    """TTS engine statistics response"""
    total_requests: int
    successful_syntheses: int
    failed_syntheses: int
    average_processing_time: float
    average_audio_duration: float
    real_time_factor: float
    cache_stats: Dict[str, Any]

router = APIRouter(prefix="/tts/production", tags=["production-tts"])

@router.on_event("startup")
async def startup_tts_engine():
    """Initialize TTS engine on startup"""
    try:
        # Preload popular voices for faster access
        await tts_engine.preload_popular_voices()
        logger.info("TTS inference engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize TTS engine: {e}")

@router.get("/voices", response_model=List[VoiceInfoResponse])
async def get_available_voices(
    quality_tier: Optional[str] = None,
    language: Optional[str] = None,
    gender: Optional[str] = None
):
    """Get list of available voices with filtering options"""
    try:
        voices = await tts_engine.get_available_voices()
        
        # Apply filters
        filtered_voices = voices
        
        if quality_tier:
            filtered_voices = [v for v in filtered_voices if v.get('quality_tier') == quality_tier]
        
        if language:
            filtered_voices = [v for v in filtered_voices if v.get('language', '').startswith(language)]
        
        if gender and gender != 'any':
            filtered_voices = [v for v in filtered_voices if v.get('gender') == gender]
        
        # Convert to response format
        voice_responses = []
        for voice in filtered_voices:
            voice_response = VoiceInfoResponse(
                id=voice['id'],
                name=voice['name'],
                description=voice['description'],
                language=voice['language'],
                gender=voice['gender'],
                accent=voice['accent'],
                quality_score=voice['quality_score'],
                quality_tier=voice['quality_tier'],
                commercial_use=voice['commercial_use'],
                sample_audio_url=f"/api/tts/production/preview/{voice['id']}"
            )
            voice_responses.append(voice_response)
        
        return voice_responses
        
    except Exception as e:
        logger.error(f"Failed to get available voices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voice list"
        )

@router.post("/synthesize", response_model=ProductionTTSResponse)
async def synthesize_speech_production(
    request: ProductionTTSRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """High-performance speech synthesis with real TTS engine"""
    
    start_time = datetime.utcnow()
    job_id = f"tts_prod_{uuid.uuid4().hex[:12]}"
    
    try:
        logger.info(f"Starting synthesis job {job_id} for user {current_user.id}")
        
        # Create synthesis request
        synthesis_request = SynthesisRequest(
            text=request.text,
            voice_id=request.voice_id,
            output_format=request.output_format,
            sample_rate=request.sample_rate,
            speed=request.speed,
            pitch_shift=request.pitch_shift,
            emotion=request.emotion,
            quality=request.quality
        )
        
        # Perform synthesis
        result = await tts_engine.synthesize_speech(synthesis_request)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Store audio result temporarily
        audio_storage_path = Path(f"temp_audio/{job_id}.{result.format}")
        audio_storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(audio_storage_path, 'wb') as f:
            f.write(result.audio_data)
        
        # Log usage in background
        background_tasks.add_task(
            log_synthesis_usage,
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            voice_id=request.voice_id,
            text_length=len(request.text),
            audio_duration=result.duration,
            processing_time=processing_time,
            quality_score=result.metadata.get('model_info', {}).get('quality_score', 0.8)
        )
        
        # Prepare response
        response = ProductionTTSResponse(
            success=True,
            job_id=job_id,
            audio_duration=result.duration,
            processing_time=processing_time,
            voice_id=result.metadata['voice_id'],
            voice_name=result.metadata['voice_name'],
            quality_score=result.metadata['model_info']['quality_score'],
            metadata={
                'text_length': len(request.text),
                'sample_rate': result.sample_rate,
                'format': result.format,
                'generation_timestamp': result.metadata['generation_timestamp'],
                'download_url': f"/api/tts/production/download/{job_id}",
                'expires_at': (datetime.utcnow().timestamp() + 3600)  # 1 hour expiry
            }
        )
        
        logger.info(f"Synthesis job {job_id} completed successfully in {processing_time:.2f}s")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid request for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Synthesis failed for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech synthesis failed"
        )

@router.get("/download/{job_id}")
async def download_synthesized_audio(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download synthesized audio file"""
    
    try:
        # Find audio file
        audio_files = list(Path("temp_audio").glob(f"{job_id}.*"))
        
        if not audio_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found or expired"
            )
        
        audio_file = audio_files[0]
        file_extension = audio_file.suffix[1:]  # Remove dot
        
        # Determine content type
        content_types = {
            'wav': 'audio/wav',
            'mp3': 'audio/mpeg',
            'flac': 'audio/flac'
        }
        content_type = content_types.get(file_extension, 'application/octet-stream')
        
        # Stream the file
        def generate_audio():
            with open(audio_file, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk
        
        filename = f"synthesized_speech_{job_id}.{file_extension}"
        
        return StreamingResponse(
            generate_audio(),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download audio for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download audio file"
        )

@router.get("/preview/{voice_id}")
async def get_voice_preview(
    voice_id: str,
    text: Optional[str] = None
):
    """Generate and stream a voice preview sample"""
    
    try:
        # Generate preview
        result = await tts_engine.generate_voice_preview(voice_id, text)
        
        # Stream preview audio
        def generate_preview():
            yield result.audio_data
        
        return StreamingResponse(
            generate_preview(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"inline; filename=preview_{voice_id}.wav",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to generate preview for voice {voice_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate voice preview"
        )

@router.get("/stats", response_model=TTSStatsResponse)
async def get_tts_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get TTS engine performance statistics"""
    
    try:
        stats = tts_engine.get_synthesis_stats()
        
        return TTSStatsResponse(
            total_requests=stats['total_requests'],
            successful_syntheses=stats['successful_syntheses'],
            failed_syntheses=stats['failed_syntheses'],
            average_processing_time=stats['average_processing_time'],
            average_audio_duration=stats['average_audio_duration'],
            real_time_factor=stats['real_time_factor'],
            cache_stats=stats['cache_stats']
        )
        
    except Exception as e:
        logger.error(f"Failed to get TTS statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.post("/batch-synthesize")
async def batch_synthesize_speech(
    requests: List[ProductionTTSRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Batch processing of multiple TTS requests"""
    
    if len(requests) > 10:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 requests per batch"
        )
    
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    results = []
    
    try:
        logger.info(f"Starting batch synthesis {batch_id} with {len(requests)} requests")
        
        for i, request in enumerate(requests):
            try:
                # Create individual synthesis request
                synthesis_request = SynthesisRequest(
                    text=request.text,
                    voice_id=request.voice_id,
                    output_format=request.output_format,
                    sample_rate=request.sample_rate,
                    speed=request.speed,
                    pitch_shift=request.pitch_shift,
                    emotion=request.emotion,
                    quality=request.quality
                )
                
                # Perform synthesis
                result = await tts_engine.synthesize_speech(synthesis_request)
                job_id = f"{batch_id}_{i}"
                
                # Store audio result
                audio_storage_path = Path(f"temp_audio/{job_id}.{result.format}")
                audio_storage_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(audio_storage_path, 'wb') as f:
                    f.write(result.audio_data)
                
                results.append({
                    'index': i,
                    'success': True,
                    'job_id': job_id,
                    'duration': result.duration,
                    'download_url': f"/api/tts/production/download/{job_id}"
                })
                
            except Exception as e:
                logger.error(f"Batch item {i} failed: {e}")
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })
        
        # Log batch usage in background
        successful_count = sum(1 for r in results if r.get('success'))
        background_tasks.add_task(
            log_batch_usage,
            db=db,
            user_id=current_user.id,
            batch_id=batch_id,
            total_requests=len(requests),
            successful_requests=successful_count
        )
        
        return {
            'batch_id': batch_id,
            'total_requests': len(requests),
            'successful_requests': successful_count,
            'failed_requests': len(requests) - successful_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Batch synthesis failed for {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch synthesis failed"
        )

# Background task functions
def log_synthesis_usage(
    db: Session,
    user_id: int,
    job_id: str,
    voice_id: str,
    text_length: int,
    audio_duration: float,
    processing_time: float,
    quality_score: float
):
    """Log individual synthesis usage"""
    try:
        usage_log = UsageLog(
            user_id=user_id,
            action="tts_synthesize",
            resource_id=job_id,
            metadata={
                'voice_id': voice_id,
                'text_length': text_length,
                'audio_duration': audio_duration,
                'processing_time': processing_time,
                'quality_score': quality_score
            },
            timestamp=datetime.utcnow()
        )
        
        db.add(usage_log)
        db.commit()
        logger.info(f"Logged synthesis usage for job {job_id}")
        
    except Exception as e:
        logger.error(f"Failed to log synthesis usage: {e}")
        db.rollback()

def log_batch_usage(
    db: Session,
    user_id: int,
    batch_id: str,
    total_requests: int,
    successful_requests: int
):
    """Log batch synthesis usage"""
    try:
        usage_log = UsageLog(
            user_id=user_id,
            action="tts_batch_synthesize",
            resource_id=batch_id,
            metadata={
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'success_rate': successful_requests / total_requests
            },
            timestamp=datetime.utcnow()
        )
        
        db.add(usage_log)
        db.commit()
        logger.info(f"Logged batch usage for {batch_id}")
        
    except Exception as e:
        logger.error(f"Failed to log batch usage: {e}")
        db.rollback()

# Health check endpoint
@router.get("/health")
async def health_check():
    """Check TTS engine health"""
    try:
        voices = await tts_engine.get_available_voices()
        stats = tts_engine.get_synthesis_stats()
        
        return {
            'status': 'healthy',
            'available_voices': len(voices),
            'total_requests': stats['total_requests'],
            'success_rate': (
                stats['successful_syntheses'] / max(stats['total_requests'], 1)
            ) * 100,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }