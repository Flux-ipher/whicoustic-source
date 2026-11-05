# Backend Dockerfile optimized for XTTS zero-shot cloning
# Uses Python 3.10 for better compatibility with Coqui TTS

FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps for audio/TTS builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend sources
COPY . /app

# Install minimal dependencies for XTTS zero-shot cloning
# This avoids platform-specific packages from the full requirements.txt
COPY requirements.txt /app/requirements.txt
COPY requirements-xtts.txt /app/requirements-xtts.txt

# Layer 1: PyTorch CPU (~750MB) — cached independently so code changes don't re-download it
RUN python -m pip install --upgrade pip --no-cache-dir \
    && python -m pip install --no-cache-dir \
    torch==2.5.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cpu

# Layer 2: everything else the app needs (sqlalchemy, pydantic, redis, jose, TTS, etc.)
# torch is already installed above so pip skips it here
RUN python -m pip install --no-cache-dir \
    psycopg2-binary==2.9.9 \
    asyncpg==0.29.0 \
    sqlalchemy==2.0.52 \
    alembic==1.13.1 \
    aiosqlite \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    python-jose[cryptography]==3.3.0 \
    python-dotenv==1.0.0 \
    python-multipart==0.0.6 \
    fastapi==0.104.1 \
    "uvicorn[standard]==0.24.0" \
    passlib[bcrypt]==1.7.4 \
    PyJWT==2.8.0 \
    redis==5.0.1 \
    aiofiles==23.2.0 \
    loguru==0.7.2 \
    soundfile>=0.12.1 \
    librosa>=0.10.1 \
    numpy>=1.26.0 \
    scipy>=1.12.0 \
    pydub>=0.25.1 \
    scikit-learn>=1.3.0 \
    joblib>=1.3.0 \
    email-validator>=2.1.0 \
    reedsolo \
    "faster-whisper>=0.10.0" \
    "av<14" \
    "websockets>=12.0" \
    TTS==0.22.0 \
    "transformers<5.0,>=4.36.2"

EXPOSE 8000

# Run the production server
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
