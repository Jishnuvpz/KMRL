"""
Document management routes with Optimized MongoDB + S3 Architecture
MongoDB Atlas: Lightweight metadata only (~1-5KB per document)
AWS S3: Raw file storage with unlimited capacity
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict
import uuid
import logging
from datetime import datetime

from app.services.optimized_document_service import get_optimized_document_service
from app.services.semantic_integration import on_document_uploaded, on_document_deleted
from app.services.mongodb_service import get_mongodb_service
from app.utils.auth import get_current_user
from app.db import get_db
from sqlalchemy.orm import Session

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
    Upload document with optimized storage:
    - File → AWS S3 (raw storage)
    - Lightweight metadata → MongoDB Atlas (~1-5KB per document)
    - Automatic semantic search embedding generation (optional)
    """
    try:
        # Parse tags from comma-separated string
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Use optimized document service
        result = get_optimized_document_service().upload_document(
            file_obj=file.file,
            filename=file.filename or "untitled",
            title=title,
            user_id=str(current_user["id"]),
            category=category or "uncategorized",
            tags=tag_list,
            content_type=file.content_type or "application/octet-stream"
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))
        
        # Trigger semantic search processing in background if enabled
        if enable_semantic_search:
            try:
                await on_document_uploaded(
                    document_id=result["document_id"],
                    user_id=str(current_user["id"]),
                    background=True  # Process in background
                )
            except Exception as e:
                # Don't fail upload if semantic processing fails
                logger.warning(f"Semantic search processing failed for document {result['document_id']}: {e}")
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "document": {
                "id": result["document_id"],
                "title": title,
                "category": category or "uncategorized",
                "tags": tag_list,
                "file_size": result["metadata"]["file_size"],
                "storage_info": result["storage"]
            },
            "file_access": {
                "s3_key": result["s3_key"],
                "download_url": result["file_url"]
            },
            "semantic_search": {
                "enabled": enable_semantic_search,
                "status": "processing" if enable_semantic_search else "disabled",
                "message": "Embeddings are being generated in background" if enable_semantic_search else "Semantic search not enabled for this document"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/")
async def get_documents(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Get user's documents from MongoDB
    """
    try:
        # Get documents from MongoDB
        # Temporarily commented out to get server started
        # documents = get_mongodb_service().get_user_documents(
            user_id=str(current_user["id"]),
            limit=limit,
            skip=skip
        )
        
        # Filter by category if specified
        if category:
            documents = [doc for doc in documents if doc.get('category') == category]
        
        # Log analytics event
        analytics_event = {
            "user_id": str(current_user["id"]),
            "event_type": "documents_list",
            "filter_category": category,
            "result_count": len(documents)
        }
        mongodb_service.store_analytics_event(analytics_event)
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents),
            "filters": {
                "category": category,
                "skip": skip,
                "limit": limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get specific document by ID from MongoDB
    """
    try:
        # Get document from MongoDB
        document = mongodb_service.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user owns the document
        if document.get('user_id') != str(current_user["id"]):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Log analytics event
        analytics_event = {
            "user_id": str(current_user["id"]),
            "event_type": "document_view",
            "document_id": document_id,
            "document_category": document.get('category'),
            "document_title": document.get('title')
        }
        mongodb_service.store_analytics_event(analytics_event)
        
        return {
            "success": True,
            "document": document
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

@router.post("/search")
async def search_documents(
    query: str,
    category: Optional[str] = None,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """
    Search documents using MongoDB full-text search
    """
    try:
        # Prepare search filters
        filters = {}
        if category:
            filters['category'] = category
        
        # Search documents
        results = mongodb_service.search_documents(
            user_id=str(current_user["id"]),
            query=query,
            filters=filters,
            limit=limit
        )
        
        # Log analytics event
        analytics_event = {
            "user_id": str(current_user["id"]),
            "event_type": "document_search",
            "search_query": query,
            "search_category": category,
            "result_count": len(results)
        }
        mongodb_service.store_analytics_event(analytics_event)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "filters": filters
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    try:
        document_service = DocumentService(db)
        documents = document_service.get_user_documents(
            user_id=current_user["id"],
            skip=skip,
            limit=limit,
            category=category
        )
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}")
async def get_document(
    document_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific document
    """
    try:
        document_service = DocumentService(db)
        document = document_service.get_document(
            document_id=document_id,
            user_id=current_user["id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"document": document}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{document_id}")
async def update_document(
    document_id: int,
    update_data: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update document metadata
    """
    try:
        document_service = DocumentService(db)
        document = document_service.update_document(
            document_id=document_id,
            user_id=current_user["id"],
            update_data=update_data
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document updated successfully", "document": document}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete document
    """
    try:
        document_service = DocumentService(db)
        success = document_service.delete_document(
            document_id=document_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_documents(
    search_data: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search documents by content or metadata
    """
    try:
        document_service = DocumentService(db)
        results = document_service.search_documents(
            user_id=current_user["id"],
            query=search_data.get("query"),
            filters=search_data.get("filters", {})
        )
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Google Vision routes have been removed

# Semantic Search Integration Routes
@router.get("/{document_id}/semantic-status")
async def get_document_semantic_status(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get semantic search processing status for a document
    """
    try:
        from app.services.semantic_integration import semantic_search_integration
        
        status = await semantic_search_integration.get_processing_status(
            document_id=document_id,
            user_id=str(current_user["id"])
        )
        
        return {
            "success": True,
            "document_id": document_id,
            "semantic_search": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get semantic status: {str(e)}")

@router.post("/{document_id}/semantic-reprocess")
async def reprocess_document_semantics(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """
    Reprocess document for semantic search (force regenerate embeddings)
    """
    try:
        from app.services.semantic_integration import semantic_search_integration
        
        result = await semantic_search_integration.reprocess_document(
            document_id=document_id,
            user_id=str(current_user["id"])
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Document semantic processing initiated",
                "document_id": document_id,
                "processing_info": result
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=result.get("error", "Failed to reprocess document")
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reprocess document: {str(e)}")