"""
Google Drive storage adapter for Whicoustic platform.
Stores raw vocal recordings and synthesized audio in Google Drive,
with automatic resilient fallback to local storage when credentials or folder ID are unset.
"""

from __future__ import annotations

import io
import os
import shutil
import uuid
import mimetypes
import logging
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator

import aiofiles
import aiofiles.os

from app.core.config import settings

logger = logging.getLogger(__name__)

# Optional Google client libraries guard
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from google.oauth2 import service_account
    from google.auth.exceptions import GoogleAuthError
    HAS_GOOGLE_LIBS = True
except ImportError:
    HAS_GOOGLE_LIBS = False
    build = None
    MediaFileUpload = None
    MediaIoBaseDownload = None
    service_account = None


class GoogleDriveStorageService:
    """Storage adapter integrating Google Drive API with local storage fallback."""

    def __init__(
        self,
        folder_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        upload_path: Optional[str] = None,
    ):
        self.folder_id = folder_id or getattr(settings, "GOOGLE_DRIVE_FOLDER_ID", None)
        self.credentials_json = credentials_json or getattr(settings, "GOOGLE_DRIVE_CREDENTIALS_JSON", None)
        self.credentials_path = credentials_path or getattr(settings, "GOOGLE_DRIVE_CREDENTIALS_PATH", None)
        self.upload_path = Path(upload_path or getattr(settings, "UPLOAD_PATH", "./uploads"))
        self.upload_path.mkdir(parents=True, exist_ok=True)

        self.drive_service = None
        self._is_drive_active = False

        self._initialize_client()

    def _initialize_client(self):
        """Attempt to initialize the Google Drive API client; fall back to local if unavailable."""
        if not HAS_GOOGLE_LIBS:
            logger.info("Google client libraries not installed. Using local storage fallback.")
            self._is_drive_active = False
            return

        if not self.folder_id:
            logger.info("GOOGLE_DRIVE_FOLDER_ID is unset. Using local storage fallback.")
            self._is_drive_active = False
            return

        try:
            creds = None
            scopes = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

            if self.credentials_json:
                import json
                info = json.loads(self.credentials_json) if isinstance(self.credentials_json, str) else self.credentials_json
                creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
            elif self.credentials_path and os.path.exists(self.credentials_path):
                creds = service_account.Credentials.from_service_account_file(self.credentials_path, scopes=scopes)

            if creds:
                self.drive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
                # Verify folder access
                self.drive_service.files().get(fileId=self.folder_id, fields="id, name").execute()
                self._is_drive_active = True
                logger.info(f"Google Drive storage adapter initialized successfully with folder {self.folder_id}.")
            else:
                logger.info("No valid Google Drive credentials provided. Using local storage fallback.")
                self._is_drive_active = False
        except Exception as exc:
            logger.warning(
                f"Google Drive initialization failed ({exc}). Falling back to local storage adapter."
            )
            self.drive_service = None
            self._is_drive_active = False

    @property
    def is_drive_active(self) -> bool:
        """Return True if connected to Google Drive API, False if operating on local fallback."""
        return self._is_drive_active

    async def upload_file(
        self,
        file_path: str,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload file to Google Drive or local storage fallback."""
        path_obj = Path(file_path)
        if not path_obj.exists():
            return {"success": False, "error": f"Source file does not exist: {file_path}"}

        target_name = file_name or path_obj.name
        guessed_type, _ = mimetypes.guess_type(target_name)
        target_mime = mime_type or guessed_type or "audio/wav"
        file_size = path_obj.stat().st_size

        if self._is_drive_active and self.drive_service:
            try:
                target_folder = folder_id or self.folder_id
                file_metadata = {
                    "name": target_name,
                    "parents": [target_folder] if target_folder else [],
                }
                media = MediaFileUpload(str(path_obj), mimetype=target_mime, resumable=True)
                created = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, mimeType, size, webViewLink, webContentLink",
                ).execute()

                return {
                    "success": True,
                    "file_id": created.get("id"),
                    "file_name": created.get("name"),
                    "mime_type": created.get("mimeType", target_mime),
                    "file_size": int(created.get("size", file_size)),
                    "storage_type": "google_drive",
                    "web_view_link": created.get("webViewLink"),
                    "web_content_link": created.get("webContentLink"),
                }
            except Exception as exc:
                logger.warning(f"Google Drive upload failed ({exc}). Falling back to local storage for this file.")

        # Local storage fallback
        try:
            unique_prefix = uuid.uuid4().hex[:12]
            dest_filename = f"{unique_prefix}_{target_name}"
            dest_path = self.upload_path / dest_filename

            async with aiofiles.open(path_obj, "rb") as src:
                content = await src.read()
                async with aiofiles.open(dest_path, "wb") as dst:
                    await dst.write(content)

            file_id = f"local_{unique_prefix}_{target_name}"
            return {
                "success": True,
                "file_id": file_id,
                "file_path": str(dest_path),
                "file_name": target_name,
                "mime_type": target_mime,
                "file_size": len(content),
                "storage_type": "local",
                "web_view_link": f"/files/{dest_filename}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def download_file(self, file_id: str, dest_path: str) -> bool:
        """Download file from Google Drive or copy from local storage to destination."""
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if self._is_drive_active and self.drive_service and not file_id.startswith("local_"):
            try:
                request = self.drive_service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                fh.seek(0)
                async with aiofiles.open(dest, "wb") as f:
                    await f.write(fh.read())
                return True
            except Exception as exc:
                logger.warning(f"Google Drive download failed ({exc}). Trying local fallback.")

        # Local fallback resolution
        local_candidate = self._resolve_local_file_path(file_id)
        if local_candidate and local_candidate.exists():
            shutil.copy2(local_candidate, dest)
            return True

        return False

    async def get_file_stream(self, file_id: str, chunk_size: int = 64 * 1024) -> AsyncGenerator[bytes, None]:
        """Yield chunks of bytes for the given file_id from Google Drive or local storage."""
        if self._is_drive_active and self.drive_service and not file_id.startswith("local_"):
            try:
                request = self.drive_service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                fh.seek(0)
                while True:
                    chunk = fh.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
                return
            except Exception as exc:
                logger.warning(f"Google Drive streaming failed ({exc}). Falling back to local.")

        # Local fallback
        local_candidate = self._resolve_local_file_path(file_id)
        if local_candidate and local_candidate.exists():
            async with aiofiles.open(local_candidate, "rb") as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        else:
            raise FileNotFoundError(f"Audio file with ID or path '{file_id}' not found")

    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Retrieve metadata for a file in Google Drive or local storage."""
        if self._is_drive_active and self.drive_service and not file_id.startswith("local_"):
            try:
                meta = self.drive_service.files().get(
                    fileId=file_id,
                    fields="id, name, mimeType, size, createdTime, modifiedTime",
                ).execute()
                return {
                    "success": True,
                    "file_id": meta.get("id"),
                    "name": meta.get("name"),
                    "mime_type": meta.get("mimeType"),
                    "size": int(meta.get("size", 0)),
                    "storage_type": "google_drive",
                    "created_time": meta.get("createdTime"),
                }
            except Exception as exc:
                logger.warning(f"Failed to fetch metadata from Google Drive ({exc}). Checking local.")

        local_candidate = self._resolve_local_file_path(file_id)
        if local_candidate and local_candidate.exists():
            stat = local_candidate.stat()
            guessed_mime, _ = mimetypes.guess_type(local_candidate.name)
            return {
                "success": True,
                "file_id": file_id,
                "name": local_candidate.name,
                "mime_type": guessed_mime or "audio/wav",
                "size": stat.st_size,
                "storage_type": "local",
                "created_time": stat.st_ctime,
            }

        return {"success": False, "error": f"File '{file_id}' not found"}

    def _resolve_local_file_path(self, file_id: str) -> Optional[Path]:
        """Locate a local file from an ID, absolute path, or upload directory file."""
        # Direct path check
        direct = Path(file_id)
        if direct.exists() and direct.is_file():
            return direct

        # Check in upload path
        candidate = self.upload_path / file_id
        if candidate.exists() and candidate.is_file():
            return candidate

        # Check if stripped of local_ prefix
        if file_id.startswith("local_"):
            sub = file_id[len("local_"):]
            cand2 = self.upload_path / sub
            if cand2.exists() and cand2.is_file():
                return cand2
            # Try fuzzy search in upload_path
            for f in self.upload_path.iterdir():
                if f.is_file() and (sub in f.name or f.name.endswith(sub)):
                    return f

        # Search recursively in upload_path
        for f in self.upload_path.rglob("*"):
            if f.is_file() and f.name == file_id:
                return f

        return None


# Global singleton instance
google_drive_storage = GoogleDriveStorageService()


def get_google_drive_storage() -> GoogleDriveStorageService:
    """Dependency / accessor for the Google Drive storage service."""
    return google_drive_storage
