import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid
import mimetypes
from io import BytesIO

from app.core.config import settings


class S3StorageService:
    """AWS S3 storage service for audio files"""
    
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.AWS_S3_BUCKET
            self._test_connection()
        except (NoCredentialsError, Exception) as e:
            print(f"S3 initialization failed: {e}. Falling back to local storage.")
            self.s3_client = None
            self.bucket_name = None
    
    def _test_connection(self):
        """Test S3 connection and bucket access"""
        if self.s3_client:
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
            except ClientError:
                print(f"Cannot access S3 bucket {self.bucket_name}. Check permissions.")
    
    async def upload_audio_file(
        self,
        file_path: str,
        user_id: str,
        file_type: str = "voice_sample",
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload audio file to S3 or local storage"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"success": False, "error": "File not found"}
            
            # Generate unique filename
            file_extension = file_path_obj.suffix
            unique_filename = f"{file_type}/{user_id}/{uuid.uuid4().hex}{file_extension}"
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = "audio/wav"
            
            if self.s3_client:
                # Upload to S3
                return await self._upload_to_s3(file_path, unique_filename, content_type)
            else:
                # Fallback to local storage
                return await self._upload_to_local(file_path, unique_filename, content_type)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _upload_to_s3(self, file_path: str, s3_key: str, content_type: str) -> Dict[str, Any]:
        """Upload file to S3"""
        try:
            # Read file
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ServerSideEncryption='AES256',
                Metadata={
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'original_filename': Path(file_path).name
                }
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            
            return {
                "success": True,
                "url": url,
                "storage_path": s3_key,
                "storage_type": "s3",
                "file_size": len(file_content)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _upload_to_local(self, file_path: str, relative_path: str, content_type: str) -> Dict[str, Any]:
        """Upload file to local storage as fallback"""
        try:
            # Create storage directory
            storage_root = Path(settings.UPLOAD_PATH)
            storage_root.mkdir(parents=True, exist_ok=True)
            
            # Create destination path
            dest_path = storage_root / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            async with aiofiles.open(file_path, 'rb') as src:
                content = await src.read()
                async with aiofiles.open(dest_path, 'wb') as dst:
                    await dst.write(content)
            
            # Generate local URL
            url = f"/files/{relative_path}"
            
            return {
                "success": True,
                "url": url,
                "storage_path": str(dest_path),
                "storage_type": "local",
                "file_size": len(content)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_file(self, storage_path: str, storage_type: str = "s3") -> Dict[str, Any]:
        """Delete file from storage"""
        try:
            if storage_type == "s3" and self.s3_client:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )
            else:
                # Local storage
                file_path = Path(storage_path)
                if file_path.exists():
                    await aiofiles.os.remove(file_path)
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600,
        storage_type: str = "s3"
    ) -> Optional[str]:
        """Generate presigned URL for file access"""
        try:
            if storage_type == "s3" and self.s3_client:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': storage_path},
                    ExpiresIn=expiration
                )
                return url
            else:
                # For local storage, return direct path
                return f"/files/{storage_path}"
                
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    async def get_file_info(self, storage_path: str, storage_type: str = "s3") -> Dict[str, Any]:
        """Get file information"""
        try:
            if storage_type == "s3" and self.s3_client:
                response = self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )
                return {
                    "success": True,
                    "size": response['ContentLength'],
                    "last_modified": response['LastModified'],
                    "content_type": response.get('ContentType', 'unknown'),
                    "metadata": response.get('Metadata', {})
                }
            else:
                # Local storage
                file_path = Path(storage_path)
                if file_path.exists():
                    stat = file_path.stat()
                    return {
                        "success": True,
                        "size": stat.st_size,
                        "last_modified": datetime.fromtimestamp(stat.st_mtime),
                        "content_type": mimetypes.guess_type(str(file_path))[0] or 'unknown'
                    }
                else:
                    return {"success": False, "error": "File not found"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}


class LocalStorageService:
    """Local file storage service as fallback"""
    
    def __init__(self):
        self.storage_root = Path(settings.UPLOAD_PATH)
        self.storage_root.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file_content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
        """Save uploaded file to local storage"""
        try:
            # Create user directory
            user_dir = self.storage_root / user_id
            user_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            file_extension = Path(filename).suffix
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = user_dir / unique_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "url": f"/files/{user_id}/{unique_filename}",
                "file_size": len(file_content)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete file from local storage"""
        try:
            path = Path(file_path)
            if path.exists():
                await aiofiles.os.remove(path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global storage service instances
s3_storage = S3StorageService()
local_storage = LocalStorageService()


def get_storage_service() -> Union[S3StorageService, LocalStorageService]:
    """Get appropriate storage service based on configuration"""
    if s3_storage.s3_client:
        return s3_storage
    else:
        return local_storage
