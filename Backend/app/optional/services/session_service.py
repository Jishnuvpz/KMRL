"""
Session Management Service
=========================

Comprehensive session management service for user authentication and state management.
Handles session creation, validation, refresh, cleanup, and multi-device support.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import asyncio
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.models.user_session import (
    UserSession, 
    SessionResponse, 
    ActiveSessionsResponse,
    SessionCreateRequest,
    SessionValidationResponse,
    SESSION_INDEXES,
    SessionConfig
)
from app.db import get_database

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing user sessions with MongoDB persistence.
    
    Features:
    - Session creation and validation
    - Automatic session cleanup
    - Multi-device session support
    - Session refresh and extension
    - Security monitoring
    """
    
    def __init__(self):
        """Initialize session service with database connection"""
        self.db = None
        self.sessions_collection: Optional[Collection] = None
        self._cleanup_task = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service and set up database indexes"""
        if self._initialized:
            return
        
        try:
            self.db = await get_database()
            self.sessions_collection = self.db.user_sessions
            
            # Create indexes for optimal performance
            await self._ensure_indexes()
            
            # Start automatic cleanup task
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            self._initialized = True
            logger.info("Session service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize session service: {e}")
            raise
    
    async def _ensure_indexes(self):
        """Ensure all required indexes exist"""
        try:
            for index in SESSION_INDEXES:
                await self.sessions_collection.create_index(index.document)
            logger.info("Session collection indexes created/verified")
        except Exception as e:
            logger.error(f"Failed to create session indexes: {e}")
    
    async def create_session(self, request: SessionCreateRequest) -> UserSession:
        """
        Create a new user session.
        
        Args:
            request: Session creation request with user details
            
        Returns:
            UserSession: Created session object
            
        Raises:
            Exception: If session creation fails
        """
        try:
            # Check active session limit per user
            active_count = await self._count_active_sessions(request.user_id)
            if active_count >= SessionConfig.MAX_SESSIONS_PER_USER:
                # Deactivate oldest session
                await self._deactivate_oldest_session(request.user_id)
            
            # Create new session
            session = UserSession(
                user_id=request.user_id,
                device_info=request.device_info or {},
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                expires_at=datetime.utcnow() + timedelta(hours=request.session_duration_hours)
            )
            
            # Store in database
            await self.sessions_collection.insert_one(session.to_dict())
            
            logger.info(f"Created session {session.session_id} for user {request.user_id}")
            return session
            
        except DuplicateKeyError:
            logger.error(f"Session ID collision for user {request.user_id}")
            # Retry with new UUID
            return await self.create_session(request)
        except Exception as e:
            logger.error(f"Failed to create session for user {request.user_id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            UserSession: Session object or None if not found
        """
        try:
            session_data = await self.sessions_collection.find_one({"session_id": session_id})
            
            if not session_data:
                return None
            
            session = UserSession(**session_data)
            
            # Update last accessed time
            if session.is_active and not session.is_expired():
                await self._update_last_accessed(session_id)
                session.last_accessed = datetime.utcnow()
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None
    
    async def validate_session(self, session_id: str) -> SessionValidationResponse:
        """
        Validate a session and return detailed status.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionValidationResponse: Validation result with details
        """
        try:
            session = await self.get_session(session_id)
            
            if not session:
                return SessionValidationResponse(is_valid=False)
            
            # Check if session is expired or inactive
            if not session.is_active or session.is_expired():
                return SessionValidationResponse(
                    is_valid=False,
                    session_id=session_id
                )
            
            # Check if session needs refresh (expires within threshold)
            needs_refresh = (
                session.expires_at - datetime.utcnow()
            ).total_seconds() < (SessionConfig.SESSION_REFRESH_THRESHOLD_HOURS * 3600)
            
            return SessionValidationResponse(
                is_valid=True,
                session_id=session.session_id,
                user_id=session.user_id,
                expires_at=session.expires_at,
                last_accessed=session.last_accessed,
                needs_refresh=needs_refresh
            )
            
        except Exception as e:
            logger.error(f"Failed to validate session {session_id}: {e}")
            return SessionValidationResponse(is_valid=False)
    
    async def refresh_session(self, session_id: str, extend_hours: int = 24) -> bool:
        """
        Refresh a session, extending its expiration time.
        
        Args:
            session_id: Session identifier
            extend_hours: Hours to extend the session
            
        Returns:
            bool: True if refresh successful, False otherwise
        """
        try:
            session = await self.get_session(session_id)
            
            if not session or not session.can_refresh():
                return False
            
            # Update session in database
            update_result = await self.sessions_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "expires_at": datetime.utcnow() + timedelta(hours=extend_hours),
                        "last_accessed": datetime.utcnow()
                    },
                    "$inc": {"refresh_count": 1}
                }
            )
            
            success = update_result.modified_count > 0
            if success:
                logger.info(f"Refreshed session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to refresh session {session_id}: {e}")
            return False
    
    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate (logout) a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if invalidation successful
        """
        try:
            update_result = await self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"is_active": False}}
            )
            
            success = update_result.modified_count > 0
            if success:
                logger.info(f"Invalidated session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False
    
    async def invalidate_user_sessions(self, user_id: str, except_session: Optional[str] = None) -> int:
        """
        Invalidate all sessions for a user (global logout).
        
        Args:
            user_id: User identifier
            except_session: Session ID to keep active (current session)
            
        Returns:
            int: Number of sessions invalidated
        """
        try:
            query = {"user_id": user_id, "is_active": True}
            if except_session:
                query["session_id"] = {"$ne": except_session}
            
            update_result = await self.sessions_collection.update_many(
                query,
                {"$set": {"is_active": False}}
            )
            
            count = update_result.modified_count
            logger.info(f"Invalidated {count} sessions for user {user_id}")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to invalidate sessions for user {user_id}: {e}")
            return 0
    
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> ActiveSessionsResponse:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            active_only: Whether to return only active sessions
            
        Returns:
            ActiveSessionsResponse: User's session information
        """
        try:
            query = {"user_id": user_id}
            if active_only:
                query["is_active"] = True
                query["expires_at"] = {"$gt": datetime.utcnow()}
            
            cursor = self.sessions_collection.find(query).sort("last_accessed", -1)
            sessions_data = await cursor.to_list(length=None)
            
            sessions = []
            for session_data in sessions_data:
                session = UserSession(**session_data)
                sessions.append(SessionResponse(
                    session_id=session.session_id,
                    user_id=session.user_id,
                    expires_at=session.expires_at,
                    is_active=session.is_active,
                    last_accessed=session.last_accessed,
                    device_info=session.device_info
                ))
            
            return ActiveSessionsResponse(
                user_id=user_id,
                total_sessions=len(sessions),
                active_sessions=sessions
            )
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return ActiveSessionsResponse(
                user_id=user_id,
                total_sessions=0,
                active_sessions=[]
            )
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired and inactive sessions.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            # Delete expired sessions
            delete_result = await self.sessions_collection.delete_many({
                "$or": [
                    {"expires_at": {"$lt": datetime.utcnow()}},
                    {"is_active": False}
                ]
            })
            
            count = delete_result.deleted_count
            if count > 0:
                logger.info(f"Cleaned up {count} expired/inactive sessions")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    async def _count_active_sessions(self, user_id: str) -> int:
        """Count active sessions for a user"""
        try:
            count = await self.sessions_collection.count_documents({
                "user_id": user_id,
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            return count
        except Exception as e:
            logger.error(f"Failed to count active sessions for {user_id}: {e}")
            return 0
    
    async def _deactivate_oldest_session(self, user_id: str):
        """Deactivate the oldest active session for a user"""
        try:
            oldest_session = await self.sessions_collection.find_one(
                {
                    "user_id": user_id,
                    "is_active": True
                },
                sort=[("created_at", 1)]
            )
            
            if oldest_session:
                await self.invalidate_session(oldest_session["session_id"])
                logger.info(f"Deactivated oldest session for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to deactivate oldest session for {user_id}: {e}")
    
    async def _update_last_accessed(self, session_id: str):
        """Update the last accessed time for a session"""
        try:
            await self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"last_accessed": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Failed to update last accessed for session {session_id}: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic task to cleanup expired sessions"""
        while True:
            try:
                await asyncio.sleep(SessionConfig.CLEANUP_INTERVAL_MINUTES * 60)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in session cleanup task: {e}")
    
    async def close(self):
        """Clean up resources and stop background tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Session service closed")


# Global session service instance
session_service = SessionService()


async def get_session_service() -> SessionService:
    """
    Dependency function to get initialized session service.
    
    Returns:
        SessionService: Initialized session service instance
    """
    if not session_service._initialized:
        await session_service.initialize()
    return session_service