from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from loguru import logger

# VCAAS - Voice Cloning as a Service API
app = FastAPI(
    title="VCAAS API - Voice Cloning as a Service",
    description="Professional AI voice cloning and text-to-speech platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VCAAS API - Voice Cloning as a Service", 
        "version": "1.0.0",
        "description": "Professional AI voice cloning and text-to-speech platform",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "auth": "/api/auth",
            "voices": "/api/voice",
            "tts": "/api/tts"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": "development",
        "version": "1.0.0"
    }


# Simple mock endpoints for testing
@app.get("/api/auth/me")
async def get_current_user():
    """Mock current user endpoint"""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "username": "testuser"
    }


@app.get("/api/voice/samples")
async def get_voice_samples():
    """Mock voice samples endpoint"""
    return {
        "samples": [
            {
                "id": "sample-1",
                "name": "Test Voice Sample",
                "status": "trained",
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]
    }


@app.get("/api/tts/voices")
async def get_available_voices():
    """Mock available voices endpoint"""
    return {
        "owned_voices": [
            {
                "id": "voice-1",
                "name": "Professional Voice",
                "status": "trained",
                "quality": "excellent",
                "can_use": True
            }
        ],
        "licensed_voices": []
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
