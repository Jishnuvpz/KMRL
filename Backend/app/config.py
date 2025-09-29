"""
Configuration settings for Document Management System
Professional configuration management with validation and environment handling
"""
import os
import logging
from typing import List, Optional, Dict, Any
from pydantic import Field, validator, root_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Application settings with comprehensive configuration management
    Supports development, staging, and production environments
    """
    
    # Environment settings
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Application settings
    PROJECT_NAME: str = Field(default="Document Management System", env="PROJECT_NAME")
    PROJECT_VERSION: str = Field(default="2.0.0", env="PROJECT_VERSION")
    API_V1_STR: str = Field(default="/api", env="API_V1_STR")
    
    # Database settings
    DATABASE_URL: str = Field(default="sqlite:///./app.db", env="DATABASE_URL")
    
    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")  # Required
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS settings
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5000,http://127.0.0.1:5000,file://", 
        env="ALLOWED_ORIGINS"
    )
    
    @property
    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # Email settings
    SMTP_SERVER: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str = Field(default="", env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    
    # Email data fetching settings
    EMAIL_DATA_SOURCE: str = Field(default="zodiacmrv@gmail.com", env="EMAIL_DATA_SOURCE")
    EMAIL_FETCH_INTERVAL: int = Field(default=300, env="EMAIL_FETCH_INTERVAL")  # 5 minutes
    EMAIL_FOLDER: str = Field(default="INBOX", env="EMAIL_FOLDER")
    EMAIL_MAX_FETCH: int = Field(default=50, env="EMAIL_MAX_FETCH")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    UPLOAD_DIRECTORY: str = Field(default="uploads", env="UPLOAD_DIRECTORY")
    ALLOWED_FILE_TYPES: str = Field(
        default="pdf,doc,docx,txt,jpg,jpeg,png,tiff,bmp,gif", 
        env="ALLOWED_FILE_TYPES"
    )
    
    @property
    def get_allowed_file_types(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_FILE_TYPES.split(",")]
    
    # OCR settings
    TESSERACT_PATH: str = Field(default="tesseract", env="TESSERACT_PATH")
    OCR_LANGUAGES: str = Field(default="eng,mal", env="OCR_LANGUAGES")  # English and Malayalam
    TESSERACT_CONFIG: str = Field(default="--oem 1 --psm 6", env="TESSERACT_CONFIG")
    
    @property
    def get_ocr_languages(self) -> List[str]:
        return [lang.strip() for lang in self.OCR_LANGUAGES.split(",")]
    
    # Google Cloud Vision API settings - REMOVED
    # GOOGLE_CLOUD_PROJECT_ID: str = Field(default="", env="GOOGLE_CLOUD_PROJECT_ID")
    # GOOGLE_APPLICATION_CREDENTIALS: str = Field(default="", env="GOOGLE_APPLICATION_CREDENTIALS")
    # GOOGLE_VISION_API_ENABLED: bool = Field(default=False, env="GOOGLE_VISION_API_ENABLED")
    # GOOGLE_VISION_MAX_RESULTS: int = Field(default=50, env="GOOGLE_VISION_MAX_RESULTS")
    # GOOGLE_VISION_LANGUAGE_HINTS: str = Field(default="en,ml", env="GOOGLE_VISION_LANGUAGE_HINTS")
    # AI Summarization settings
    HUGGINGFACE_API_KEY: str = Field(default="", env="HUGGINGFACE_API_KEY")
    ENGLISH_SUMMARIZATION_MODEL: str = Field(
        default="facebook/bart-large-cnn", 
        env="ENGLISH_SUMMARIZATION_MODEL"
    )
    MALAYALAM_SUMMARIZATION_MODEL: str = Field(
        default="ai4bharat/IndicBART", 
        env="MALAYALAM_SUMMARIZATION_MODEL"
    )
    SUMMARIZATION_MAX_LENGTH: int = Field(default=150, env="SUMMARIZATION_MAX_LENGTH")
    SUMMARIZATION_MIN_LENGTH: int = Field(default=30, env="SUMMARIZATION_MIN_LENGTH")
    
    # Supabase settings removed
    
    # AWS S3 settings
    AWS_ACCESS_KEY_ID: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_S3_BUCKET_NAME: str = Field(default="", env="AWS_S3_BUCKET_NAME")
    AWS_S3_CUSTOM_DOMAIN: str = Field(default="", env="AWS_S3_CUSTOM_DOMAIN")
    AWS_S3_USE_SSL: bool = Field(default=True, env="AWS_S3_USE_SSL")
    
    # MongoDB Atlas settings
    MONGODB_URL: str = Field(default="", env="MONGODB_URL")
    MONGODB_DATABASE_NAME: str = Field(default="document_management", env="MONGODB_DATABASE_NAME")
    MONGODB_COLLECTION_DOCUMENTS: str = Field(default="documents", env="MONGODB_COLLECTION_DOCUMENTS")
    MONGODB_COLLECTION_ANALYTICS: str = Field(default="analytics", env="MONGODB_COLLECTION_ANALYTICS")
    MONGODB_COLLECTION_LOGS: str = Field(default="logs", env="MONGODB_COLLECTION_LOGS")
    
    # Cloud storage settings
    USE_S3_STORAGE: bool = Field(default=True, env="USE_S3_STORAGE")
    S3_UPLOAD_FOLDER: str = Field(default="uploads", env="S3_UPLOAD_FOLDER")
    S3_PROCESSED_FOLDER: str = Field(default="processed", env="S3_PROCESSED_FOLDER")
    S3_BACKUP_FOLDER: str = Field(default="backups", env="S3_BACKUP_FOLDER")
    
    # AWS S3 Raw Data Storage settings
    S3_RAW_DATA_FOLDER: str = Field(default="raw-data", env="S3_RAW_DATA_FOLDER")
    S3_EMAIL_DATA_FOLDER: str = Field(default="raw-data/emails", env="S3_EMAIL_DATA_FOLDER")
    S3_DOCUMENT_DATA_FOLDER: str = Field(default="raw-data/documents", env="S3_DOCUMENT_DATA_FOLDER")
    S3_IOT_DATA_FOLDER: str = Field(default="raw-data/iot", env="S3_IOT_DATA_FOLDER")
    S3_ANALYTICS_DATA_FOLDER: str = Field(default="raw-data/analytics", env="S3_ANALYTICS_DATA_FOLDER")
    S3_RAW_DATA_RETENTION_DAYS: int = Field(default=365, env="S3_RAW_DATA_RETENTION_DAYS")
    S3_RAW_DATA_STORAGE_CLASS: str = Field(default="STANDARD_IA", env="S3_RAW_DATA_STORAGE_CLASS")
    
    # IoT settings (optional)
    IOT_MQTT_BROKER: str = Field(default="localhost", env="IOT_MQTT_BROKER")
    IOT_MQTT_PORT: int = Field(default=1883, env="IOT_MQTT_PORT")
    IOT_MQTT_USERNAME: str = Field(default="", env="IOT_MQTT_USERNAME")
    IOT_MQTT_PASSWORD: str = Field(default="", env="IOT_MQTT_PASSWORD")
    
    # Redis settings (for caching)
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="app.log", env="LOG_FILE")
    LOG_MAX_SIZE: int = Field(default=10485760, env="LOG_MAX_SIZE")  # 10MB
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Performance settings
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    MAX_REQUESTS_PER_MINUTE: int = Field(default=100, env="MAX_REQUESTS_PER_MINUTE")
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @root_validator(skip_on_failure=True)
    def validate_aws_settings(cls, values):
        """Validate AWS S3 configuration"""
        use_s3 = values.get("USE_S3_STORAGE", False)
        if use_s3:
            required_fields = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_S3_BUCKET_NAME"]
            missing_fields = [field for field in required_fields if not values.get(field)]
            
            if missing_fields:
                logger.warning(f"S3 storage enabled but missing: {', '.join(missing_fields)}")
        
        return values
    
    # Google Vision validation method removed
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == "development"
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL for the environment"""
        return self.DATABASE_URL
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service configuration information"""
        return {
            "project_name": self.PROJECT_NAME,
            "version": self.PROJECT_VERSION,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "services": {
                "aws_s3": bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY),
                # "google_vision": removed,
                # "supabase": bool(self.SUPABASE_URL and self.SUPABASE_KEY),
                "mongodb": bool(self.MONGODB_URL),
                "redis": self.REDIS_ENABLED,
                "email": bool(self.SMTP_USERNAME and self.SMTP_PASSWORD)
            }
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"

# Create settings instance
try:
    settings = Settings()
    logger.info(f"Configuration loaded successfully for {settings.ENVIRONMENT} environment")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    # Create minimal settings for development
    os.environ.setdefault("SECRET_KEY", "development-secret-key-change-in-production-please")
    settings = Settings()
    logger.warning("Using fallback configuration")