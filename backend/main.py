"""
Whicoustic Main Server Entrypoint.
Exposes the authoritative FastAPI app from app.main.
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
