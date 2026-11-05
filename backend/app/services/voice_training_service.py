"""
Voice Training Service

Manages the background processing of voice uploads,
including audio preprocessing, embedding extraction, and DB status tracking.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from pathlib import Path
from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import SyncSessionLocal
from app.models.user import User
from app.models.voice import Voice
from app.services.voice_processor import VoiceProcessor

class VoiceTrainingService:
    """SQLite-backed voice training service for long-running processing."""
    
    def __init__(self):
        self.training_queue = asyncio.Queue()
        self.is_processing = False

    async def start_training(self, voice_id: str, temp_file_path: str):
        """Enqueue a voice for processing."""
        await self.training_queue.put({
            "voice_id": voice_id,
            "temp_file_path": temp_file_path
        })
        
        if not self.is_processing:
            asyncio.create_task(self._process_training_queue())
            
        logger.info(f"Enqueued training job for voice {voice_id}")

    async def _process_training_queue(self):
        self.is_processing = True
        
        try:
            while True:
                try:
                    # Get next job (wait up to 10 seconds, then check again)
                    job = await asyncio.wait_for(self.training_queue.get(), timeout=10.0)
                    await self._execute_training_job(job)
                except asyncio.TimeoutError:
                    if self.training_queue.empty():
                        break
                except Exception as e:
                    logger.error(f"Error in training queue processing: {e}")
        finally:
            self.is_processing = False

    async def _execute_training_job(self, job: Dict[str, Any]):
        voice_id = job["voice_id"]
        temp_file_path = job["temp_file_path"]
        
        try:
            db = SyncSessionLocal()
            try:
                voice = db.query(Voice).filter(Voice.id == voice_id).first()
                if not voice:
                    logger.error(f"Voice {voice_id} not found in DB")
                    return
                
                # Update status to processing
                voice.status = "processing"
                db.commit()
                
                logger.info(f"Starting processing for voice {voice_id}")
                
                # Simulate a little delay if no GPUs
                await asyncio.sleep(2)
                
                # Initialize voice processor
                voice_processor = VoiceProcessor()
                
                # Preprocess audio (denoise, normalize, extract features)
                processed_audio_path = await voice_processor.preprocess_audio(
                    temp_file_path, 
                    voice_id
                )
                
                # Extract speaker embedding
                speaker_embedding = await voice_processor.extract_speaker_embedding(
                    processed_audio_path
                )
                
                # Finalize
                voice.status = "ready"
                voice.file_path = processed_audio_path
                voice.speaker_embedding = speaker_embedding.tolist()
                voice.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Completed processing for voice {voice_id}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Training job {voice_id} failed: {e}")
            try:
                db = SyncSessionLocal()
                try:
                    voice = db.query(Voice).filter(Voice.id == voice_id).first()
                    if voice:
                        voice.status = "failed"
                        db.commit()
                finally:
                    db.close()
            except Exception as inner_e:
                logger.error(f"Could not update voice status to failed: {inner_e}")
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

voice_training_service = VoiceTrainingService()