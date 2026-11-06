from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from typing import List, Optional
import os


# Host allowlist is required when TrustedHostMiddleware is enabled.
DEFAULT_ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "testserver",
    "whicoustic.onrender.com",
    "*.onrender.com",
    "whicoustic.ai",
    "app.whicoustic.ai",
    "whicoustic.xyz",
    "app.whicoustic.xyz",
    "*.whicoustic.xyz",
]

# CORS - Handled manually to avoid pydantic parsing issues.
# Keep production origins explicitly configured and do not use '*' with credentials.
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://app.localhost:5173",
    "http://localhost:8000",
    "https://whicoustic-rbu8.vercel.app",
    "https://whicoustic.vercel.app",
    "https://whicoustic.ai",
    "https://app.whicoustic.ai",
    "https://whicoustic.xyz",
    "https://app.whicoustic.xyz",
]


def _parse_env_list(raw_value: str | None, fallback: list[str]) -> list[str]:
    if not raw_value or not raw_value.strip():
        return list(fallback)

    value = raw_value.strip()

    try:
        import json
        if value.startswith("["):
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        pass

    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        return list(fallback)

    return list(dict.fromkeys(list(fallback) + items))


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    MOCK_AUTH_ENABLED: bool = Field(default=False, env="MOCK_AUTH_ENABLED")
    PUBLIC_STREAMING_ENABLED: bool = Field(default=False, env="PUBLIC_STREAMING_ENABLED")

    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Whicoustic"
    SECRET_KEY: str = Field(default="", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Database (Supabase PostgreSQL with automatic SQLite fallback)
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./vcaas_dev2.db", env="DATABASE_URL")
    SUPABASE_URL: Optional[str] = Field(default=None, env="SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_DB_URL: Optional[str] = Field(default=None, env="SUPABASE_DB_URL")

    # Google Drive Storage Adapter
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_FOLDER_ID")
    GOOGLE_DRIVE_CREDENTIALS_JSON: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_CREDENTIALS_JSON")
    GOOGLE_DRIVE_CREDENTIALS_PATH: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_CREDENTIALS_PATH")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = Field(default="whicoustic", env="FIREBASE_PROJECT_ID")
    FIREBASE_PRIVATE_KEY_ID: str = Field(default="dummy", env="FIREBASE_PRIVATE_KEY_ID")
    FIREBASE_PRIVATE_KEY: str = Field(default="dummy", env="FIREBASE_PRIVATE_KEY")
    FIREBASE_CLIENT_EMAIL: str = Field(default="dummy", env="FIREBASE_CLIENT_EMAIL")
    FIREBASE_CLIENT_ID: str = Field(default="dummy", env="FIREBASE_CLIENT_ID")
    FIREBASE_AUTH_URI: str = Field(
        default="https://accounts.google.com/o/oauth2/auth",
        env="FIREBASE_AUTH_URI"
    )
    FIREBASE_TOKEN_URI: str = Field(
        default="https://oauth2.googleapis.com/token",
        env="FIREBASE_TOKEN_URI"
    )

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = Field(default="dummy", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="dummy", env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-west-2", env="AWS_REGION")
    AWS_S3_BUCKET: str = Field(default="dummy", env="AWS_S3_BUCKET")

    # TTS Configuration
    TTS_MODEL_PATH: str = Field(default="./models", env="TTS_MODEL_PATH")
    TTS_OUTPUT_PATH: str = Field(default="./audio", env="TTS_OUTPUT_PATH")
    MAX_AUDIO_DURATION: int = Field(default=300, env="MAX_AUDIO_DURATION")  # 5 minutes
    SUPPORTED_AUDIO_FORMATS: List[str] = ["wav", "mp3", "flac", "ogg"]

    # Voice Processing
    SAMPLE_RATE: int = 22050
    HOP_LENGTH: int = 256
    WIN_LENGTH: int = 1024
    N_FFT: int = 1024
    N_MELS: int = 80

    # Watermarking
    WATERMARK_STRENGTH: float = 0.1
    WATERMARK_KEY: str = Field(default="dev-watermark-key-32-bytes-padding", env="WATERMARK_KEY")

    # Celery Configuration
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="voice_clone.log", env="LOG_FILE")

    # Security
    BCRYPT_ROUNDS: int = 12
    JWT_ALGORITHM: str = "HS256"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")

    # File Upload
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_PATH: str = Field(default="./uploads", env="UPLOAD_PATH")

    model_config = SettingsConfigDict(
        env_file=(".env", "env.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Keep ALLOWED_ORIGINS / ALLOWED_HOSTS as runtime attributes instead of model fields,
        # because Render and Vercel inject comma-delimited env strings and they are not valid
        # Pydantic fields for assignment after init.
        object.__setattr__(
            self,
            'ALLOWED_ORIGINS',
            _parse_env_list(os.getenv('ALLOWED_ORIGINS'), DEFAULT_ALLOWED_ORIGINS),
        )
        object.__setattr__(
            self,
            'ALLOWED_HOSTS',
            _parse_env_list(os.getenv('ALLOWED_HOSTS'), DEFAULT_ALLOWED_HOSTS),
        )

    @model_validator(mode="after")
    def validate_security_defaults(self):
        if self.ENVIRONMENT.lower() not in {"development", "test"}:
            if not self.SECRET_KEY or self.SECRET_KEY.startswith("dev-"):
                raise ValueError("SECRET_KEY must be explicitly configured outside development")
            if self.MOCK_AUTH_ENABLED:
                raise ValueError("MOCK_AUTH_ENABLED cannot be enabled outside development")
        return self


# Create settings instance
settings = Settings()
