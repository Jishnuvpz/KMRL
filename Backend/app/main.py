"""
Document Management System API
A comprehensive solution for document processing, OCR, summarization, and storage

Features:
- Multi-language OCR (Tesseract + Google Vision API)
- AI-powered summarization (English BART + Malayalam IndicBART)
- AWS S3 raw data storage with compression
- Email processing from zodiacmrv@gmail.com
- Real-time document processing workflows
- JWT authentication and security
"""
import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn

from app.config import settings
from app.db import engine, Base
from app.core.exceptions import setup_exception_handlers, create_success_response
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.routes import (
    auth, 
    documents, 
    optimized_documents,
    admin_email,
    dashboard, 
    settings as settings_routes, 
    alerts, 
    email, 
    cloud, 
    raw_data, 
    summarization_routes,
    session,
    document_sharing,
    websocket
)
from app.routes import ocr_routes, semantic_search

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown procedures"""
    
    # Startup procedures
    logger.info("🚀 Starting Document Management System...")
    
    try:
        # Create database tables
        logger.info("📊 Initializing database...")
        Base.metadata.create_all(bind=engine)
        
        # Import all models to ensure they're registered
        from app.models import user, document, alert, settings as settings_models, admin_email_config
        
        # Create tables for new admin email config models
        from app.models.admin_email_config import AdminEmailConfig, EmailProcessingLog, EmailNotificationTemplate
        
        # Create tables for document sharing models
        from app.models.document_sharing import DocumentShare, DocumentComment, DocumentActivity, CollaborationSession
        
        # Initialize services
        logger.info("🔧 Initializing core services...")
        await initialize_services()
        
        # Initialize session service
        logger.info("🔐 Initializing session service...")
        from app.services.session_service import get_session_service
        await get_session_service()
        
        logger.info("✅ Document Management System started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown procedures
    logger.info("🛑 Shutting down Document Management System...")
    await cleanup_services()
    logger.info("✅ Shutdown complete")

async def initialize_services():
    """Initialize all application services"""
    services = []
    
    try:
        # Initialize OCR services
        logger.info("👁️ Initializing OCR services...")
        from app.services.tesseract_service import tesseract_service
        from app.services.combined_ocr_service import combined_ocr_service
        services.extend(["tesseract_ocr", "combined_ocr"])
        
        # Initialize summarization services
        logger.info("📝 Initializing summarization services...")
        from app.services.combined_summarization_service import combined_summarizer
        services.append("summarization")
        
        # Initialize cloud services
        logger.info("☁️ Initializing cloud services...")
        # AWS S3, Email, etc. are initialized on-demand
        services.append("cloud_services")
        
        logger.info(f"✅ Initialized {len(services)} service groups: {', '.join(services)}")
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        raise

async def cleanup_services():
    """Cleanup services during shutdown"""
    try:
        # Cleanup session service
        logger.info("🧹 Cleaning up session service...")
        from app.services.session_service import session_service
        await session_service.close()
        
        # Cleanup collaboration sessions
        logger.info("🧹 Cleaning up collaboration sessions...")
        from app.core.collaboration_manager import collaboration_manager
        # End all active sessions gracefully
        for document_id in list(collaboration_manager.active_connections.keys()):
            for websocket in list(collaboration_manager.active_connections[document_id]):
                collaboration_manager.disconnect(websocket)
        
        # Add any other necessary cleanup procedures here
        logger.info("🧹 Cleaning up other services...")
        # Services are automatically cleaned up by garbage collection
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Document Management System API",
    description="""
    ## 📄 Comprehensive Document Management Solution
    
    A powerful API for processing documents with advanced OCR and AI-powered summarization.
    
    ### 🚀 Key Features:
    - **Multi-language OCR**: Tesseract (85%+) + Google Vision API (95%+)
    - **AI Summarization**: English (BART) + Malayalam (IndicBART)
    - **Email Integration**: Process attachments from zodiacmrv@gmail.com
    - **Cloud Storage**: AWS S3 with compression and encryption
    - **Real-time Processing**: Instant document analysis and summaries
    - **Secure Authentication**: JWT-based user management
    - **Document Sharing**: Real-time collaboration with permission management
    - **Live Collaboration**: WebSocket-based real-time editing and comments
    
    ### 🌍 Language Support:
    - **English**: 3-4 line clear summaries using BART/Pegasus
    - **Malayalam**: Native script summaries using IndicBART
    - **Auto-detection**: Automatic language routing
    
    ### 📊 Processing Workflows:
    1. **Document Upload** → OCR → Language Detection → Summarization → Storage
    2. **Email Processing** → Attachment Extraction → OCR → Summary → AWS S3
    3. **Batch Processing** → Multiple Documents → Parallel Processing → Reports
    
    ### 🔗 Integration Ready:
    - Frontend: Connect your Frontend React application
    - Storage: AWS S3 raw data storage with metadata
    - Database: MongoDB Atlas (no Supabase)
    - Monitoring: Health checks and performance metrics
    """,
    version="2.0.0",
    contact={
        "name": "Document Management System",
        "email": "zodiacmrv@gmail.com",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS and middleware
from app.core.cors import setup_cors
setup_cors(app)
setup_middleware(app)

# Add session middleware
logger.info("🔐 Setting up session middleware...")
from app.core.session_middleware import SessionMiddleware, SessionSecurityMiddleware
app.add_middleware(SessionSecurityMiddleware, max_requests_per_minute=100)
app.add_middleware(SessionMiddleware, excluded_paths=[
    "/docs", "/redoc", "/openapi.json", "/api/sessions/login", 
    "/health", "/health/quick", "/", "/favicon.ico", "/api/docs", "/api/redoc"
])

# Setup exception handlers
setup_exception_handlers(app)

# Include routers with proper organization
app.include_router(session.router, tags=["🔐 Session Management"])
app.include_router(auth.router, prefix="/api/auth", tags=["🔐 Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["📄 Documents"])
app.include_router(optimized_documents.router, prefix="/api/optimized-documents", tags=["⚡ Optimized Documents (MongoDB Atlas + S3)"])
app.include_router(semantic_search.router, tags=["🔍 FAISS Semantic Search"])
app.include_router(document_sharing.router, prefix="/api", tags=["🤝 Document Sharing & Collaboration"])
app.include_router(admin_email.router, prefix="/api/admin", tags=["👨‍💼 Admin Email Configuration"])
app.include_router(ocr_routes.router, prefix="/api", tags=["👁️ OCR Processing"])
app.include_router(summarization_routes.router, prefix="/api", tags=["📝 Summarization"])
app.include_router(email.router, prefix="/api/email", tags=["📧 Email Processing"])
app.include_router(cloud.router, prefix="/api/cloud", tags=["☁️ Cloud Services"])
app.include_router(raw_data.router, prefix="/api/raw-data", tags=["🗄️ Raw Data Storage"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["📊 Dashboard"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["⚙️ Settings"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["🚨 Alerts"])

# Add WebSocket endpoint for real-time collaboration
@app.websocket("/ws/collaborate/{session_id}")
async def websocket_endpoint(websocket, session_id: str, token: str):
    """WebSocket endpoint for document collaboration"""
    from app.routes.websocket import websocket_collaboration_endpoint
    from app.db import get_db
    
    # Get database session
    db = next(get_db())
    try:
        await websocket_collaboration_endpoint(websocket, session_id, token, db)
    finally:
        db.close()

@app.get("/")
async def root():
    """
    Root endpoint providing system overview
    """
    return create_success_response(
        data={
            "system": "Document Management System API",
            "version": "2.0.0",
            "status": "operational",
            "features": [
                "Multi-language OCR (Tesseract + Google Vision)",
                "AI-powered summarization (English BART + Malayalam IndicBART)",
                "Email processing from zodiacmrv@gmail.com",
                "AWS S3 raw data storage with compression",
                "Real-time document processing workflows",
                "JWT authentication and security",
                "Document sharing and collaboration",
                "Real-time WebSocket collaboration"
            ],
            "endpoints": {
                "documentation": "/api/docs",
                "health_check": "/health",
                "ocr_status": "/api/ocr/health",
                "summarization_demo": "/api/summarization/demo"
            },
            "languages_supported": ["English", "Malayalam"],
            "contact": "zodiacmrv@gmail.com"
        },
        message="Document Management System API v2.0.0 - Ready for processing!"
    )

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint with caching
    """
    from app.core.health import health_checker
    
    try:
        # Get comprehensive health status
        health_status = await health_checker.check_all_services()
        
        # Determine HTTP status code based on overall health
        status_code = 200
        if health_status["overall_status"] == "degraded":
            status_code = 200  # Still operational but with issues
        elif health_status["overall_status"] == "unhealthy":
            status_code = 503  # Service unavailable
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "data": health_status,
                "message": f"Health check completed - Status: {health_status['overall_status']}"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "message": "Health check system failure",
                    "code": "HEALTH_CHECK_ERROR",
                    "details": str(e)
                },
                "data": {
                    "overall_status": "error",
                    "timestamp": time.time(),
                    "basic_status": {
                        "api": "running",
                        "version": "2.0.0"
                    }
                }
            }
        )

@app.get("/health/quick")
async def quick_health_check():
    """
    Quick health check for load balancers and monitoring
    """
    return create_success_response(
        data={
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": time.time(),
            "api": "operational"
        },
        message="Quick health check - API is running"
    )

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Document Management System API",
        version="2.0.0",
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom schema information
    openapi_schema["info"]["x-logo"] = {
        "url": "https://via.placeholder.com/150x50/007ACC/FFFFFF?text=DMS+API"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )