from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize MongoDB
from config.mongodb_init import init_db, close_db

# Import routes
from routes import auth, users, calls, webhooks, admin, payments
from services.websocket_manager import manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="CallBot Research API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    logger.info("MongoDB initialized successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_db()
    logger.info("MongoDB connection closed")

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(calls.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(payments.router, prefix="/api")

# Root endpoint
@app.get("/api/")
async def root():
    return {"message": "CallBot Research API", "status": "running"}

# WebSocket endpoint for real-time call events
@app.websocket("/ws/calls/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            logger.info(f"Received from {user_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"Client {user_id} disconnected")

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "database": "mongodb"}

# Deepgram audio serving endpoint
@app.api_route("/api/audio/deepgram/{audio_id}.mp3", methods=["GET", "HEAD"])
async def serve_deepgram_audio(audio_id: str, request: Request):
    """Serve Deepgram generated audio files - Support both GET and HEAD requests"""
    from fastapi.responses import FileResponse
    from services.deepgram_service import DeepgramService
    
    try:
        deepgram = DeepgramService()
        filename = os.path.join(deepgram.audio_dir, f"{audio_id}.mp3")
        
        # Check if file exists
        if not os.path.exists(filename):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Get file size for Content-Length header
        file_size = os.path.getsize(filename)
        
        # For HEAD requests, return headers only (SignalWire validation)
        if request.method == "HEAD":
            from fastapi import Response as FastAPIResponse
            return FastAPIResponse(
                status_code=200,
                headers={
                    "Content-Type": "audio/mpeg",
                    "Content-Length": str(file_size),
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        
        # For GET requests, return audio file
        from fastapi.responses import StreamingResponse
        import io
        
        audio_data = deepgram.get_audio_file(audio_id)
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename={audio_id}.mp3",
                "Content-Length": str(len(audio_data)),
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except FileNotFoundError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Error serving audio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)