""""""

import Dict
import Optional
import loggingfrom typing import List
from app.services.combined_summarization_service import get_combined_summarizer
from app.services.combined_ocr_service import get_ocr_servicefrom sqlalchemy.orm import Session
from app.utils.auth import get_current_userfrom app.db import get_db
from app.models.document_sharing import DocumentShare, DocumentComment, DocumentActivityfrom app.utils.auth import get_current_user
from app.models.user import Userfrom app.services.mongodb_service import get_mongodb_service
from app.models.document import Documentfrom app.services.semantic_integration import on_document_uploaded, on_document_deleted
from app.db import get_dbfrom app.services.optimized_document_service import get_optimized_document_service
from datetime import datetimefrom datetime import datetime
import uuidimport logging
import osimport uuid
from typing import List, Optionalfrom fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
Document management routes for KMRL Document Management SystemDocument management routes with Optimized MongoDB + S3 Architecture

"""MongoDB Atlas: Lightweight metadata only (~1-5KB per document)

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, QueryAWS S3: Raw file storage with unlimited capacity

from sqlalchemy.orm import Session"""


logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)router = APIRouter()


router = APIRouter(prefix="/api/documents",
                   tags=["Document Management"])@router.post("/upload")


async def upload_document(

@ router.post("/upload")    file: UploadFile = File(...),

async def upload_document(title: str=Form(...),

    file: UploadFile=File(...),    category: Optional[str]=Form("uncategorized"),

    title: str=Form(...),    tags: Optional[str]=Form(None),

    sender: str=Form(default=""),    enable_semantic_search: bool=Form(True),

    recipient: str=Form(default=""),    current_user=Depends(get_current_user)

    departments: str=Form(default="[]"),  # JSON string):

    category: str=Form(default="uncategorized"),    """

    # JSON string    Upload document with optimized storage:
    tags: str = Form(default="[]"),

    priority: str = Form(default="medium"),    - File → AWS S3 (raw storage)

    enable_ocr: bool = Form(default=True),    - Lightweight metadata → MongoDB Atlas (~1-5KB per document)

    enable_summarization: bool = Form(default=True),    - Automatic semantic search embedding generation (optional)

    current_user: User = Depends(get_current_user),    """

    db: Session=Depends(get_db) try:

):        # Parse tags from comma-separated string

    """Upload and process a document"""        tag_list = []

            if tags:

    try:            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Validate file

        if not file.filename:        # Use optimized document service

            raise HTTPException(status_code=400, detail="No file provided")        result = get_optimized_document_service().upload_document(

                    file_obj=file.file,

        # Parse JSON fields            filename=file.filename or "untitled",

        import json            title=title,

        try:            user_id=str(current_user["id"]),

            departments_list=json.loads(departments) if departments else []            category=category or "uncategorized",

            tags_list=json.loads(tags) if tags else []            tags=tag_list,

        except json.JSONDecodeError:            content_type=file.content_type or "application/octet-stream"

            departments_list=[])

            tags_list = []

                if not result.get("success"):

        # Generate unique filename            raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))

        file_extension = os.path.splitext(file.filename)[1]

        # Trigger semantic search processing in background if enabled
        unique_filename = f"{uuid.uuid4()}{file_extension}"

                if enable_semantic_search:

        # Create upload directory if it doesn't exist            try:

        upload_dir = "uploads" await on_document_uploaded(

        os.makedirs(upload_dir, exist_ok=True)                    document_id=result["document_id"],

        file_path=os.path.join(upload_dir, unique_filename)                    user_id=str(current_user["id"]),

                            background=True  # Process in background

        # Save file                )

        content=await file.read() except Exception as e:

        # Don't fail upload if semantic processing fails
        with open(file_path, "wb") as f:

            f.write(content)                logger.warning(f"Semantic search processing failed for document {result['document_id']}: {e}")



        # Create document record        return {

        document=Document("success": True,

            title=title,            "message": "Document uploaded successfully",

            filename=file.filename,            "document": {

            file_path = file_path,                "id": result["document_id"],

            file_type = file.content_type,                "title": title,

            file_size = len(content),                "category": category or "uncategorized",

            sender = sender,                "tags": tag_list,

            recipient = recipient,                "file_size": result["metadata"]["file_size"],

            departments = departments_list,                "storage_info": result["storage"]

            category = category, },

            tags=tags_list,            "file_access": {

            priority = priority,                "s3_key": result["s3_key"],

            status = "uploaded",                "download_url": result["file_url"]

            user_id= current_user.id},

        )            "semantic_search": {

                        "enabled": enable_semantic_search,

        db.add(document)                "status": "processing" if enable_semantic_search else "disabled",

        db.commit()                "message": "Embeddings are being generated in background" if enable_semantic_search else "Semantic search not enabled for this document"

        db.refresh(document)}

                }

        # Log activity

        activity=DocumentActivity(except HTTPException:

            document_id=document.id, raise

            user_id=current_user.id, except Exception as e:

            activity_type="created", raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

            activity_description=f"Document '{title}' uploaded"

        )@router.get("/")

        db.add(activity)async def get_documents(

            skip: int=0,

        # Process document asynchronously    limit: int = 50,

        if enable_ocr or enable_summarization:    category: Optional[str]=None,

            # Start background processing    current_user = Depends(get_current_user)

            document.status="processing"):

            document.processing_stage="ocr" if enable_ocr else "summarization"    """

            db.commit()    Get user's documents from MongoDB

                """

            # Process OCR    try:

            extracted_text=""        # Get documents from MongoDB

            if enable_ocr:        # Temporarily commented out to get server started

                try:        # documents = get_mongodb_service().get_user_documents(

                    ocr_service=get_ocr_service()            user_id=str(current_user["id"]),

                    ocr_result=await ocr_service.process_document(file_path)            limit=limit,

                    extracted_text=ocr_result.get("text", "")            skip=skip

                    document.ocr_text=extracted_text)

                    document.content = extracted_text

                    document.confidence_score = ocr_result.get(
                        "confidence", 0.0)        # Filter by category if specified

                            if category:

                    logger.info(f"OCR completed for document {document.id}")            documents = [doc for doc in documents if doc.get('category') == category]

                except Exception as e:        

                    logger.error(f"OCR failed for document {document.id}: {e}")        # Log analytics event

                    analytics_event = {

            # Process summarization            "user_id": str(current_user["id"]),

            if enable_summarization and extracted_text:            "event_type": "documents_list",

                try:            "filter_category": category,

                    document.processing_stage = "summarization"            "result_count": len(documents)

                    db.commit()        }

                            mongodb_service.store_analytics_event(analytics_event)

                    summarizer = get_combined_summarizer()        

                    summary_result = await summarizer.auto_summarize(        return {

                        text=extracted_text,            "success": True,

                        role_context=current_user.role            "documents": documents,

                    )            "count": len(documents),

                                "filters": {

                    document.summary = summary_result.get("summary", {})                "category": category,

                    document.language = summary_result.get("primary_language", "english")                "skip": skip,

                                    "limit": limit

                    logger.info(f"Summarization completed for document {document.id}")            }

                except Exception as e:        }

                    logger.error(f"Summarization failed for document {document.id}: {e}")        

                except Exception as e:

            document.status = "processed"        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

            document.processing_stage = "complete"

            document.processed_at = datetime.utcnow()@router.get("/{document_id}")

        async def get_document(

        db.commit()    document_id: str,

            current_user = Depends(get_current_user)

        logger.info(f"Document uploaded: {title} by {current_user.username}")):

            """

        return {    Get specific document by ID from MongoDB

            "success": True,    """

            "data": document.to_dict(),    try:

            "message": "Document uploaded and processed successfully"        # Get document from MongoDB

        }        document = mongodb_service.get_document(document_id)

            

    except Exception as e:        if not document:

        logger.error(f"Document upload failed: {e}")            raise HTTPException(status_code=404, detail="Document not found")

        if 'document' in locals():        

            document.status = "failed"        # Check if user owns the document

            db.commit()        if document.get('user_id') != str(current_user["id"]):

        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")            raise HTTPException(status_code=403, detail="Access denied")

        

@router.get("/")        # Log analytics event

async def list_documents(        analytics_event = {

    skip: int = Query(0, ge=0),            "user_id": str(current_user["id"]),

    limit: int = Query(100, ge=1, le=1000),            "event_type": "document_view",

    category: Optional[str] = Query(None),            "document_id": document_id,

    department: Optional[str] = Query(None),            "document_category": document.get('category'),

    priority: Optional[str] = Query(None),            "document_title": document.get('title')

    status: Optional[str] = Query(None),        }

    search: Optional[str] = Query(None),        mongodb_service.store_analytics_event(analytics_event)

    current_user: User = Depends(get_current_user),        

    db: Session = Depends(get_db)        return {

):            "success": True,

    """List documents with filtering"""            "document": document

            }

    query = db.query(Document)        

        except HTTPException:

    # Apply user's department filter unless they can access all        raise

    if not current_user.can_access_all_departments:    except Exception as e:

        query = query.filter(Document.departments.contains([current_user.department]))        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

    

    # Apply filters@router.post("/search")

    if category:async def search_documents(

        query = query.filter(Document.category == category)    query: str,

        category: Optional[str] = None,

    if department:    limit: int = 20,

        query = query.filter(Document.departments.contains([department]))    current_user = Depends(get_current_user)

    ):

    if priority:    """

        query = query.filter(Document.priority == priority)    Search documents using MongoDB full-text search

        """

    if status:    try:

        query = query.filter(Document.status == status)        # Prepare search filters

            filters = {}

    if search:        if category:

        query = query.filter(            filters['category'] = category

            (Document.title.contains(search)) |        

            (Document.content.contains(search)) |        # Search documents

            (Document.sender.contains(search))        results = mongodb_service.search_documents(

        )            user_id=str(current_user["id"]),

                query=query,

    # Get total count            filters=filters,

    total = query.count()            limit=limit

            )

    # Apply pagination        

    documents = query.offset(skip).limit(limit).all()        # Log analytics event

            analytics_event = {

    return {            "user_id": str(current_user["id"]),

        "success": True,            "event_type": "document_search",

        "data": {            "search_query": query,

            "documents": [doc.to_dict() for doc in documents],            "search_category": category,

            "total": total,            "result_count": len(results)

            "skip": skip,        }

            "limit": limit        mongodb_service.store_analytics_event(analytics_event)

        }        

    }        return {

            "success": True,

@router.get("/{document_id}")            "query": query,

async def get_document(            "results": results,

    document_id: int,            "count": len(results),

    current_user: User = Depends(get_current_user),            "filters": filters

    db: Session = Depends(get_db)        }

):        

    """Get a specific document"""    except Exception as e:

            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    document = db.query(Document).filter(Document.id == document_id).first()    try:

            document_service = DocumentService(db)

    if not document:        documents = document_service.get_user_documents(

        raise HTTPException(status_code=404, detail="Document not found")            user_id=current_user["id"],

                skip=skip,

    # Check access permissions            limit=limit,

    if not current_user.can_access_all_departments:            category=category

        if current_user.department not in (document.departments or []):        )

            raise HTTPException(status_code=403, detail="Access denied")        return {"documents": documents}

        except Exception as e:

    # Log view activity        raise HTTPException(status_code=500, detail=str(e))

    activity = DocumentActivity(

        document_id=document.id,@router.get("/{document_id}")

        user_id=current_user.id,async def get_document(

        activity_type="viewed",    document_id: int,

        activity_description=f"Document viewed by {current_user.username}"    current_user = Depends(get_current_user),

    )    db: Session = Depends(get_db)

    db.add(activity)):

    db.commit()    """

        Get specific document

    return {    """

        "success": True,    try:

        "data": document.to_dict()        document_service = DocumentService(db)

    }        document = document_service.get_document(

            document_id=document_id,

@router.put("/{document_id}")            user_id=current_user["id"]

async def update_document(        )

    document_id: int,        

    title: Optional[str] = Form(None),        if not document:

    category: Optional[str] = Form(None),            raise HTTPException(status_code=404, detail="Document not found")

    tags: Optional[str] = Form(None),        

    priority: Optional[str] = Form(None),        return {"document": document}

    departments: Optional[str] = Form(None),    except Exception as e:

    current_user: User = Depends(get_current_user),        raise HTTPException(status_code=500, detail=str(e))

    db: Session = Depends(get_db)

):@router.put("/{document_id}")

    """Update document metadata"""async def update_document(

        document_id: int,

    document = db.query(Document).filter(Document.id == document_id).first()    update_data: dict,

        current_user = Depends(get_current_user),

    if not document:    db: Session = Depends(get_db)

        raise HTTPException(status_code=404, detail="Document not found")):

        """

    # Check permissions    Update document metadata

    if document.user_id != current_user.id and not current_user.can_manage_users:    """

        raise HTTPException(status_code=403, detail="Permission denied")    try:

            document_service = DocumentService(db)

    # Update fields        document = document_service.update_document(

    if title:            document_id=document_id,

        document.title = title            user_id=current_user["id"],

    if category:            update_data=update_data

        document.category = category        )

    if priority:        

        document.priority = priority        if not document:

                raise HTTPException(status_code=404, detail="Document not found")

    if tags:        

        import json        return {"message": "Document updated successfully", "document": document}

        try:    except Exception as e:

            document.tags = json.loads(tags)        raise HTTPException(status_code=500, detail=str(e))

        except json.JSONDecodeError:

            pass@router.delete("/{document_id}")

    async def delete_document(

    if departments:    document_id: int,

        import json    current_user = Depends(get_current_user),

        try:    db: Session = Depends(get_db)

            document.departments = json.loads(departments)):

        except json.JSONDecodeError:    """

            pass    Delete document

        """

    document.updated_at = datetime.utcnow()    try:

            document_service = DocumentService(db)

    # Log activity        success = document_service.delete_document(

    activity = DocumentActivity(            document_id=document_id,

        document_id=document.id,            user_id=current_user["id"]

        user_id=current_user.id,        )

        activity_type="updated",        

        activity_description=f"Document updated by {current_user.username}"        if not success:

    )            raise HTTPException(status_code=404, detail="Document not found")

    db.add(activity)        

            return {"message": "Document deleted successfully"}

    db.commit()    except Exception as e:

            raise HTTPException(status_code=500, detail=str(e))

    return {

        "success": True,@router.post("/search")

        "data": document.to_dict(),async def search_documents(

        "message": "Document updated successfully"    search_data: dict,

    }    current_user = Depends(get_current_user),

    db: Session = Depends(get_db)

@router.delete("/{document_id}")):

async def delete_document(    """

    document_id: int,    Search documents by content or metadata

    current_user: User = Depends(get_current_user),    """

    db: Session = Depends(get_db)    try:

):        document_service = DocumentService(db)

    """Delete a document"""        results = document_service.search_documents(

                user_id=current_user["id"],

    document = db.query(Document).filter(Document.id == document_id).first()            query=search_data.get("query"),

                filters=search_data.get("filters", {})

    if not document:        )

        raise HTTPException(status_code=404, detail="Document not found")        

            return {"results": results}

    # Check permissions    except Exception as e:

    if document.user_id != current_user.id and not current_user.can_manage_users:        raise HTTPException(status_code=500, detail=str(e))

        raise HTTPException(status_code=403, detail="Permission denied")

    # Google Vision routes have been removed

    # Delete file

    if document.file_path and os.path.exists(document.file_path):# Semantic Search Integration Routes

        os.remove(document.file_path)@router.get("/{document_id}/semantic-status")

    async def get_document_semantic_status(

    # Log activity before deletion    document_id: str,

    activity = DocumentActivity(    current_user = Depends(get_current_user)

        document_id=document.id,):

        user_id=current_user.id,    """

        activity_type="deleted",    Get semantic search processing status for a document

        activity_description=f"Document deleted by {current_user.username}"    """

    )    try:

    db.add(activity)        from app.services.semantic_integration import semantic_search_integration

            

    # Delete from database        status = await semantic_search_integration.get_processing_status(

    db.delete(document)            document_id=document_id,

    db.commit()            user_id=str(current_user["id"])

            )

    return {        

        "success": True,        return {

        "message": "Document deleted successfully"            "success": True,

    }            "document_id": document_id,

            "semantic_search": status

@router.get("/{document_id}/activities")        }

async def get_document_activities(        

    document_id: int,    except Exception as e:

    current_user: User = Depends(get_current_user),        raise HTTPException(status_code=500, detail=f"Failed to get semantic status: {str(e)}")

    db: Session = Depends(get_db)

):@router.post("/{document_id}/semantic-reprocess")

    """Get document activity history"""async def reprocess_document_semantics(

        document_id: str,

    document = db.query(Document).filter(Document.id == document_id).first()    current_user = Depends(get_current_user)

    ):

    if not document:    """

        raise HTTPException(status_code=404, detail="Document not found")    Reprocess document for semantic search (force regenerate embeddings)

        """

    activities = db.query(DocumentActivity).filter(    try:

        DocumentActivity.document_id == document_id        from app.services.semantic_integration import semantic_search_integration

    ).order_by(DocumentActivity.created_at.desc()).all()        

            result = await semantic_search_integration.reprocess_document(

    return {            document_id=document_id,

        "success": True,            user_id=str(current_user["id"])

        "data": [activity.to_dict() for activity in activities]        )

    }        
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