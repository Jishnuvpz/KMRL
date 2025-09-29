"""
Minimal document management routes - just the essentials
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
import logging
from datetime import datetime

from app.services.optimized_document_service import get_optimized_document_service
from app.services.semantic_integration import on_document_uploaded
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: Optional[str] = Form("uncategorized"),
    tags: Optional[str] = Form(None),
    enable_semantic_search: bool = Form(True),
    current_user = Depends(get_current_user)
):
    """
    Upload document with optimized storage
    """
    try:
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # Use optimized service
        result = get_optimized_document_service().upload_document(
            file=file,
            title=title,
            category=category,
            tags=tag_list,
            user_id=str(current_user["id"])
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Trigger semantic search integration if enabled
        if enable_semantic_search:
            await on_document_uploaded(
                document_id=result["document_id"],
                user_id=str(current_user["id"])
            )
        
        return {
            "message": "Document uploaded successfully",
            "document_id": result["document_id"],
            "s3_url": result.get("s3_url"),
            "metadata": result.get("metadata", {}),
            "semantic_search_enabled": enable_semantic_search
        }
        
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/status")
async def get_documents_status():
    """Get document service status"""
    return {
        "status": "active",
        "service": "document_management",
        "timestamp": datetime.utcnow().isoformat()
    }