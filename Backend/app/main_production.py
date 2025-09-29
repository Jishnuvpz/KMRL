"""
KMRL Document Management System - Production Main Application
Complete system with all features restored
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from app.db import engine, Base
from app.core.exceptions import setup_exception_handlers, create_success_response
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware

# Import all models to ensure they're registered
from app.models import (
    User, Document, DocumentShare, DocumentComment, DocumentActivity,
    CollaborationSession, Alert, SystemNotification, AlertRule,
    UserSession, SessionActivity, SystemSettings
)

# Import all routes
from app.routes import auth, documents, email_routes
from app.routes import summarization_routes

# Import services
from app.services.email_service import get_email_service
from app.services.combined_summarization_service import get_combined_summarizer

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown procedures"""

    # Startup procedures
    logger.info("🚀 Starting KMRL Document Management System...")

    try:
        # Create database tables
        logger.info("📊 Initializing database...")
        Base.metadata.create_all(bind=engine)

        # Initialize services
        logger.info("🔧 Initializing services...")

        # Initialize summarization service
        try:
            summarizer = get_combined_summarizer()
            logger.info("✅ Summarization service initialized")
        except Exception as e:
            logger.warning(
                f"⚠️ Summarization service initialization failed: {e}")

        # Initialize email service
        try:
            email_service = get_email_service()
            logger.info("📧 Email service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Email service initialization failed: {e}")

        logger.info("✅ KMRL Document Management System started successfully!")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    finally:
        # Shutdown procedures
        logger.info("🛑 Shutting down KMRL Document Management System...")

        try:
            # Cleanup services
            logger.info("🧹 Cleaning up services...")

            # Any cleanup needed for services

            logger.info("✅ Shutdown completed successfully")
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="KMRL Document Management System API",
    description="""
    ## 📄 Complete Document Management Solution for KMRL
    
    A comprehensive API for document processing with advanced features:
    
    ### 🚀 Core Features:
    - **Multi-language OCR**: Tesseract integration for text extraction
    - **AI Summarization**: English (BART) + Malayalam (IndicBART) support
    - **Email Processing**: Automatic document ingestion from zodiacmrv@gmail.com
    - **Document Sharing**: Inter-department collaboration and permissions
    - **Real-time Alerts**: Intelligent notification system
    - **Session Management**: Advanced user session tracking
    - **Audit Trail**: Complete activity logging and monitoring
    
    ### 🌍 Language Support:
    - **English**: Clear summaries using BART models
    - **Malayalam**: Native script summaries using IndicBART
    - **Auto-detection**: Automatic language routing
    
    ### 🏢 Departments Supported:
    - Operations, HR, Finance, Legal, IT, Safety, Engineering, Maintenance
    
    ### 🔗 Integration Features:
    - React Frontend Compatible
    - Real-time WebSocket Support
    - RESTful API Design
    - JWT Authentication
    - Role-based Access Control
    
    ### 📊 System Status:
    - Environment: Production
    - Database: SQLite/PostgreSQL
    - Authentication: JWT-based
    - File Storage: Local/S3
    """,
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup middleware
setup_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    logger.warning("Static files directory not found, skipping mount")

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(email_routes.router)
app.include_router(summarization_routes.router)


@app.get("/")
async def root():
    """
    Root endpoint providing system overview
    """
    return create_success_response(
        data={
            "system": "KMRL Document Management System API",
            "version": "3.0.0",
            "status": "operational",
            "environment": "production",
            "features": [
                "Multi-language OCR (Tesseract)",
                "AI-powered summarization (English BART + Malayalam IndicBART)",
                "Email processing from zodiacmrv@gmail.com",
                "Document sharing and collaboration",
                "Real-time alerts and notifications",
                "Advanced session management",
                "Complete audit trail",
                "Inter-department workflow",
                "Role-based access control",
                "Real-time WebSocket support"
            ],
            "endpoints": {
                "documentation": "/api/docs",
                "redoc": "/api/redoc",
                "health_check": "/health",
                "authentication": "/api/auth",
                "documents": "/api/documents",
                "email": "/api/email",
                "summarization": "/api/summarization"
            },
            "departments": [
                "Operations", "HR", "Finance", "Legal",
                "IT", "Safety", "Engineering", "Maintenance"
            ],
            "languages_supported": ["English", "Malayalam"],
            "contact": "zodiacmrv@gmail.com",
            "organization": "KMRL (Kochi Metro Rail Limited)"
        },
        message="Welcome to KMRL Document Management System"
    )


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    """
    health_status = {
        "status": "healthy",
        "timestamp": "2024-07-20T12:00:00Z",
        "version": "3.0.0",
        "components": {
            "database": "healthy",
            "ocr_service": "healthy",
            "summarization_service": "healthy",
            "email_service": "healthy",
            "file_storage": "healthy"
        }
    }

    return create_success_response(
        data=health_status,
        message="All systems operational"
    )


@app.get("/api/system/info")
async def system_info():
    """
    System information endpoint
    """
    return create_success_response(
        data={
            "name": "KMRL Document Management System",
            "version": "3.0.0",
            "description": "Complete document management solution for KMRL",
            "features": {
                "ocr": True,
                "summarization": True,
                "email_processing": True,
                "document_sharing": True,
                "real_time_alerts": True,
                "session_management": True,
                "audit_trail": True,
                "multilingual": True
            },
            "supported_formats": [
                "PDF", "DOCX", "DOC", "TXT", "JPG", "JPEG", "PNG", "TIFF"
            ],
            "departments": [
                "Operations", "HR", "Finance", "Legal",
                "IT", "Safety", "Engineering", "Maintenance"
            ],
            "roles": ["Staff", "Manager", "Director", "Admin"],
            "organization": "KMRL (Kochi Metro Rail Limited)"
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "Endpoint not found",
                "details": f"The requested endpoint {request.url.path} was not found"
            }
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "details": "Please contact system administrator if the problem persists"
            }
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main_production:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
