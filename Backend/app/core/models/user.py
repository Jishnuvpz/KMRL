"""
User model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Profile information
    profile_picture = Column(String(500))
    phone = Column(String(20))
    company = Column(String(255))
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    alerts = relationship("Alert", back_populates="user")
    iot_devices = relationship("IoTDevice", back_populates="owner")
    settings = relationship("UserSettings", back_populates="user", uselist=False)