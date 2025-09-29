"""
Minimal FastAPI Application for FAISS Semantic Search Demo - CLEANED VERSION
Only core functionality with fixed imports
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from datetime import datetime

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="FAISS Document Search API - Clean",
    description="Cleaned FAISS semantic search system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "FAISS Document Search API - CLEANED",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "authentication": "demo user available",
            "structure": "cleaned and organized",
            "focus": "core FAISS functionality"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Backend structure cleaned successfully!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)