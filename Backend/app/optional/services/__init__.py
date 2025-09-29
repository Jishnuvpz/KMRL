"""
Services package initialization
Document Management System Services

This package contains all the core business logic services for:
- Authentication and authorization
- Document processing and storage
- OCR (Optical Character Recognition) 
- AI-powered summarization
- Cloud storage and email integration
"""

# Core authentication and authorization
from .auth_service import AuthService

# Email processing services
from .email_service import EmailService

# OCR and text extraction services
from .tesseract_service import tesseract_service
# from .google_vision_service import google_vision_service  # REMOVED
from .combined_ocr_service import combined_ocr_service

# AI summarization services
from .english_summarization_service import get_english_summarizer
from .malayalam_summarization_service import get_malayalam_summarizer
from .combined_summarization_service import get_combined_summarizer

# Cloud and database services
from .s3_service import s3_service
from .mongodb_service import get_mongodb_service
from .raw_data_service import get_raw_data_service

## Supabase service removed

__all__ = [
    # Authentication
    "AuthService",
    
    # Email processing
    "EmailService", 
    
    # OCR services
    "tesseract_service",
    # "google_vision_service",  # REMOVED
    "combined_ocr_service",
    
    # Summarization services
    "get_english_summarizer",
    "get_malayalam_summarizer", 
    "get_combined_summarizer",
    
    # Cloud and storage services
    "get_s3_service", 
    # "supabase_service", 
    "get_mongodb_service",
    "get_raw_data_service"
]