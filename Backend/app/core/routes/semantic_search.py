"""
Semantic Search API Routes for FAISS-based document similarity search
Provides endpoints for search queries, embedding management, and search analytics
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import time
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.database import get_db
from app.models.semantic_search import (
    DocumentEmbedding, 
    DocumentChunk, 
    SemanticSearchQuery, 
    SemanticSearchResult, 
    SearchAnalytics
)
from app.models.document import Document
from app.services.faiss_service import get_faiss_service
from app.services.embedding_service import get_embedding_service
from app.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/semantic-search", tags=["Semantic Search"])

# Pydantic models for request/response

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    search_type: str = Field(default="hybrid", description="Search type: 'document', 'chunk', or 'hybrid'")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score")
    document_types: Optional[List[str]] = Field(default=None, description="Filter by document types")
    date_range: Optional[Dict[str, str]] = Field(default=None, description="Date range filter")
    include_chunks: bool = Field(default=False, description="Include chunk details in results")

class SearchResult(BaseModel):
    document_id: int
    title: str
    file_type: str
    similarity_score: float
    snippet: Optional[str] = None
    chunks: Optional[List[Dict[str, Any]]] = None
    created_at: str
    author: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    search_type: str
    query_id: Optional[int] = None

class EmbeddingRequest(BaseModel):
    document_id: int
    force_regenerate: bool = Field(default=False, description="Force regeneration of existing embeddings")
    chunk_strategy: str = Field(default="paragraph", description="Chunking strategy: paragraph, sentence, fixed_size")

class EmbeddingResponse(BaseModel):
    document_id: int
    embeddings_generated: int
    chunks_created: int
    processing_time_ms: float
    status: str

class AnalyticsResponse(BaseModel):
    total_queries: int
    avg_response_time_ms: float
    popular_queries: List[Dict[str, Any]]
    search_types_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]

@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform semantic search across documents and chunks
    """
    start_time = time.time()
    
    try:
        # Get services
        faiss_service = get_faiss_service()
        embedding_service = get_embedding_service()
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(request.query)
        if query_embedding is None:
            raise HTTPException(status_code=400, detail="Failed to generate query embedding")
        
        # Store search query
        search_query = SemanticSearchQuery(
            user_id=current_user.id,
            query_text=request.query,
            search_type=request.search_type,
            parameters={
                "top_k": request.top_k,
                "min_score": request.min_score,
                "document_types": request.document_types,
                "include_chunks": request.include_chunks
            }
        )
        db.add(search_query)
        db.commit()
        db.refresh(search_query)
        
        # Perform search based on type
        results = []
        
        if request.search_type in ["document", "hybrid"]:
            doc_results = await _search_documents(
                faiss_service, query_embedding, request, db, current_user
            )
            results.extend(doc_results)
        
        if request.search_type in ["chunk", "hybrid"]:
            chunk_results = await _search_chunks(
                faiss_service, query_embedding, request, db, current_user
            )
            results.extend(chunk_results)
        
        # Remove duplicates and sort by score
        seen_docs = set()
        unique_results = []
        for result in sorted(results, key=lambda x: x.similarity_score, reverse=True):
            if result.document_id not in seen_docs:
                unique_results.append(result)
                seen_docs.add(result.document_id)
        
        # Apply top_k limit
        final_results = unique_results[:request.top_k]
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Store search results and analytics in background
        background_tasks.add_task(
            _store_search_results, 
            db, search_query.id, final_results, response_time
        )
        
        return SearchResponse(
            query=request.query,
            results=final_results,
            total_results=len(final_results),
            search_time_ms=round(response_time, 2),
            search_type=request.search_type,
            query_id=search_query.id
        )
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

async def _search_documents(
    faiss_service, 
    query_embedding, 
    request: SearchRequest, 
    db: Session, 
    current_user: User
) -> List[SearchResult]:
    """Search at document level"""
    try:
        # Get document embeddings
        doc_embeddings_query = db.query(DocumentEmbedding).join(Document).filter(
            Document.user_id == current_user.id
        )
        
        # Apply filters
        if request.document_types:
            doc_embeddings_query = doc_embeddings_query.filter(
                Document.file_type.in_(request.document_types)
            )
        
        doc_embeddings = doc_embeddings_query.all()
        
        if not doc_embeddings:
            return []
        
        # Prepare embeddings for FAISS search
        embeddings_data = [
            {
                "embedding": doc_emb.get_embedding_vector(),
                "document_id": doc_emb.document_id,
                "metadata": {"type": "document"}
            }
            for doc_emb in doc_embeddings
            if doc_emb.get_embedding_vector() is not None
        ]
        
        if not embeddings_data:
            return []
        
        # Perform FAISS search
        search_results = await faiss_service.search_similar(
            query_embedding=query_embedding,
            embeddings_data=embeddings_data,
            top_k=request.top_k * 2,  # Get more to allow for filtering
            threshold=request.min_score
        )
        
        # Convert to SearchResult objects
        results = []
        for result in search_results:
            doc_id = result["metadata"]["document_id"]
            document = db.query(Document).filter(Document.id == doc_id).first()
            
            if document and result["similarity"] >= request.min_score:
                results.append(SearchResult(
                    document_id=doc_id,
                    title=document.title,
                    file_type=document.file_type,
                    similarity_score=round(result["similarity"], 4),
                    snippet=_generate_snippet(document.content, request.query),
                    created_at=document.created_at.isoformat(),
                    author=document.user.username if document.user else None
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error in document search: {e}")
        return []

async def _search_chunks(
    faiss_service, 
    query_embedding, 
    request: SearchRequest, 
    db: Session, 
    current_user: User
) -> List[SearchResult]:
    """Search at chunk level"""
    try:
        # Get chunk embeddings
        chunk_embeddings_query = db.query(DocumentChunk).join(
            DocumentEmbedding
        ).join(Document).filter(
            Document.user_id == current_user.id
        )
        
        # Apply filters
        if request.document_types:
            chunk_embeddings_query = chunk_embeddings_query.filter(
                Document.file_type.in_(request.document_types)
            )
        
        chunk_embeddings = chunk_embeddings_query.all()
        
        if not chunk_embeddings:
            return []
        
        # Prepare embeddings for FAISS search
        embeddings_data = [
            {
                "embedding": chunk.get_embedding_vector(),
                "document_id": chunk.document_embedding.document_id,
                "chunk_id": chunk.id,
                "metadata": {
                    "type": "chunk",
                    "chunk_text": chunk.chunk_text,
                    "start_position": chunk.start_position,
                    "end_position": chunk.end_position
                }
            }
            for chunk in chunk_embeddings
            if chunk.get_embedding_vector() is not None
        ]
        
        if not embeddings_data:
            return []
        
        # Perform FAISS search
        search_results = await faiss_service.search_similar(
            query_embedding=query_embedding,
            embeddings_data=embeddings_data,
            top_k=request.top_k * 3,  # Get more for chunk-to-document aggregation
            threshold=request.min_score
        )
        
        # Aggregate chunks by document
        doc_chunks = {}
        for result in search_results:
            doc_id = result["metadata"]["document_id"]
            if doc_id not in doc_chunks:
                doc_chunks[doc_id] = []
            doc_chunks[doc_id].append(result)
        
        # Convert to SearchResult objects
        results = []
        for doc_id, chunks in doc_chunks.items():
            document = db.query(Document).filter(Document.id == doc_id).first()
            if not document:
                continue
            
            # Use best chunk score for document score
            best_score = max(chunk["similarity"] for chunk in chunks)
            
            if best_score >= request.min_score:
                chunk_details = None
                if request.include_chunks:
                    chunk_details = [
                        {
                            "chunk_id": chunk["metadata"]["chunk_id"],
                            "text": chunk["metadata"]["chunk_text"],
                            "score": round(chunk["similarity"], 4),
                            "position": {
                                "start": chunk["metadata"]["start_position"],
                                "end": chunk["metadata"]["end_position"]
                            }
                        }
                        for chunk in chunks[:5]  # Limit to top 5 chunks per document
                    ]
                
                # Use best chunk text as snippet
                best_chunk = max(chunks, key=lambda x: x["similarity"])
                snippet = best_chunk["metadata"]["chunk_text"][:200] + "..."
                
                results.append(SearchResult(
                    document_id=doc_id,
                    title=document.title,
                    file_type=document.file_type,
                    similarity_score=round(best_score, 4),
                    snippet=snippet,
                    chunks=chunk_details,
                    created_at=document.created_at.isoformat(),
                    author=document.user.username if document.user else None
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error in chunk search: {e}")
        return []

def _generate_snippet(content: str, query: str, max_length: int = 200) -> str:
    """Generate a snippet from document content based on query"""
    if not content:
        return ""
    
    # Simple implementation - find query terms in content
    query_terms = query.lower().split()
    content_lower = content.lower()
    
    # Find first occurrence of any query term
    best_position = 0
    for term in query_terms:
        pos = content_lower.find(term)
        if pos != -1:
            best_position = max(0, pos - 50)  # Start 50 chars before
            break
    
    # Extract snippet
    snippet = content[best_position:best_position + max_length]
    if best_position > 0:
        snippet = "..." + snippet
    if len(content) > best_position + max_length:
        snippet = snippet + "..."
    
    return snippet

async def _store_search_results(
    db: Session, 
    query_id: int, 
    results: List[SearchResult], 
    response_time: float
):
    """Store search results and analytics in background"""
    try:
        # Store individual results
        for rank, result in enumerate(results, 1):
            search_result = SemanticSearchResult(
                query_id=query_id,
                document_id=result.document_id,
                similarity_score=result.similarity_score,
                rank=rank
            )
            db.add(search_result)
        
        # Store analytics
        analytics = SearchAnalytics(
            query_id=query_id,
            results_count=len(results),
            response_time_ms=response_time,
            clicked_results=[]  # Will be updated when user clicks
        )
        db.add(analytics)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error storing search results: {e}")
        db.rollback()

@router.post("/embeddings/generate", response_model=EmbeddingResponse)
async def generate_document_embeddings(
    request: EmbeddingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate embeddings for a specific document
    """
    start_time = time.time()
    
    try:
        # Get document
        document = db.query(Document).filter(
            and_(Document.id == request.document_id, Document.user_id == current_user.id)
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if embeddings already exist
        existing_embedding = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.document_id == request.document_id
        ).first()
        
        if existing_embedding and not request.force_regenerate:
            raise HTTPException(
                status_code=400, 
                detail="Embeddings already exist. Use force_regenerate=true to overwrite."
            )
        
        # Generate embeddings in background
        background_tasks.add_task(
            _generate_embeddings_background,
            db, document, request.chunk_strategy, request.force_regenerate
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return EmbeddingResponse(
            document_id=request.document_id,
            embeddings_generated=0,  # Will be updated in background
            chunks_created=0,
            processing_time_ms=round(processing_time, 2),
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embeddings")

async def _generate_embeddings_background(
    db: Session, 
    document: Document, 
    chunk_strategy: str, 
    force_regenerate: bool
):
    """Generate embeddings in background task"""
    try:
        embedding_service = get_embedding_service()
        faiss_service = get_faiss_service()
        
        # Delete existing embeddings if force regenerate
        if force_regenerate:
            existing = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document.id
            ).first()
            if existing:
                db.delete(existing)
                db.commit()
        
        # Generate document-level embedding
        doc_embedding_vector = await embedding_service.generate_embedding(
            f"{document.title} {document.content[:2000]}"
        )
        
        if doc_embedding_vector is None:
            logger.error(f"Failed to generate document embedding for document {document.id}")
            return
        
        # Create document embedding record
        doc_embedding = DocumentEmbedding(
            document_id=document.id,
            embedding_model=embedding_service.model_name,
            embedding_dimension=len(doc_embedding_vector)
        )
        doc_embedding.set_embedding_vector(doc_embedding_vector)
        
        db.add(doc_embedding)
        db.commit()
        db.refresh(doc_embedding)
        
        # Generate chunk embeddings
        chunks_data = await embedding_service.chunk_and_embed_document(
            document.content,
            chunk_strategy=chunk_strategy
        )
        
        # Store chunks in database
        chunks_created = 0
        for chunk_data in chunks_data:
            chunk = DocumentChunk(
                document_embedding_id=doc_embedding.id,
                chunk_index=chunk_data["chunk_index"],
                chunk_text=chunk_data["text"],
                start_position=chunk_data["start_position"],
                end_position=chunk_data["end_position"],
                chunk_type=chunk_data["chunk_type"],
                confidence_score=chunk_data["confidence_score"]
            )
            chunk.set_embedding_vector(chunk_data["embedding"])
            
            db.add(chunk)
            chunks_created += 1
        
        db.commit()
        
        # Add embeddings to FAISS index
        await faiss_service.add_embeddings([
            {
                "embedding": doc_embedding.get_embedding_vector(),
                "metadata": {"document_id": document.id, "type": "document"}
            }
        ] + [
            {
                "embedding": chunk_data["embedding"],
                "metadata": {
                    "document_id": document.id,
                    "type": "chunk",
                    "chunk_index": chunk_data["chunk_index"]
                }
            }
            for chunk_data in chunks_data
        ])
        
        logger.info(f"Generated embeddings for document {document.id}: 1 document + {chunks_created} chunks")
        
    except Exception as e:
        logger.error(f"Error in background embedding generation: {e}")
        db.rollback()

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_search_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get search analytics and insights
    """
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total queries
        total_queries = db.query(SemanticSearchQuery).filter(
            and_(
                SemanticSearchQuery.user_id == current_user.id,
                SemanticSearchQuery.created_at >= cutoff_date
            )
        ).count()
        
        # Average response time
        avg_response = db.query(SearchAnalytics).join(SemanticSearchQuery).filter(
            and_(
                SemanticSearchQuery.user_id == current_user.id,
                SemanticSearchQuery.created_at >= cutoff_date
            )
        ).all()
        
        avg_response_time = 0
        if avg_response:
            avg_response_time = sum(a.response_time_ms for a in avg_response) / len(avg_response)
        
        # Popular queries (simplified)
        popular_queries = []
        
        # Search types distribution
        search_types = db.query(SemanticSearchQuery.search_type).filter(
            and_(
                SemanticSearchQuery.user_id == current_user.id,
                SemanticSearchQuery.created_at >= cutoff_date
            )
        ).all()
        
        search_types_dist = {}
        for (search_type,) in search_types:
            search_types_dist[search_type] = search_types_dist.get(search_type, 0) + 1
        
        # Recent activity
        recent_queries = db.query(SemanticSearchQuery).filter(
            and_(
                SemanticSearchQuery.user_id == current_user.id,
                SemanticSearchQuery.created_at >= cutoff_date
            )
        ).order_by(desc(SemanticSearchQuery.created_at)).limit(10).all()
        
        recent_activity = [
            {
                "query": q.query_text,
                "search_type": q.search_type,
                "timestamp": q.created_at.isoformat()
            }
            for q in recent_queries
        ]
        
        return AnalyticsResponse(
            total_queries=total_queries,
            avg_response_time_ms=round(avg_response_time, 2),
            popular_queries=popular_queries,
            search_types_distribution=search_types_dist,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@router.get("/status")
async def get_search_status():
    """
    Get status of semantic search services
    """
    try:
        faiss_service = get_faiss_service()
        embedding_service = get_embedding_service()
        
        # Get service information
        faiss_info = await faiss_service.get_index_info()
        embedding_info = await embedding_service.get_model_info()
        
        return {
            "status": "healthy",
            "faiss_service": faiss_info,
            "embedding_service": embedding_info,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error getting search status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }