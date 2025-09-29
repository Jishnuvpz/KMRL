"""
User model for KMRL Document Management System
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext

from app.db import Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))

    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Role and department
    # staff, manager, director, admin
    role = Column(String(50), default="staff")
    department = Column(String(100))
    position = Column(String(100))

    # Permissions
    permissions = Column(JSON)  # List of permission strings
    can_access_all_departments = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    can_configure_system = Column(Boolean, default=False)

    # Profile
    phone = Column(String(20))
    office_location = Column(String(100))
    reporting_manager = Column(String(255))

    # Session and security
    last_login = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="user")
    document_shares = relationship("DocumentShare", back_populates="shared_by")
    comments = relationship("DocumentComment", back_populates="user")
    activities = relationship("DocumentActivity", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")

    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str):
        """Set password hash"""
        self.hashed_password = pwd_context.hash(password)
        self.password_changed_at = datetime.utcnow()

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if not self.permissions:
            return False
        return permission in self.permissions

    def can_access_department(self, department: str) -> bool:
        """Check if user can access specific department"""
        if self.can_access_all_departments:
            return True
        return self.department == department

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "role": self.role,
            "department": self.department,
            "position": self.position,
            "phone": self.phone,
            "office_location": self.office_location,
            "reporting_manager": self.reporting_manager,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_sensitive:
            data.update({
                "permissions": self.permissions,
                "can_access_all_departments": self.can_access_all_departments,
                "can_manage_users": self.can_manage_users,
                "can_configure_system": self.can_configure_system,
                "failed_login_attempts": self.failed_login_attempts,
                "locked_until": self.locked_until.isoformat() if self.locked_until else None
            })

        return data
