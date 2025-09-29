"""
Document model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    category = Column(String(100))
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    
    # Content and processing
    extracted_text = Column(Text)
    key_information = Column(JSON)  # Structured data extracted by NLP
    summary = Column(Text)
    keywords = Column(JSON)  # List of extracted keywords
    
    # Metadata
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    modified_date = Column(DateTime(timezone=True), onupdate=func.now())
    processed_date = Column(DateTime(timezone=True))
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="documents")
    
    # Search and indexing
    search_vector = Column(Text)  # For full-text search
    confidence_score = Column(Float)  # OCR confidence score
    
    # Document status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, error
    error_message = Column(Text)