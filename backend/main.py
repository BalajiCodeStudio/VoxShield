import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Import routers
from backend.routes.health import router as health_router
from backend.routes.analyze import router as analyze_router

app = FastAPI(
    title="VoxShield API",
    description="Backend for VoxShield - Real-time Voice Scam & Deepfake Detection",
    version="1.0.0"
)

# Enable CORS for frontend/mobile apps to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router, tags=["Health"])
app.include_router(analyze_router, tags=["Analysis"])

@app.get("/")
async def root():
    return {"message": "VoxShield API is running. Use /analyze to process audio."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
