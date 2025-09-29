"""
Minimal FastAPI Application for FAISS Semantic Search Demo
Only includes essential routes to get the demo working
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import time
from datetime import datetime

# Import only the essential routes
from app.core.routes.auth import router as auth_router
from app.core.routes.documents_minimal import router as documents_router
# Only import working OCR and semantic search if they exist
try:
    from app.core.routes.ocr_routes import router as ocr_router
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from app.core.routes.semantic_search import router as semantic_router
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="FAISS Document Search API",
    description="A semantic search system using FAISS vector database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

# Include essential routers
app.include_router(auth_router, prefix="/api/auth", tags=["🔐 Authentication"])
app.include_router(documents_router, prefix="/api/documents", tags=["📄 Documents"])

# Include optional routers if available
if OCR_AVAILABLE:
    app.include_router(ocr_router, prefix="/api/ocr", tags=["👁️ OCR Processing"])

if SEMANTIC_AVAILABLE:
    app.include_router(semantic_router, prefix="/api/semantic", tags=["🔍 Semantic Search"])

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "FAISS Document Search API",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "authentication": True,
            "document_upload": True,
            "ocr_processing": OCR_AVAILABLE,
            "semantic_search": SEMANTIC_AVAILABLE
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "auth": "enabled",
            "documents": "enabled",
            "ocr": "enabled" if OCR_AVAILABLE else "disabled",
            "semantic_search": "enabled" if SEMANTIC_AVAILABLE else "disabled"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)