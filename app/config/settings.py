"""
Core application settings with environment-based configuration.
"""
import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """
    Application settings with environment-based configuration.
    Uses Pydantic BaseSettings for automatic environment variable loading.
    """
    
    # Application Settings
    app_name: str = Field(default="The Plugs API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # Database Settings
    database_url: str = Field(..., description="Database connection URL")
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=30, description="Database max overflow connections")
    database_pool_timeout: int = Field(default=30, description="Database pool timeout in seconds")
    database_pool_recycle: int = Field(default=3600, description="Database pool recycle time in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis Settings
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    
    # Security Settings
    secret_key: str = Field(..., description="Secret key for JWT and encryption")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=30, description="JWT access token expiration in minutes")
    jwt_refresh_token_expire_days: int = Field(default=7, description="JWT refresh token expiration in days")
    
    # CORS Settings
    cors_origins: str = Field(default="*", description="CORS allowed origins (comma-separated)")
    cors_credentials: bool = Field(default=True, description="CORS allow credentials")
    cors_methods: str = Field(default="*", description="CORS allowed methods (comma-separated)")
    cors_headers: str = Field(default="*", description="CORS allowed headers (comma-separated)")
    
    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or text")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Email Settings (for notifications)
    smtp_host: Optional[str] = Field(default=None, description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    
    # SendGrid Settings (preferred email provider)
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API key")
    sendgrid_from_email: Optional[str] = Field(default=None, description="SendGrid from email address")
    
    # Frontend URL (for password reset links)
    frontend_url: str = Field(default="http://localhost:3000", description="Frontend application URL")
    
    # Celery Settings (for background tasks)
    celery_broker_url: str = Field(default="redis://redis:6379/1", description="Celery broker URL")
    celery_result_backend: str = Field(default="redis://redis:6379/2", description="Celery result backend URL")
    
    # File Upload Settings
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes (10MB)")
    upload_path: str = Field(default="uploads", description="File upload directory")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if not self.cors_origins or self.cors_origins == "":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def cors_methods_list(self) -> List[str]:
        """Get CORS methods as a list."""
        if not self.cors_methods or self.cors_methods == "":
            return ["*"]
        return [method.strip() for method in self.cors_methods.split(",") if method.strip()]
    
    @property
    def cors_headers_list(self) -> List[str]:
        """Get CORS headers as a list."""
        if not self.cors_headers or self.cors_headers == "":
            return ["*"]
        return [header.strip() for header in self.cors_headers.split(",") if header.strip()]
    
    @validator("environment", pre=True)
    def validate_environment(cls, v):
        """Validate environment value."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable prefixes
        env_prefix = ""
        
        # Allow extra fields for flexibility
        extra = "ignore"


# Global settings instance
settings = Settings()