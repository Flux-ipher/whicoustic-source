"""
File Upload Service (Stubbed for SQL/No-Mongo mode)

Handles audio file uploads, validation, storage, and processing.
"""

import uuid
from typing import Optional, Dict, Any, List
from fastapi import UploadFile
from loguru import logger

class FileUploadService:
    """Stubbed Service for handling file uploads"""
    
    def __init__(self):
        pass
    
    def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        return {"valid": True, "file_info": {"filename": file.filename}}
    
    async def upload_voice_sample(
        self, 
        file: UploadFile, 
        user_id: str,
        transcription: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload and process a voice sample (Mock)"""
        logger.warning(f"Mock upload_voice_sample called for user {user_id}")
        return {
            "valid": True,
            "voice_sample_id": str(uuid.uuid4()),
            "file_info": {
                "duration": 5.0,
                "file_size": 1024,
                "sample_rate": 44100,
                "format": "wav"
            },
            "quality_analysis": {
                "overall_score": 0.9,
                "is_suitable_for_training": True,
                "recommendations": []
            },
            "message": "File uploaded (MOCK)"
        }
    
    async def get_upload_stats(self, user_id: str) -> Dict[str, Any]:
        """Get upload statistics for user (Mock)"""
        return {
            "total_samples": 5,
            "suitable_for_training": 3,
            "total_duration_minutes": 2.5,
            "average_quality_score": 0.85,
            "total_storage_mb": 15.0,
            "limits": {
                "max_samples": 10,
                "remaining_samples": 5
            }
        }
    
    async def delete_voice_sample(self, sample_id: str, user_id: str) -> bool:
        """Delete a voice sample (Mock)"""
        logger.warning(f"Mock delete_voice_sample called for {sample_id}")
        return True
    
    async def cleanup_old_files(self, max_age_days: int = 30):
        """Clean up old files (Mock)"""
        return 0


# Global file upload service instance
file_upload_service = FileUploadService()