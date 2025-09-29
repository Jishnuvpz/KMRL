"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db import get_db
from app.utils.jwt import create_access_token, verify_token
from app.core.models.user import User
from app.core.services.auth_service import AuthService

router = APIRouter()
security = HTTPBearer()

@router.post("/login")
async def login(credentials: dict, db: Session = Depends(get_db)):
    """
    User login endpoint
    """
    try:
        auth_service = AuthService(db)
        user = auth_service.authenticate_user(
            credentials.get("email"),
            credentials.get("password")
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/register")
async def register(user_data: dict, db: Session = Depends(get_db)):
    """
    User registration endpoint
    """
    try:
        auth_service = AuthService(db)
        user = auth_service.create_user(
            email=user_data.get("email"),
            password=user_data.get("password"),
            name=user_data.get("name")
        )
        
        return {
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/logout")
async def logout(token: str = Depends(security)):
    """
    User logout endpoint
    """
    # In a real implementation, you might want to blacklist the token
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)):
    """
    Get current user information
    """
    try:
        payload = verify_token(token.credentials)
        email = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )