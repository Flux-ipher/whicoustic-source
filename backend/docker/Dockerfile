# Whicoustic Backend Dockerfile
# Multi-stage build for production optimization

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    git \
    libsndfile1 \
    libsndfile1-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash whicoustic
USER whicoustic
WORKDIR /home/whicoustic

# Set up Python environment
ENV PATH="/home/whicoustic/.local/bin:$PATH"

# Copy requirements first for better caching
COPY --chown=whicoustic:whicoustic requirements*.txt ./

# Install Python dependencies
RUN pip install --user --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --user --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY --chown=whicoustic:whicoustic . .

# Create necessary directories
RUN mkdir -p data/{uploads,processed_voices,synthesized,models} logs

# Expose port
EXPOSE 8000

# Development command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy application code
COPY --chown=whicoustic:whicoustic . .

# Create necessary directories
RUN mkdir -p data/{uploads,processed_voices,synthesized,models} logs

# Optimize Python bytecode
RUN python -m compileall .

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--max-requests", "1000", "--max-requests-jitter", "50", "--preload"]