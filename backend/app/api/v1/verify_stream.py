"""
Real-Time Streaming Deepfake Detection — WebSocket endpoint.

Path: ws://host/api/v1/verify/stream

Protocol:
  Client → Server:
    Binary frames of raw 16-bit signed PCM, mono, 16kHz.
    The recommended frame is exactly 30ms = 480 samples = 960 bytes at 16kHz.
    The client may send frames of any size; the session handles frame
    alignment internally.

  Server → Client:
    JSON text frames on each speech-containing analysis window:
    {
      "overall_authenticity_score": 0.72,
      "verdict": "Suspicious (Likely Human)",
      "is_authentic": true,
      "confidence": 0.60,
      "buffer_seconds": 3.2,
      "samples_processed": 51200,
      "layers": { ... per-layer results ... }
    }

    Or on error:
    { "error": "message" }

Authentication:
    Supports a Bearer token in the WebSocket query string:
  ws://host/api/v1/verify/stream?token=YOUR_FIREBASE_ID_TOKEN
    Anonymous/public mode is available only when PUBLIC_STREAMING_ENABLED=true
    in a development environment.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.websockets import WebSocketState

from ...services.stream_session import StreamSession
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["real-time-streaming"])


@router.websocket("/verify/stream")
async def verify_stream(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None, description="Optional Firebase ID token"),
    mode: str = Query(default="normal", description="Analysis mode: 'normal' or 'phone'"),
    sample_rate: int = Query(default=16000, description="Audio sample rate: 8000 or 16000"),
):
    """
    Real-time streaming deepfake detection WebSocket endpoint.

    Accepts raw PCM audio frames and returns live verdict JSON on each
    speech-containing window. See module docstring for full protocol.
    """
    # Resolve identity before accepting the stream. Anonymous access is an
    # explicit development-only choice, not an implicit fallback.
    user_id: Optional[str] = None
    if token:
        if settings.MOCK_AUTH_ENABLED and settings.ENVIRONMENT.lower() in {"development", "test"} and token == "mock-token-123":
            user_id = "demo-user-123"
            logger.info("Streaming session opened for mock user %s", user_id)
        else:
            try:
                import firebase_admin.auth as fb_auth  # type: ignore
                decoded = fb_auth.verify_id_token(token)
                user_id = decoded.get("uid")
                logger.info("Streaming session opened for user %s", user_id)
            except Exception as exc:
                logger.debug("Streaming session: token verification failed (%s)", exc)
                await websocket.close(code=1008, reason="Invalid authentication token")
                return

    if not user_id and not settings.PUBLIC_STREAMING_ENABLED:
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket.accept()
    session = StreamSession(sample_rate=sample_rate, mode=mode)

    if not user_id:
        logger.info("Streaming session opened in anonymous mode")

    try:
        while True:
            # Receive the next binary PCM frame
            try:
                data = await websocket.receive_bytes()
            except WebSocketDisconnect:
                break
            except Exception as exc:
                logger.warning("Streaming session receive error: %s", exc)
                break

            if not data:
                continue

            # Process chunk through the session state machine
            try:
                result = await session.process_chunk(data)
            except Exception as exc:
                logger.error("Streaming session process_chunk error: %s", exc, exc_info=True)
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({"error": str(exc)})
                continue

            # Send verdict if analysis ran (None = silence / buffer filling)
            if result is not None:
                if websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_json(result)
                    except Exception as exc:
                        logger.warning("Streaming session send error: %s", exc)
                        break

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("Streaming session unhandled error: %s", exc, exc_info=True)
    finally:
        session.cleanup()
        logger.info(
            "Streaming session closed. Total samples: %d (%.1fs)",
            session.total_samples_received,
            session.total_samples_received / 16000,
        )
        # Gracefully close if still open
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass
