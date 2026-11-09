"""
Voice management endpoints for Whicoustic API v1.
Handles voice upload, processing, cloning, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Header, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

from ...core.database import get_db
from ...core.config import settings
from ...core.rate_limit import rate_limit_streaming
from ...services.google_drive_storage import get_google_drive_storage
from ...services.voice_processor import VoiceProcessor
from ...services.audio_processor import AudioProcessor
from ...services.voice_training_service import voice_training_service
from ...models.user import User
from ...models.voice import Voice
from .auth import get_current_user
from ...schemas.voice import (
    VoiceCreate,
    VoiceResponse,
    VoiceUpdate,
    VoiceUploadResponse
)

router = APIRouter(prefix="/voices", tags=["voice-management"])

@router.post("/upload", response_model=VoiceUploadResponse)
@router.post("/upload/", response_model=VoiceUploadResponse)
async def upload_voice(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a voice sample for processing and cloning."""
    
    # Validate file type and extension
    allowed_mimes = {
        'audio/wav', 'audio/x-wav', 'audio/wave',
        'audio/mpeg', 'audio/mp3', 'audio/x-mp3',
        'audio/flac', 'audio/x-flac',
        'audio/m4a', 'audio/x-m4a', 'audio/mp4', 'audio/aac',
        'audio/ogg', 'audio/webm',
    }
    allowed_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.mp4', '.aac', '.ogg', '.webm', '.wma'}

    file_ext = os.path.splitext(file.filename or '')[1].lower()
    raw_content_type = (file.content_type or '').split(';')[0].strip().lower()

    is_valid_mime = raw_content_type in allowed_mimes
    is_valid_ext = file_ext in allowed_extensions

    if not (is_valid_mime or is_valid_ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{raw_content_type or file_ext}'. Supported formats: MP3, WAV, FLAC, M4A, OGG, WEBM."
        )

    # Save uploaded file temporarily with normalized extension
    safe_suffix = file_ext if file_ext in allowed_extensions else '.wav'
    with tempfile.NamedTemporaryFile(delete=False, suffix=safe_suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Process audio
        audio_processor = AudioProcessor()
        audio_info = await audio_processor.get_audio_info_from_path(temp_file_path)

        duration = audio_info.get('duration') or audio_info.get('estimated_duration') or 0.0

        # Validate audio duration
        if duration < 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio sample is too short ({duration:.1f}s). Please provide at least 1 second of audio."
            )

        if duration > 300:  # Maximum 5 minutes
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio sample is too long ({duration:.1f}s). Audio must be less than 5 minutes long."
            )
        
        # Generate unique voice ID
        voice_id = f"voice_{uuid.uuid4().hex[:12]}"
        
        # Pre-upload raw audio file to persistent Google Drive / local storage adapter
        storage = get_google_drive_storage()
        raw_storage_id = None
        try:
            raw_upload = await storage.upload_file(
                file_path=temp_file_path,
                file_name=f"raw_{voice_id}_{file.filename or 'sample.wav'}",
                mime_type=file.content_type or "audio/wav"
            )
            if raw_upload.get("success"):
                raw_storage_id = raw_upload.get("file_id")
        except Exception as store_err:
            logger.warning(f"Initial raw audio storage upload deferred to background: {store_err}")

        # Create voice record in database as pending/processing
        voice = Voice(
            id=voice_id,
            user_id=current_user.id,
            name=name or f"Voice {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=description,
            original_filename=file.filename,
            file_path=raw_storage_id,
            speaker_embedding=None,
            duration=duration,
            sample_rate=audio_info.get('sample_rate') or 16000,
            file_size=audio_info.get('file_size_bytes') or (os.path.getsize(temp_file_path) if os.path.exists(temp_file_path) else 0),
            status='pending',
            quality_score=audio_info.get('quality_score', 0.85)
        )
        
        db.add(voice)
        db.commit()
        db.refresh(voice)
        
        # Start background processing
        await voice_training_service.start_training(voice.id, temp_file_path)
        
        return VoiceUploadResponse(
            voice_id=voice.id,
            name=voice.name,
            status=voice.status,
            duration=voice.duration,
            quality_score=voice.quality_score,
            upload_time=voice.created_at,
            next_steps="Voice is currently processing. You can check its status later."
        )
        
    except Exception as e:
        # Clean up temporary file only on immediate error
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise e

@router.get("", response_model=List[VoiceResponse])
@router.get("/", response_model=List[VoiceResponse])
async def list_voices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all voices belonging to the current user."""
    voices = db.query(Voice).filter(Voice.user_id == current_user.id).all()
    
    return [
        VoiceResponse(
            id=voice.id,
            name=voice.name,
            description=voice.description,
            status=voice.status,
            duration=voice.duration,
            quality_score=voice.quality_score,
            created_at=voice.created_at,
            updated_at=voice.updated_at
        )
        for voice in voices
    ]

@router.get("/{voice_id}", response_model=VoiceResponse)
@router.get("/{voice_id}/", response_model=VoiceResponse)
async def get_voice(
    voice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific voice."""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found"
        )
    
    return VoiceResponse(
        id=voice.id,
        name=voice.name,
        description=voice.description,
        status=voice.status,
        duration=voice.duration,
        quality_score=voice.quality_score,
        created_at=voice.created_at,
        updated_at=voice.updated_at,
        sample_rate=voice.sample_rate,
        file_size=voice.file_size
    )

@router.put("/{voice_id}", response_model=VoiceResponse)
@router.put("/{voice_id}/", response_model=VoiceResponse)
async def update_voice(
    voice_id: str,
    voice_update: VoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update voice metadata."""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found"
        )
    
    # Update fields if provided
    if voice_update.name is not None:
        voice.name = voice_update.name
    if voice_update.description is not None:
        voice.description = voice_update.description
    
    voice.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(voice)
    
    return VoiceResponse(
        id=voice.id,
        name=voice.name,
        description=voice.description,
        status=voice.status,
        duration=voice.duration,
        quality_score=voice.quality_score,
        created_at=voice.created_at,
        updated_at=voice.updated_at
    )

@router.delete("/{voice_id}")
@router.delete("/{voice_id}/")
async def delete_voice(
    voice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a voice and its associated files."""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found"
        )
    
    # Clean up files
    if voice.file_path and os.path.exists(voice.file_path):
        os.unlink(voice.file_path)
    
    # Delete from database
    db.delete(voice)
    db.commit()
    
    return {"message": "Voice deleted successfully"}

@router.get("/{voice_id}/stream", dependencies=[Depends(rate_limit_streaming)])
@router.get("/{voice_id}/stream/", dependencies=[Depends(rate_limit_streaming)])
async def stream_voice_audio(
    voice_id: str,
    request: Request,
    range_header: Optional[str] = Header(None, alias="Range"),
    db: Session = Depends(get_db)
):
    """
    Proxy stream voice audio with HTTP range request support via Google Drive adapter or local fallback.
    Supports HTTP 206 Partial Content for efficient seeking and player streaming.
    """
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found"
        )

    if not voice.file_path:
        # Check standard processing directories for fallback repair
        for p in [
            Path("data/processed_voices") / f"{voice.id}_processed.wav",
            Path("uploads") / f"{voice.id}_processed.wav",
            Path("data/synthesized") / f"synthesis_{voice.id}.wav"
        ]:
            if p.exists():
                voice.file_path = str(p)
                db.commit()
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not configured for this voice"
            )

    storage = get_google_drive_storage()
    meta = await storage.get_file_metadata(voice.file_path)

    if not meta.get("success"):
        if not os.path.exists(voice.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found"
            )
        file_size = os.path.getsize(voice.file_path)
        mime_type = "audio/wav"
    else:
        file_size = meta["size"]
        mime_type = meta.get("mime_type", "audio/wav")

    if file_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file is empty"
        )

    start = 0
    end = file_size - 1
    status_code = status.HTTP_200_OK

    if range_header and range_header.startswith("bytes="):
        range_val = range_header[len("bytes="):].strip()
        if "," in range_val:
            range_val = range_val.split(",")[0].strip()
        parts = range_val.split("-")
        if len(parts) == 2:
            prefix_str, suffix_str = parts[0].strip(), parts[1].strip()
            if not prefix_str and suffix_str:
                # Suffix byte range: bytes=-N indicates the last N bytes (RFC 9110 Section 14.1.2)
                try:
                    suffix_len = int(suffix_str)
                except ValueError:
                    suffix_len = None

                if suffix_len is not None:
                    if suffix_len <= 0:
                        raise HTTPException(
                            status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
                            detail="Requested range not satisfiable",
                            headers={"Content-Range": f"bytes */{file_size}"}
                        )
                    # RFC 9110: If file_size <= suffix_length, range corresponds to entire representation
                    start = max(0, file_size - suffix_len)
                    end = file_size - 1
                    status_code = status.HTTP_206_PARTIAL_CONTENT

            elif prefix_str:
                # Prefix range: bytes=N- or bytes=N-M (RFC 9110 Section 14.1.2)
                try:
                    start_val = int(prefix_str)
                except ValueError:
                    start_val = None

                if start_val is not None:
                    if start_val < 0 or start_val >= file_size:
                        raise HTTPException(
                            status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
                            detail="Requested range not satisfiable",
                            headers={"Content-Range": f"bytes */{file_size}"}
                        )
                    start = start_val
                    if suffix_str:
                        try:
                            end_val = int(suffix_str)
                        except ValueError:
                            end_val = None
                        if end_val is not None:
                            if end_val < start:
                                raise HTTPException(
                                    status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
                                    detail="Requested range not satisfiable",
                                    headers={"Content-Range": f"bytes */{file_size}"}
                                )
                            # RFC 9110: If last-byte-pos >= file_size, clamp to file_size - 1
                            end = min(end_val, file_size - 1)
                        else:
                            end = file_size - 1
                    else:
                        end = file_size - 1
                    status_code = status.HTTP_206_PARTIAL_CONTENT

    content_length = end - start + 1

    async def range_stream_generator():
        chunk_size = 64 * 1024
        current_pos = 0
        bytes_to_send = content_length

        async for chunk in storage.get_file_stream(voice.file_path, chunk_size=chunk_size):
            chunk_len = len(chunk)
            chunk_start = current_pos
            chunk_end = current_pos + chunk_len

            if chunk_end <= start:
                current_pos = chunk_end
                continue
            if chunk_start > end or bytes_to_send <= 0:
                break

            slice_start = max(0, start - chunk_start)
            slice_end = min(chunk_len, slice_start + bytes_to_send)
            data_to_yield = chunk[slice_start:slice_end]
            bytes_to_send -= len(data_to_yield)
            current_pos = chunk_end
            yield data_to_yield

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": mime_type,
    }
    if status_code == status.HTTP_206_PARTIAL_CONTENT:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    return StreamingResponse(
        range_stream_generator(),
        status_code=status_code,
        media_type=mime_type,
        headers=headers,
    )


@router.get("/{voice_id}/preview", dependencies=[Depends(rate_limit_streaming)])
@router.get("/{voice_id}/preview/", dependencies=[Depends(rate_limit_streaming)])
async def get_voice_preview(
    voice_id: str,
    request: Request,
    range_header: Optional[str] = Header(None, alias="Range"),
    db: Session = Depends(get_db)
):
    """
    Get a preview of the voice sample via Google Drive adapter or local storage streaming.
    Supports HTTP 206 Partial Content range requests and standard audio players.
    """
    return await stream_voice_audio(
        voice_id=voice_id,
        request=request,
        range_header=range_header,
        db=db
    )


@router.post("/{voice_id}/clone-test")
@router.post("/{voice_id}/clone-test/")
async def test_voice_clone(
    voice_id: str,
    text: str = "Hello, this is a test of your cloned voice.",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test voice cloning with a short phrase."""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice not found"
        )
    
    # Initialize voice processor
    voice_processor = VoiceProcessor()
    
    # Generate test audio
    test_audio_path = await voice_processor.synthesize_speech(
        text=text,
        voice_id=voice_id,
        speaker_embedding=voice.speaker_embedding
    )
    
    # Upload synthesized test audio to storage adapter if configured
    try:
        storage = get_google_drive_storage()
        await storage.upload_file(
            file_path=test_audio_path,
            file_name=f"test_{voice.name or voice_id}.wav",
            mime_type="audio/wav"
        )
    except Exception as drive_err:
        logger.warning(f"Could not upload test audio to Google Drive storage: {drive_err}")
    
    return FileResponse(
        test_audio_path,
        media_type="audio/wav",
        filename=f"{voice.name}_test.wav"
    )
