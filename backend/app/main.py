"""
Main FastAPI application for Whicoustic platform.
Handles routing, middleware, and application lifecycle.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

# Import routers
from .api.v1 import auth, voices, tts, licenses, verify, verify_stream, training
from .api.v1 import otp as otp_routes
from .api.v1 import users as users_routes
from .core.config import settings
from .core.database import create_tables_sync, db_manager
from .services.tts_service import TTSService, tts_service as default_tts_service
from .core.security import set_security_config

set_security_config(settings.SECRET_KEY, settings.JWT_ALGORITHM)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global services
tts_service = default_tts_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global tts_service
    
    # Startup
    logger.info("Starting Whicoustic application...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        create_tables_sync()
        
        # Test database connection
        if db_manager.health_check():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
        
        # Initialize TTS service
        logger.info("Initializing TTS service...")
        tts_service = TTSService()
        await tts_service.initialize()
        
        # Store service in app state
        app.state.tts_service = tts_service
        
        logger.info("Whicoustic application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Whicoustic application...")
    
    try:
        # Cleanup TTS service
        if tts_service:
            await tts_service.cleanup_old_jobs()
        
        logger.info("Whicoustic application shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="Whicoustic",
    description="Creator-first, ethical voice cloning and biometric licensing platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted host middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Custom middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.3f}s"
        )
        raise

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        },
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": request.url.path,
            "method": request.method,
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

# Include API routers
app.include_router(
    auth.router,
    prefix="/api/v1",
    tags=["Authentication"]
)
app.include_router(
    otp_routes.router,
    prefix="/api/v1",
    tags=["Authentication"]
)
app.include_router(
    users_routes.router,
    prefix="/api/v1",
    tags=["Users"]
)

app.include_router(
    voices.router,
    prefix="/api/v1",
    tags=["Voice Management"]
)

app.include_router(
    tts.router,
    prefix="/api/v1",
    tags=["Text-to-Speech"]
)

# Back-compat alias for frontend expecting /api/tts/clone paths
from .api.v1.tts import clone_speech as v1_clone_speech, clone_warmup as v1_clone_warmup
app.add_api_route("/api/tts/clone", v1_clone_speech, methods=["POST"], tags=["Text-to-Speech"])
app.add_api_route("/api/tts/clone/warmup", v1_clone_warmup, methods=["POST"], tags=["Text-to-Speech"])

app.include_router(
    licenses.router,
    prefix="/api/v1",
    tags=["Licensing"]
)

app.include_router(
    verify.router,
    prefix="/api/v1",
    tags=["Watermark Verification"]
)

app.include_router(
    verify_stream.router,
    prefix="/api/v1",
    tags=["Real-Time Streaming"]
)
app.include_router(
    training.router,
    prefix="/api/v1/training",
    tags=["Voice Training"]
)

# Root endpoints
@app.get("/live", response_class=HTMLResponse)
async def live_dashboard():
    """Live interactive voice verification and streaming deepfake detection UI."""
    import os
    html_path = os.path.join(os.path.dirname(__file__), "static", "live_test.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Live dashboard template not found</h1>", status_code=404)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Whicoustic",
        "version": "1.0.0",
        "description": "Creator-first, ethical voice cloning and biometric licensing platform",
        "features": [
            "Voice upload and processing",
            "Few-shot voice cloning",
            "Inaudible watermarking",
            "Licensing system",
            "Usage analytics",
            "Watermark verification"
        ],
        "docs_url": "/docs" if settings.ENVIRONMENT == "development" else None,
        "api_version": "v1",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "voices": "/api/v1/voices",
            "tts": "/api/v1/tts", 
            "licenses": "/api/v1/licenses",
            "verification": "/api/v1/verify"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        db_healthy = db_manager.health_check()
        
        # Check TTS service
        tts_healthy = tts_service is not None and tts_service.inference_engine is not None
        
        # Overall health
        healthy = db_healthy and tts_healthy
        
        return {
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": time.time(),
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "tts": "healthy" if tts_healthy else "unhealthy",
                "defense_engine": {
                    "layer1_acoustic": True,
                    "layer2_biometrics": True,
                    "layer3_prosody": True,
                    "layer4_paralinguistic": True,
                    "layer5_whisper": True,
                    "layer6_watermark": True,
                    "streaming_websocket": getattr(settings, "PUBLIC_STREAMING_ENABLED", False) or settings.ENVIRONMENT == "development"
                }
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e) if settings.DEBUG else "Health check failed",
            "version": "1.0.0"
        }

@app.get("/stats")
async def get_system_stats():
    """Get system statistics."""
    try:
        stats = {
            "application": {
                "name": "Whicoustic",
                "version": "1.0.0",
                "environment": "development" if settings.DEBUG else "production"
            },
            "database": {
                "connection_info": db_manager.get_connection_info(),
                "healthy": db_manager.health_check()
            }
        }
        
        # Add TTS service stats if available
        if tts_service:
            stats["tts_service"] = tts_service.get_service_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics")

@app.get("/api/v1/info")
async def api_info():
    """API version information."""
    return {
        "api_version": "v1",
        "features": {
            "authentication": {
                "methods": ["JWT", "API Keys"],
                "endpoints": ["/auth/register", "/auth/login", "/auth/profile"]
            },
            "voice_management": {
                "supported_formats": ["wav", "mp3", "flac", "m4a"],
                "max_duration": "5 minutes",
                "quality_checks": ["VAD", "SNR", "Spectral Analysis"]
            },
            "text_to_speech": {
                "engine": "Coqui TTS",
                "voice_cloning": "YourTTS",
                "watermarking": ["MVP Sine", "Robust Spread-Spectrum"]
            },
            "licensing": {
                "types": ["Personal", "Commercial", "Enterprise", "Educational"],
                "token_based": True,
                "usage_tracking": True
            },
            "verification": {
                "watermark_detection": ["MVP", "Robust", "Auto-Detect"],
                "forensic_analysis": True,
                "batch_processing": True
            }
        },
        "limits": {
            "free_tier": {
                "voices_per_month": 3,
                "syntheses_per_month": 100,
                "max_audio_length": 300
            },
            "premium_tier": {
                "voices_per_month": 50,
                "syntheses_per_month": 10000,
                "max_audio_length": 1800
            }
        }
    }

# Development endpoints (only in debug mode)
if settings.DEBUG:
    @app.get("/debug/config")
    async def debug_config():
        """Debug configuration (development only)."""
        return {
            "debug": settings.DEBUG,
            "database_url": settings.DATABASE_URL.replace(settings.DATABASE_URL.split('@')[0].split('/')[-1], '***'),
            "allowed_origins": settings.ALLOWED_ORIGINS,
            "environment": "development"
        }
    
    @app.post("/debug/test-tts")
    async def debug_test_tts(text: str = "Hello, this is a test"):
        """Test TTS service (development only)."""
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS service not available")
        
        try:
            # Test synthesis with fallback voice
            audio_path = await tts_service.synthesize_text(
                text=text,
                voice_id="test_voice",
                speaker_embedding=None
            )
            
            return {
                "message": "TTS test completed successfully",
                "audio_path": audio_path,
                "text": text
            }
            
        except Exception as e:
            logger.error(f"TTS test failed: {e}")
            raise HTTPException(status_code=500, detail=f"TTS test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )