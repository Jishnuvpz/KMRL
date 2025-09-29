"""
OCR routes for the Document Management System
Unified OCR endpoints combining Tesseract and Google Vision API
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from io import BytesIO

from app.core.exceptions import create_success_response, OCRException

logger = logging.getLogger(__name__)

# Pydantic models
class OCRRequest(BaseModel):
    image_base64: str
    ocr_method: Optional[str] = "auto"  # auto, tesseract, google_vision
    config: Optional[str] = "--psm 6"

class OCRResponse(BaseModel):
    text: str
    confidence: float
    method_used: str
    processing_time: float
    word_count: int

# Create router
router = APIRouter(prefix="/ocr", tags=["OCR Processing"])

@router.post("/extract-text")
async def extract_text_from_image(request: OCRRequest):
    """
    Extract text from base64 encoded image
    
    - **image_base64**: Base64 encoded image data
    - **ocr_method**: OCR method to use (auto, tesseract, google_vision)
    - **config**: Tesseract configuration string
    """
    try:
        from app.services.combined_ocr_service import get_combined_ocr_service
        
        ocr_service = get_combined_ocr_service()
        
        # Extract text based on method
        if request.ocr_method == "tesseract":
            from app.services.tesseract_service import get_tesseract_service
            tesseract = get_tesseract_service()
            result = tesseract.extract_text_from_base64(request.image_base64, request.config)
        elif request.ocr_method == "google_vision":
            try:
                from app.services.google_vision_service import GoogleVisionService
                vision = GoogleVisionService()
                result = vision.extract_text_from_base64(request.image_base64)
            except Exception as e:
                # Fallback to Tesseract if Google Vision fails
                from app.services.tesseract_service import get_tesseract_service
                tesseract = get_tesseract_service()
                result = tesseract.extract_text_from_base64(request.image_base64, request.config)
                result["fallback_used"] = True
        else:  # auto
            result = ocr_service.extract_text_from_base64(request.image_base64)
        
        if result.get("error"):
            raise OCRException(result["error"])
        
        return create_success_response(
            data={
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0),
                "method_used": result.get("method", "unknown"),
                "processing_time": result.get("processing_time", 0),
                "word_count": result.get("word_count", 0),
                "character_count": result.get("char_count", 0),
                "fallback_used": result.get("fallback_used", False)
            },
            message="Text extracted successfully"
        )
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@router.post("/extract-from-upload")
async def extract_text_from_upload(
    file: UploadFile = File(...),
    ocr_method: str = Form("auto"),
    config: str = Form("--psm 6")
):
    """
    Extract text from uploaded image file
    
    - **file**: Image file (jpg, png, bmp, tiff)
    - **ocr_method**: OCR method to use
    - **config**: Tesseract configuration
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        file_content = await file.read()
        
        from app.services.combined_ocr_service import get_combined_ocr_service
        ocr_service = get_combined_ocr_service()
        
        # Extract text
        result = ocr_service.extract_text_from_bytes(file_content)
        
        if result.get("error"):
            raise OCRException(result["error"])
        
        return create_success_response(
            data={
                "filename": file.filename,
                "file_size": len(file_content),
                "content_type": file.content_type,
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0),
                "method_used": result.get("method", "unknown"),
                "processing_time": result.get("processing_time", 0),
                "word_count": result.get("word_count", 0),
                "fallback_used": result.get("fallback_used", False)
            },
            message="Text extracted from uploaded file successfully"
        )
        
    except Exception as e:
        logger.error(f"File OCR extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"File OCR processing failed: {str(e)}")

@router.get("/status")
async def get_ocr_status():
    """
    Get status of OCR services
    """
    try:
        from app.services.combined_ocr_service import get_combined_ocr_service
        
        ocr_service = get_combined_ocr_service()
        status = ocr_service.get_ocr_status()
        
        return create_success_response(
            data=status,
            message="OCR status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"OCR status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR status check failed: {str(e)}")

@router.get("/health")
async def ocr_health_check():
    """
    Health check for OCR services
    """
    try:
        from app.services.combined_ocr_service import get_combined_ocr_service
        
        ocr_service = get_combined_ocr_service()
        health = ocr_service.health_check()
        
        return create_success_response(
            data={
                "overall_status": health.get("overall_status", "unknown"),
                "working_methods": health.get("working_methods", 0),
                "primary_ocr": health.get("primary_ocr", "unknown"),
                "fallback_ready": health.get("fallback_ready", False),
                "recommendations": health.get("recommendations", []),
                "services": {
                    "tesseract": {
                        "available": True,
                        "accuracy": "85%+",
                        "local": True
                    },
                    "google_vision": {
                        "available": health.get("details", {}).get("google_vision", {}).get("available", False),
                        "accuracy": "95%+",
                        "cloud": True,
                        "billing_required": True
                    }
                }
            },
            message="OCR health check completed"
        )
        
    except Exception as e:
        logger.error(f"OCR health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR health check failed: {str(e)}")

@router.post("/batch-extract")
async def batch_extract_text(files: List[UploadFile] = File(...)):
    """
    Extract text from multiple image files in batch
    
    - **files**: List of image files to process
    """
    try:
        if len(files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch")
        
        from app.services.combined_ocr_service import get_combined_ocr_service
        ocr_service = get_combined_ocr_service()
        
        results = []
        total_processing_time = 0
        
        for i, file in enumerate(files):
            try:
                # Validate file type
                if not file.content_type.startswith('image/'):
                    results.append({
                        "index": i,
                        "filename": file.filename,
                        "success": False,
                        "error": "File must be an image"
                    })
                    continue
                
                # Read and process file
                file_content = await file.read()
                result = ocr_service.extract_text_from_bytes(file_content)
                
                total_processing_time += result.get("processing_time", 0)
                
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "success": True,
                    "text": result.get("text", ""),
                    "confidence": result.get("confidence", 0),
                    "method_used": result.get("method", "unknown"),
                    "processing_time": result.get("processing_time", 0),
                    "word_count": result.get("word_count", 0)
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        successful_extractions = sum(1 for r in results if r.get("success"))
        
        return create_success_response(
            data={
                "results": results,
                "summary": {
                    "total_files": len(files),
                    "successful_extractions": successful_extractions,
                    "failed_extractions": len(files) - successful_extractions,
                    "total_processing_time": total_processing_time,
                    "average_processing_time": total_processing_time / len(files) if files else 0
                }
            },
            message=f"Batch OCR completed: {successful_extractions}/{len(files)} files processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Batch OCR failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch OCR processing failed: {str(e)}")