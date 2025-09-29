"""
Enhanced Authentication Service
==============================

Comprehensive authentication service with JWT token management and session integration.
Handles user authentication, token creation/validation, and password management.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.user import User

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def create_access_token(data: Dict[str, Any], expires_delta_hours: Optional[int] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Token payload data
        expires_delta_hours: Token expiration time in hours
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta_hours:
        expire = datetime.utcnow() + timedelta(hours=expires_delta_hours)
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Dict[str, Any]: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Dict[str, Any]: Current user information
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no user information"
            )
        
        return {
            "user_id": user_id,
            "session_id": payload.get("session_id"),
            "token_type": payload.get("type", "access")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


class AuthService:
    """Enhanced authentication service with session management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User: Authenticated user or None if authentication fails
        """
        try:
            # First try to find user in database
            user = self.db.query(User).filter(User.email == email).first()
            
            if user and self.verify_password(password, user.hashed_password):
                logger.info(f"User authenticated successfully from database: {email}")
                return user
            
            # Demo mode: Allow hardcoded demo credentials
            if email == "admin@kmrl.co.in" and password == "password123":
                # Create a demo user object (not persisted to database)
                demo_user = User()
                demo_user.id = 1
                demo_user.email = "admin@kmrl.co.in"
                demo_user.name = "Demo Admin"
                demo_user.is_active = True
                demo_user.is_admin = True
                demo_user.hashed_password = self.get_password_hash("password123")
                
                logger.info(f"Demo user authenticated: {email}")
                return demo_user
                
            logger.warning(f"Authentication failed for email: {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error during authentication for {email}: {e}")
            return None
    
    def create_user(self, email: str, password: str, name: str, role: str = "Staff") -> User:
        """
        Create a new user.
        
        Args:
            email: User email
            password: Plain text password
            name: User full name
            role: User role (default: Staff)
            
        Returns:
            User: Created user object
            
        Raises:
            ValueError: If user already exists
        """
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User with this email already exists")
            
            hashed_password = self.get_password_hash(password)
            user = User(
                email=email,
                hashed_password=hashed_password,
                name=name,
                role=role
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User created successfully: {email}")
            return user
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            self.db.rollback()
            raise
    
    def validate_user_credentials(self, credentials: Dict[str, Any]) -> Optional[str]:
        """
        Validate user credentials and return user ID.
        
        Args:
            credentials: Login credentials dictionary
            
        Returns:
            str: User ID if valid, None otherwise
        """
        try:
            email = credentials.get("username") or credentials.get("email")
            password = credentials.get("password")
            
            if not email or not password:
                return None
            
            # For demo purposes, we'll use a simple mock validation
            # In production, this would query the database
            mock_users = {
                "admin@kmrl.co.in": "password123",
                "board@kmrl.co.in": "password123",
                "director.ops@kmrl.co.in": "password123",
                "director.hr@kmrl.co.in": "password123",
                "manager.fin@kmrl.co.in": "password123",
                "staff.safety@kmrl.co.in": "password123",
                "staff.legal@kmrl.co.in": "password123"
            }
            
            if email in mock_users and mock_users[email] == password:
                return email
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating credentials: {e}")
            return None