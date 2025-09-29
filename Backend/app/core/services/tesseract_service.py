"""
Tesseract OCR Service for Document Management System
Provides local OCR capabilities as fallback to Google Vision API
"""
import os
import pytesseract
from PIL import Image
import io
import base64
from typing import Dict, List, Optional, Union
import logging
from pathlib import Path

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TesseractOCRService:
    """Local OCR service using Tesseract"""
    
    def __init__(self):
        """Initialize Tesseract OCR service"""
        self.tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self._verify_installation()
    
    def _verify_installation(self) -> bool:
        """Verify Tesseract installation"""
        try:
            if not os.path.exists(self.tesseract_path):
                raise FileNotFoundError(f"Tesseract not found at {self.tesseract_path}")
            
            # Test with a simple version check
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR v{version} ready")
            return True
            
        except Exception as e:
            logger.error(f"Tesseract verification failed: {e}")
            return False
    
    def extract_text_from_image(self, image_path: str, config: str = '--psm 6') -> Dict:
        """
        Extract text from image file
        
        Args:
            image_path: Path to image file
            config: Tesseract configuration string
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Open and process image
            image = Image.open(image_path)
            
            # Extract text with configuration
            extracted_text = pytesseract.image_to_string(image, config=config)
            
            # Get additional data (bounding boxes, confidence)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            result = {
                "text": extracted_text.strip(),
                "confidence": avg_confidence,
                "word_count": len(extracted_text.split()),
                "char_count": len(extracted_text),
                "bounding_boxes": self._extract_bounding_boxes(data),
                "method": "tesseract_local",
                "config_used": config
            }
            
            logger.info(f"Extracted {result['word_count']} words with {avg_confidence:.1f}% confidence")
            return result
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                "text": "",
                "confidence": 0,
                "error": str(e),
                "method": "tesseract_local"
            }
    
    def extract_text_from_bytes(self, image_bytes: bytes, config: str = '--psm 6') -> Dict:
        """
        Extract text from image bytes
        
        Args:
            image_bytes: Image data as bytes
            config: Tesseract configuration string
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract text
            extracted_text = pytesseract.image_to_string(image, config=config)
            
            # Get detailed data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            result = {
                "text": extracted_text.strip(),
                "confidence": avg_confidence,
                "word_count": len(extracted_text.split()),
                "char_count": len(extracted_text),
                "bounding_boxes": self._extract_bounding_boxes(data),
                "method": "tesseract_local",
                "config_used": config
            }
            
            logger.info(f"Extracted {result['word_count']} words with {avg_confidence:.1f}% confidence")
            return result
            
        except Exception as e:
            logger.error(f"Text extraction from bytes failed: {e}")
            return {
                "text": "",
                "confidence": 0,
                "error": str(e),
                "method": "tesseract_local"
            }
    
    def extract_text_from_base64(self, base64_image: str, config: str = '--psm 6') -> Dict:
        """
        Extract text from base64 encoded image
        
        Args:
            base64_image: Base64 encoded image string
            config: Tesseract configuration string
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_image)
            return self.extract_text_from_bytes(image_bytes, config)
            
        except Exception as e:
            logger.error(f"Base64 text extraction failed: {e}")
            return {
                "text": "",
                "confidence": 0,
                "error": str(e),
                "method": "tesseract_local"
            }
    
    def _extract_bounding_boxes(self, data: Dict) -> List[Dict]:
        """Extract bounding box information from Tesseract data"""
        boxes = []
        n_boxes = len(data['level'])
        
        for i in range(n_boxes):
            if int(data['conf'][i]) > 0:  # Only include confident detections
                box = {
                    "text": data['text'][i],
                    "confidence": int(data['conf'][i]),
                    "x": int(data['left'][i]),
                    "y": int(data['top'][i]),
                    "width": int(data['width'][i]),
                    "height": int(data['height'][i]),
                    "level": int(data['level'][i])
                }
                boxes.append(box)
        
        return boxes
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        try:
            languages = pytesseract.get_languages(config='')
            return languages
        except Exception as e:
            logger.error(f"Could not get supported languages: {e}")
            return ['eng']  # Default to English
    
    def process_document_pages(self, image_paths: List[str], config: str = '--psm 6') -> Dict:
        """
        Process multiple pages of a document
        
        Args:
            image_paths: List of paths to image files
            config: Tesseract configuration string
            
        Returns:
            Dictionary with combined results
        """
        all_text = []
        all_confidences = []
        page_results = []
        
        for i, image_path in enumerate(image_paths):
            logger.info(f"Processing page {i+1}/{len(image_paths)}: {image_path}")
            
            page_result = self.extract_text_from_image(image_path, config)
            page_results.append({
                "page_number": i + 1,
                "result": page_result
            })
            
            if page_result.get("text"):
                all_text.append(page_result["text"])
                all_confidences.append(page_result.get("confidence", 0))
        
        # Combine results
        combined_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        return {
            "combined_text": combined_text,
            "average_confidence": avg_confidence,
            "total_pages": len(image_paths),
            "total_words": len(combined_text.split()),
            "page_results": page_results,
            "method": "tesseract_local_multipage"
        }
    
    def health_check(self) -> Dict:
        """Check if Tesseract OCR service is working"""
        try:
            # Create a simple test image with text
            from PIL import Image, ImageDraw, ImageFont
            
            # Create test image
            img = Image.new('RGB', (200, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                # Try to use a system font
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            draw.text((10, 30), "TEST OCR", fill='black', font=font)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Test OCR
            result = self.extract_text_from_bytes(img_bytes.getvalue())
            
            is_working = "TEST" in result.get("text", "").upper()
            
            return {
                "status": "working" if is_working else "error",
                "tesseract_version": str(pytesseract.get_tesseract_version()),
                "tesseract_path": self.tesseract_path,
                "supported_languages": len(self.get_supported_languages()),
                "test_result": result,
                "working": is_working
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "working": False
            }

# Create global instance
tesseract_service = TesseractOCRService()

def get_tesseract_service() -> TesseractOCRService:
    """Get the global Tesseract OCR service instance"""
    return tesseract_service