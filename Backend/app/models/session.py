"""
Session management models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

Base = declarative_base()


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Session details
    device_info = Column(JSON)  # Browser, OS, device details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    location = Column(JSON)  # Geolocation if available

    # Security
    is_active = Column(Boolean, default=True)
    is_trusted_device = Column(Boolean, default=False)
    requires_2fa = Column(Boolean, default=False)

    # Activity tracking
    last_activity = Column(DateTime, default=datetime.utcnow)
    activity_count = Column(Integer, default=0)

    # Session management
    expires_at = Column(DateTime)
    auto_extend = Column(Boolean, default=True)
    max_inactive_minutes = Column(Integer, default=480)  # 8 hours

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    terminated_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="sessions")
    activities = relationship("SessionActivity", back_populates="session")

    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.expires_at = datetime.utcnow() + timedelta(hours=8)

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at

    def is_inactive(self) -> bool:
        """Check if session is inactive"""
        if not self.last_activity:
            return True

        inactive_time = datetime.utcnow() - self.last_activity
        return inactive_time.total_seconds() > (self.max_inactive_minutes * 60)

    def extend_session(self, hours: int = 8):
        """Extend session expiry"""
        if self.auto_extend:
            self.expires_at = datetime.utcnow() + timedelta(hours=hours)
            self.last_activity = datetime.utcnow()

    def terminate(self):
        """Terminate the session"""
        self.is_active = False
        self.terminated_at = datetime.utcnow()

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "device_info": self.device_info,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "location": self.location,
            "is_active": self.is_active,
            "is_trusted_device": self.is_trusted_device,
            "requires_2fa": self.requires_2fa,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "activity_count": self.activity_count,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "auto_extend": self.auto_extend,
            "max_inactive_minutes": self.max_inactive_minutes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "terminated_at": self.terminated_at.isoformat() if self.terminated_at else None
        }


class SessionActivity(Base):
    __tablename__ = "session_activities"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey(
        "user_sessions.id"), nullable=False)

    # Activity details
    # login, logout, api_call, page_view, upload, download
    activity_type = Column(String(50), nullable=False)
    endpoint = Column(String(255))
    method = Column(String(10))  # GET, POST, PUT, DELETE

    # Request details
    request_data = Column(JSON)
    response_status = Column(Integer)
    response_time_ms = Column(Integer)

    # Context
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("UserSession", back_populates="activities")

    def __repr__(self):
        return f"<SessionActivity(id={self.id}, type='{self.activity_type}', session_id={self.session_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "activity_type": self.activity_type,
            "endpoint": self.endpoint,
            "method": self.method,
            "request_data": self.request_data,
            "response_status": self.response_status,
            "response_time_ms": self.response_time_ms,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Setting identification
    # security, session, email, storage
    category = Column(String(100), nullable=False)
    key = Column(String(255), nullable=False)

    # Setting value
    value = Column(Text)  # JSON string or plain text
    # string, integer, boolean, json
    value_type = Column(String(20), default="string")

    # Metadata
    description = Column(Text)
    # System setting vs user configurable
    is_system = Column(Boolean, default=False)
    requires_restart = Column(Boolean, default=False)

    # Validation
    validation_rules = Column(JSON)  # Validation rules for the setting

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Create unique constraint
    __table_args__ = (
        {"schema": None},
    )

    def get_typed_value(self):
        """Get value with proper type conversion"""
        if self.value_type == "integer":
            return int(self.value) if self.value else 0
        elif self.value_type == "boolean":
            return self.value.lower() in ['true', '1', 'yes'] if self.value else False
        elif self.value_type == "json":
            import json
            return json.loads(self.value) if self.value else {}
        else:
            return self.value

    def set_typed_value(self, value):
        """Set value with proper type conversion"""
        if self.value_type == "json":
            import json
            self.value = json.dumps(value)
        else:
            self.value = str(value)

    def __repr__(self):
        return f"<SystemSettings(category='{self.category}', key='{self.key}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "key": self.key,
            "value": self.get_typed_value(),
            "value_type": self.value_type,
            "description": self.description,
            "is_system": self.is_system,
            "requires_restart": self.requires_restart,
            "validation_rules": self.validation_rules,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
