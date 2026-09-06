from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
from backend.services.risk_engine import analyze_call

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit for hackathon constraints

@router.post("/analyze")
async def analyze_audio_endpoint(file: UploadFile = File(...)):
    """
    Accepts an audio file and returns the risk analysis.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
        
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")
        
    # Read the file
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Error reading upload: {e}")
        raise HTTPException(status_code=400, detail="Could not read uploaded file")
        
    # Validate size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
        
    # Analyze
    try:
        result = analyze_call(file_bytes)
        return result
    except ValueError as ve:
        # e.g., Invalid audio format
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Internal error during analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")
