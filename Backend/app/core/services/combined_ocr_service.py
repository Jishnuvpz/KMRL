"""
Combined OCR Service - Google Vision + Tesseract Fallback
"""
import os
import logging
from typing import Dict, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CombinedOCRService:
    """OCR service that tries Google Vision first, falls back to Tesseract"""
    
    def __init__(self):
        """Initialize combined OCR service"""
        self.google_vision_available = False  # Removed Google Vision
        self.tesseract_available = False
        self.google_vision = None  # Not used
        
        # Initialize Tesseract only
        try:
            from .tesseract_service import tesseract_service
            # Test Tesseract quickly
            health = tesseract_service.health_check()
            if health.get('working', False):
                self.tesseract = tesseract_service
                self.tesseract_available = True
                logger.info("Tesseract OCR initialized and working")
            else:
                logger.warning("Tesseract OCR not working properly")
                self.tesseract = None
        except Exception as e:
            logger.warning(f"Tesseract OCR not available: {e}")
            self.tesseract = None
    
    def extract_text_from_image(self, image_path: str, prefer_accuracy: bool = True) -> Dict:
        """
        Extract text from image using best available OCR method
        
        Args:
            image_path: Path to image file
            prefer_accuracy: If True, tries Google Vision first for higher accuracy
            
        Returns:
            Dictionary with extracted text and metadata
        """
        result = {
            "text": "",
            "confidence": 0,
            "method": "none",
            "error": None,
            "fallback_used": False
        }
        
        # Use Tesseract OCR only
        if self.tesseract_available:
            try:
                logger.info("Using Tesseract OCR...")
                tesseract_result = self.tesseract.extract_text_from_image(image_path)
                
                if tesseract_result.get("text"):
                    result.update(tesseract_result)
                    result["method"] = "tesseract_local"
                    logger.info("Tesseract OCR successful")
                    return result
                else:
                    logger.error("Tesseract OCR failed")
                    
            except Exception as e:
                logger.error(f"Tesseract error: {e}")
                result["error"] = str(e)
        
        # No OCR method worked
        result["error"] = "No working OCR method available"
        logger.error("All OCR methods failed")
        return result
    
    def extract_text_from_bytes(self, image_bytes: bytes, prefer_accuracy: bool = True) -> Dict:
        """
        Extract text from image bytes using best available OCR method
        
        Args:
            image_bytes: Image data as bytes
            prefer_accuracy: If True, tries Google Vision first for higher accuracy
            
        Returns:
            Dictionary with extracted text and metadata
        """
        result = {
            "text": "",
            "confidence": 0,
            "method": "none",
            "error": None,
            "fallback_used": False
        }
        
        # Use Tesseract OCR only
        if self.tesseract_available:
            try:
                logger.info("Using Tesseract OCR on bytes...")
                tesseract_result = self.tesseract.extract_text_from_bytes(image_bytes)
                
                if tesseract_result.get("text"):
                    result.update(tesseract_result)
                    result["method"] = "tesseract_local"
                    logger.info("Tesseract OCR successful")
                    return result
                else:
                    logger.error("Tesseract OCR failed")
                    
            except Exception as e:
                logger.error(f"Tesseract error: {e}")
                result["error"] = str(e)
        
        # No OCR method worked
        result["error"] = "No working OCR method available"
        logger.error("All OCR methods failed")
        return result
    
    def get_ocr_status(self) -> Dict:
        """Get status of all OCR methods"""
        return {
            "tesseract": {
                "available": self.tesseract_available,
                "status": "ready" if self.tesseract_available else "not_working",
                "accuracy": "85%+" if self.tesseract_available else "N/A"
            },
            "fallback_available": self.tesseract_available,
            "best_method": "tesseract" if self.tesseract_available else "none"
        }
    
    def health_check(self) -> Dict:
        """Comprehensive health check for OCR services"""
        status = self.get_ocr_status()
        
        # Overall health
        working_methods = 1 if self.tesseract_available else 0
        
        return {
            "overall_status": "healthy" if working_methods > 0 else "unhealthy",
            "working_methods": working_methods,
            "primary_ocr": status["best_method"],
            "fallback_ready": self.tesseract_available,
            "details": status,
            "recommendations": self._get_recommendations()
        }
    
    def _get_recommendations(self) -> list:
        """Get recommendations for improving OCR setup"""
        recommendations = []
        
        if not self.google_vision_available:
            recommendations.append("Enable Google Cloud billing for 95%+ OCR accuracy")
        
        if not self.tesseract_available:
            recommendations.append("Install Tesseract OCR for local fallback processing")
        
        if not self.google_vision_available and not self.tesseract_available:
            recommendations.append("CRITICAL: No OCR methods available - install at least one")
        
        if self.tesseract_available and not self.google_vision_available:
            recommendations.append("Consider enabling Google Vision for better accuracy")
        
        return recommendations

# Create global instance
combined_ocr_service = CombinedOCRService()

def get_combined_ocr_service() -> CombinedOCRService:
    """Get the global combined OCR service instance"""
    return combined_ocr_service