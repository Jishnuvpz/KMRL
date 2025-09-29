"""
Semantic search models for document embeddings and search results
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, LargeBinary, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import numpy as np

class DocumentEmbedding(Base):
    """
    Model for storing document-level embeddings in the database
    Used for backup and metadata storage alongside FAISS indices
    """
    __tablename__ = "document_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to document
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Embedding metadata
    embedding_model = Column(String(100), nullable=False)  # e.g., "all-MiniLM-L6-v2"
    embedding_dimension = Column(Integer, nullable=False)
    
    # FAISS index information
    faiss_vector_id = Column(Integer, index=True)  # Position in FAISS index
    faiss_index_type = Column(String(50))  # "flat", "ivf", "hnsw"
    
    # Embedding content (stored as binary blob for efficiency)
    embedding_vector = Column(LargeBinary)  # Serialized numpy array
    
    # Text content that was embedded
    embedded_text = Column(Text)  # Full document text or summary
    embedding_source = Column(String(50))  # "full_text", "summary", "title_content"
    
    # Processing metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processing_duration = Column(Float)  # Time taken to generate embedding (seconds)
    
    # Quality metrics
    confidence_score = Column(Float)  # Confidence in the embedding quality
    text_length = Column(Integer)  # Length of embedded text
    
    # Status tracking
    is_active = Column(Boolean, default=True)  # False if document was deleted
    last_search_used = Column(DateTime(timezone=True))  # Last time used in search
    search_count = Column(Integer, default=0)  # Number of times this embedding was returned in searches
    
    # Relationships
    document = relationship("Document", back_populates="embeddings")
    chunks = relationship("DocumentChunk", back_populates="document_embedding")
    
    # Database indices for performance
    __table_args__ = (
        Index('idx_doc_embedding_model', 'document_id', 'embedding_model'),
        Index('idx_faiss_vector', 'faiss_vector_id', 'faiss_index_type'),
        Index('idx_embedding_active', 'is_active', 'created_at'),
    )
    
    def get_embedding_vector(self) -> Optional[np.ndarray]:
        """Deserialize and return the embedding vector"""
        if self.embedding_vector:
            try:
                return np.frombuffer(self.embedding_vector, dtype=np.float32).reshape(1, -1)
            except Exception:
                return None
        return None
    
    def set_embedding_vector(self, vector: np.ndarray):
        """Serialize and store the embedding vector"""
        if vector is not None:
            self.embedding_vector = vector.astype(np.float32).tobytes()
            self.embedding_dimension = vector.shape[-1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "faiss_vector_id": self.faiss_vector_id,
            "faiss_index_type": self.faiss_index_type,
            "embedding_source": self.embedding_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confidence_score": self.confidence_score,
            "text_length": self.text_length,
            "is_active": self.is_active,
            "search_count": self.search_count
        }

class DocumentChunk(Base):
    """
    Model for storing document chunk embeddings
    Used for fine-grained semantic search within documents
    """
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    document_embedding_id = Column(Integer, ForeignKey("document_embeddings.id"), nullable=True)
    
    # Chunk identification
    chunk_index = Column(Integer, nullable=False)  # Order within document (0, 1, 2, ...)
    chunk_id = Column(String(100), nullable=False, index=True)  # Unique identifier
    
    # Chunk content
    chunk_text = Column(Text, nullable=False)
    chunk_type = Column(String(50))  # "paragraph", "sentence", "page", "section"
    
    # Position information
    start_position = Column(Integer)  # Character position in original document
    end_position = Column(Integer)
    page_number = Column(Integer)  # For PDF documents
    
    # Embedding metadata
    embedding_model = Column(String(100), nullable=False)
    embedding_dimension = Column(Integer, nullable=False)
    
    # FAISS index information
    faiss_vector_id = Column(Integer, index=True)
    faiss_index_type = Column(String(50))
    
    # Embedding content
    embedding_vector = Column(LargeBinary)
    
    # Quality and processing metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_duration = Column(Float)
    confidence_score = Column(Float)
    
    # Search analytics
    is_active = Column(Boolean, default=True)
    last_search_used = Column(DateTime(timezone=True))
    search_count = Column(Integer, default=0)
    relevance_score_avg = Column(Float)  # Average relevance score when returned
    
    # Relationships
    document = relationship("Document")
    document_embedding = relationship("DocumentEmbedding", back_populates="chunks")
    search_results = relationship("SemanticSearchResult", back_populates="chunk")
    
    # Database indices
    __table_args__ = (
        Index('idx_chunk_document', 'document_id', 'chunk_index'),
        Index('idx_chunk_faiss', 'faiss_vector_id', 'is_active'),
        Index('idx_chunk_position', 'document_id', 'start_position', 'end_position'),
    )
    
    def get_embedding_vector(self) -> Optional[np.ndarray]:
        """Deserialize and return the embedding vector"""
        if self.embedding_vector:
            try:
                return np.frombuffer(self.embedding_vector, dtype=np.float32).reshape(1, -1)
            except Exception:
                return None
        return None
    
    def set_embedding_vector(self, vector: np.ndarray):
        """Serialize and store the embedding vector"""
        if vector is not None:
            self.embedding_vector = vector.astype(np.float32).tobytes()
            self.embedding_dimension = vector.shape[-1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "chunk_id": self.chunk_id,
            "chunk_text": self.chunk_text,
            "chunk_type": self.chunk_type,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "page_number": self.page_number,
            "embedding_model": self.embedding_model,
            "confidence_score": self.confidence_score,
            "search_count": self.search_count,
            "is_active": self.is_active
        }

class SemanticSearchQuery(Base):
    """
    Model for tracking semantic search queries and analytics
    """
    __tablename__ = "semantic_search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(255))  # For anonymous users
    
    # Query details
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50))  # "document", "chunk", "hybrid"
    
    # Search parameters
    search_k = Column(Integer, default=10)  # Number of results requested
    score_threshold = Column(Float, default=0.0)
    filters_applied = Column(Text)  # JSON string of applied filters
    
    # Embedding information
    embedding_model = Column(String(100))
    query_embedding = Column(LargeBinary)  # Serialized query embedding
    
    # Performance metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    execution_time = Column(Float)  # Search execution time in seconds
    results_count = Column(Integer)  # Number of results returned
    
    # User interaction
    clicked_results = Column(Text)  # JSON array of clicked result IDs
    user_feedback = Column(String(20))  # "helpful", "not_helpful", "irrelevant"
    
    # Relationships
    user = relationship("User")
    results = relationship("SemanticSearchResult", back_populates="query")
    
    def get_query_embedding(self) -> Optional[np.ndarray]:
        """Deserialize and return the query embedding"""
        if self.query_embedding:
            try:
                return np.frombuffer(self.query_embedding, dtype=np.float32).reshape(1, -1)
            except Exception:
                return None
        return None
    
    def set_query_embedding(self, vector: np.ndarray):
        """Serialize and store the query embedding"""
        if vector is not None:
            self.query_embedding = vector.astype(np.float32).tobytes()

class SemanticSearchResult(Base):
    """
    Model for storing individual search results with relevance scores
    """
    __tablename__ = "semantic_search_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    query_id = Column(Integer, ForeignKey("semantic_search_queries.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=True, index=True)
    
    # Result metadata
    rank = Column(Integer, nullable=False)  # Position in search results (1, 2, 3, ...)
    relevance_score = Column(Float, nullable=False)  # Similarity score from FAISS
    result_type = Column(String(50))  # "document", "chunk"
    
    # FAISS metadata
    faiss_vector_id = Column(Integer)
    faiss_distance = Column(Float)  # Raw distance from FAISS
    
    # User interaction tracking
    was_clicked = Column(Boolean, default=False)
    click_timestamp = Column(DateTime(timezone=True))
    time_to_click = Column(Float)  # Seconds from search to click
    
    # Quality metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    query = relationship("SemanticSearchQuery", back_populates="results")
    document = relationship("Document")
    chunk = relationship("DocumentChunk", back_populates="search_results")
    
    # Database indices
    __table_args__ = (
        Index('idx_search_result_query', 'query_id', 'rank'),
        Index('idx_search_result_document', 'document_id', 'relevance_score'),
        Index('idx_search_result_interaction', 'was_clicked', 'click_timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "query_id": self.query_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "rank": self.rank,
            "relevance_score": self.relevance_score,
            "result_type": self.result_type,
            "was_clicked": self.was_clicked,
            "click_timestamp": self.click_timestamp.isoformat() if self.click_timestamp else None,
            "time_to_click": self.time_to_click
        }

class SearchAnalytics(Base):
    """
    Model for aggregated search analytics and performance metrics
    """
    __tablename__ = "search_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20))  # "hour", "day", "week", "month"
    
    # Search volume metrics
    total_searches = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    anonymous_searches = Column(Integer, default=0)
    
    # Performance metrics
    avg_execution_time = Column(Float)
    avg_results_count = Column(Float)
    avg_relevance_score = Column(Float)
    
    # User engagement
    total_clicks = Column(Integer, default=0)
    click_through_rate = Column(Float)  # Percentage of searches with clicks
    avg_time_to_click = Column(Float)
    
    # Query analysis
    top_query_terms = Column(Text)  # JSON array of popular terms
    avg_query_length = Column(Float)
    
    # System health
    search_errors = Column(Integer, default=0)
    embedding_generation_time = Column(Float)
    faiss_index_size = Column(Integer)  # Number of vectors
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Database indices
    __table_args__ = (
        Index('idx_analytics_date_period', 'date', 'period_type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "period_type": self.period_type,
            "total_searches": self.total_searches,
            "unique_users": self.unique_users,
            "avg_execution_time": self.avg_execution_time,
            "avg_results_count": self.avg_results_count,
            "total_clicks": self.total_clicks,
            "click_through_rate": self.click_through_rate,
            "search_errors": self.search_errors,
            "faiss_index_size": self.faiss_index_size
        }

# Add relationships to existing models

# Add to Document model (would be added to app/models/document.py)
# class Document(Base):
#     ...
#     embeddings = relationship("DocumentEmbedding", back_populates="document")
#     chunks = relationship("DocumentChunk", back_populates="document")