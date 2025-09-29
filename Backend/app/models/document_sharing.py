"""
Document sharing and collaboration models for KMRL Document Management System
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class SharePermission(enum.Enum):
    """Permission levels for document sharing"""
    VIEW = "view"           # Can only view the document
    COMMENT = "comment"     # Can view and add comments
    EDIT = "edit"          # Can view, comment, and edit
    ADMIN = "admin"        # Full control including sharing management


class ShareStatus(enum.Enum):
    """Status of share invitation"""
    PENDING = "pending"     # Invitation sent but not accepted
    ACCEPTED = "accepted"   # User has accepted the share
    DECLINED = "declined"   # User has declined the share
    REVOKED = "revoked"     # Share has been revoked by owner


class DocumentShare(Base):
    """Model for document sharing between users"""
    __tablename__ = "document_shares"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"),
                      nullable=False)  # User who shared the document
    shared_with_id = Column(Integer, ForeignKey(
        "users.id"), nullable=False)  # User document is shared with

    # Sharing configuration
    permission = Column(Enum(SharePermission), nullable=False,
                        default=SharePermission.VIEW)
    status = Column(Enum(ShareStatus), nullable=False,
                    default=ShareStatus.PENDING)

    # Access control
    # Can the shared user share with others
    can_reshare = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration date
    # Track how many times document was accessed
    access_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # When user accepted the share
    accepted_at = Column(DateTime(timezone=True))
    # Last time shared user accessed document
    last_accessed = Column(DateTime(timezone=True))

    # Optional sharing message
    message = Column(Text)  # Message from owner when sharing

    # Relationships
    document = relationship("Document")
    owner = relationship("User", foreign_keys=[owner_id])
    shared_with = relationship("User", foreign_keys=[shared_with_id])
    comments = relationship("DocumentComment", back_populates="share")

    def __repr__(self):
        return f"<DocumentShare(document_id={self.document_id}, shared_with={self.shared_with_id}, permission={self.permission.value})>"


class DocumentComment(Base):
    """Model for comments on shared documents"""
    __tablename__ = "document_comments"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    share_id = Column(Integer, ForeignKey("document_shares.id"),
                      nullable=True)  # Link to share if applicable
    parent_comment_id = Column(Integer, ForeignKey(
        "document_comments.id"), nullable=True)  # For threaded comments

    # Comment content
    content = Column(Text, nullable=False)
    # general, review, approval, question
    comment_type = Column(String(20), default="general")

    # For PDF documents positioning
    # For PDF documents, which page the comment is on
    page_number = Column(Integer)
    position_x = Column(Integer)   # X coordinate for positioning
    position_y = Column(Integer)   # Y coordinate for positioning

    # Status
    is_resolved = Column(Boolean, default=False)  # For action items/feedback
    is_deleted = Column(Boolean, default=False)   # Soft delete

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    document = relationship("Document")
    user = relationship("User")
    share = relationship("DocumentShare", back_populates="comments")
    # Self-referential for threaded comments
    replies = relationship("DocumentComment", remote_side=[id])

    def __repr__(self):
        return f"<DocumentComment(document_id={self.document_id}, user_id={self.user_id})>"


class DocumentActivity(Base):
    """Model for tracking activity on shared documents"""
    __tablename__ = "document_activities"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    share_id = Column(Integer, ForeignKey("document_shares.id"), nullable=True)

    # Activity details
    # view, edit, comment, share, download, etc.
    activity_type = Column(String(50), nullable=False)
    description = Column(Text)  # Human-readable description
    # JSON string for additional activity data
    activity_metadata = Column(Text)

    # Tracking
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(String(500))

    # Relationships
    document = relationship("Document")
    user = relationship("User")
    share = relationship("DocumentShare")

    def __repr__(self):
        return f"<DocumentActivity(document_id={self.document_id}, user_id={self.user_id}, type={self.activity_type})>"


class CollaborationSession(Base):
    """Model for real-time collaboration sessions"""
    __tablename__ = "collaboration_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Session details
    session_id = Column(String(255), unique=True,
                        nullable=False)  # WebSocket session ID
    is_active = Column(Boolean, default=True)

    # Presence information
    current_page = Column(Integer, default=1)
    cursor_position = Column(String(100))  # JSON string for cursor position
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now())

    # Session tracking
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))

    # Relationships
    document = relationship("Document")
    user = relationship("User")

    def __repr__(self):
        return f"<CollaborationSession(document_id={self.document_id}, user_id={self.user_id}, active={self.is_active})>"
