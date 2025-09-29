"""
Alert and notification models for KMRL Document Management System
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class AlertType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    IOT = "iot"
    DOCUMENT = "document"
    SYSTEM = "system"


class AlertPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Alert content
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)

    # Alert classification
    alert_type = Column(Enum(AlertType), default=AlertType.INFO)
    priority = Column(Enum(AlertPriority), default=AlertPriority.MEDIUM)
    source = Column(String(100))  # system, iot, document, user

    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))
    dismissed_at = Column(DateTime(timezone=True))

    # Additional data
    alert_metadata = Column(String(1000))  # JSON string for additional context
    action_url = Column(String(500))  # URL for action button

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="alerts")

    # Related entities (optional)
    document_id = Column(Integer, ForeignKey("documents.id"))
    document = relationship("Document", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', title='{self.title}')>"


class SystemNotification(Base):
    __tablename__ = "system_notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Notification content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    # announcement, maintenance, update, alert
    notification_type = Column(String(50), nullable=False)

    # Targeting
    # all, staff, managers, directors, admins
    target_audience = Column(String(50))
    departments = Column(JSON)  # List of department names

    # Display settings
    is_banner = Column(Boolean, default=False)  # Show as banner on top
    is_popup = Column(Boolean, default=False)  # Show as popup
    is_persistent = Column(Boolean, default=False)  # Don't auto-dismiss

    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    expires_at = Column(DateTime)

    def __repr__(self):
        return f"<SystemNotification(id={self.id}, type='{self.notification_type}', title='{self.title}')>"


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)

    # Rule definition
    name = Column(String(255), nullable=False)
    description = Column(Text)
    # document_upload, failed_processing, quota_exceeded
    rule_type = Column(String(50), nullable=False)

    # Conditions
    conditions = Column(JSON, nullable=False)  # Rule conditions as JSON
    threshold_value = Column(Float)
    threshold_operator = Column(String(10))  # gt, lt, eq, gte, lte

    # Actions
    alert_template = Column(JSON)  # Alert template to create
    notification_channels = Column(JSON)  # email, sms, webhook

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AlertRule(id={self.id}, name='{self.name}', type='{self.rule_type}')>"
