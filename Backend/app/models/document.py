"""
Document model for KMRL Document Management System
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Document(Base):
    __tablename__ = "documents"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic document information
    title = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))

    # Content and processing
    content = Column(Text)
    ocr_text = Column(Text)
    extracted_text = Column(Text)
    summary = Column(JSON)  # {"en": "summary", "ml": "summary"}
    key_information = Column(JSON)  # Structured data extracted by NLP
    keywords = Column(JSON)  # List of extracted keywords
    language = Column(String(20), default="english")

    # Metadata
    sender = Column(String(255))
    recipient = Column(String(255))
    departments = Column(JSON)  # List of department names
    category = Column(String(100), default="uncategorized")
    tags = Column(JSON)  # List of tags
    # low, medium, high, critical
    priority = Column(String(20), default="medium")

    # Search and indexing
    search_vector = Column(Text)  # For full-text search
    confidence_score = Column(Float)  # OCR confidence score

    # Status and processing
    # uploaded, processing, processed, failed
    status = Column(String(50), default="uploaded")
    processing_stage = Column(String(50))  # ocr, summarization, indexing
    # pending, processing, completed, error
    processing_status = Column(String(50), default="pending")
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    modified_date = Column(DateTime(timezone=True), onupdate=func.now())
    processed_date = Column(DateTime(timezone=True))

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="documents")

    # Document sharing
    shares = relationship("DocumentShare", back_populates="document")
    comments = relationship("DocumentComment", back_populates="document")
    activities = relationship("DocumentActivity", back_populates="document")

    # Alerts and notifications
    alerts = relationship("Alert", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "content": self.content,
            "ocr_text": self.ocr_text,
            "summary": self.summary,
            "language": self.language,
            "sender": self.sender,
            "recipient": self.recipient,
            "departments": self.departments,
            "category": self.category,
            "tags": self.tags,
            "priority": self.priority,
            "status": self.status,
            "processing_stage": self.processing_stage,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "user_id": self.user_id
        }
