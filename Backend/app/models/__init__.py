"""
Database models for KMRL Document Management System
"""

# Import all models for easy access
from .user import User
from .document import Document
from .document_sharing import DocumentShare, DocumentComment, DocumentActivity, CollaborationSession
from .alert import Alert, SystemNotification, AlertRule
from .session import UserSession, SessionActivity, SystemSettings

# Define all models for easy import
__all__ = [
    "User",
    "Document",
    "DocumentShare",
    "DocumentComment",
    "DocumentActivity",
    "CollaborationSession",
    "Alert",
    "SystemNotification",
    "AlertRule",
    "UserSession",
    "SessionActivity",
    "SystemSettings"
]
