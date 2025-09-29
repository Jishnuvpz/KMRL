"""
Services Package for KMRL Document Intelligence Platform

This package contains all the AI and processing services:
- Language Detection Service
- English Summarization Service (BART, Pegasus)
- Malayalam Summarization Service (IndicBART, mT5)
- Combined Summarization Service (Orchestrator)
- OCR Services
- Other utility services
"""

import logging
logger = logging.getLogger(__name__)

# Service availability flags
SERVICES_AVAILABLE = {
    'language_detection': False,
    'english_summarization': False,
    'malayalam_summarization': False,
    'combined_summarization': False,
    'ocr_services': False
}

def initialize_all_services():
    """Initialize all available services"""
    logger.info("🔧 Initializing KMRL AI Services...")
    
    # Initialize Language Detection
    try:
        from .language_detection_service import get_language_detector
        lang_detector = get_language_detector()
        SERVICES_AVAILABLE['language_detection'] = True
        logger.info("✅ Language Detection Service initialized")
    except Exception as e:
        logger.warning(f"⚠️ Language Detection Service failed: {e}")
    
    # Initialize English Summarization
    try:
        from .english_summarization_service import get_english_summarizer
        eng_summarizer = get_english_summarizer()
        SERVICES_AVAILABLE['english_summarization'] = True
        logger.info("✅ English Summarization Service initialized")
    except Exception as e:
        logger.warning(f"⚠️ English Summarization Service failed: {e}")
    
    # Initialize Malayalam Summarization
    try:
        from .malayalam_summarization_service import get_malayalam_summarizer
        mal_summarizer = get_malayalam_summarizer()
        SERVICES_AVAILABLE['malayalam_summarization'] = True
        logger.info("✅ Malayalam Summarization Service initialized")
    except Exception as e:
        logger.warning(f"⚠️ Malayalam Summarization Service failed: {e}")
    
    # Initialize Combined Summarization (requires the above two)
    try:
        from .combined_summarization_service import get_combined_summarizer
        combined_summarizer = get_combined_summarizer()
        SERVICES_AVAILABLE['combined_summarization'] = True
        logger.info("✅ Combined Summarization Service initialized")
    except Exception as e:
        logger.warning(f"⚠️ Combined Summarization Service failed: {e}")
    
    # Initialize OCR Services (if available)
    try:
        from ..core.services.tesseract_service import tesseract_service
        SERVICES_AVAILABLE['ocr_services'] = True
        logger.info("✅ OCR Services initialized")
    except Exception as e:
        logger.warning(f"⚠️ OCR Services failed: {e}")
    
    logger.info(f"🎯 Services Status: {SERVICES_AVAILABLE}")
    return SERVICES_AVAILABLE

def get_services_status():
    """Get current status of all services"""
    return SERVICES_AVAILABLE.copy()

# Convenience imports for easy access
try:
    from .language_detection_service import detect_document_language, get_language_detector
    from .english_summarization_service import summarize_english_text, get_english_summarizer
    from .malayalam_summarization_service import summarize_malayalam_text, get_malayalam_summarizer
    from .combined_summarization_service import auto_summarize_document, get_combined_summarizer
    
    __all__ = [
        'initialize_all_services',
        'get_services_status',
        'detect_document_language',
        'get_language_detector',
        'summarize_english_text',
        'get_english_summarizer',
        'summarize_malayalam_text', 
        'get_malayalam_summarizer',
        'auto_summarize_document',
        'get_combined_summarizer',
        'SERVICES_AVAILABLE'
    ]
    
except ImportError as e:
    logger.warning(f"Some summarization services not available: {e}")
    __all__ = ['initialize_all_services', 'get_services_status', 'SERVICES_AVAILABLE']
