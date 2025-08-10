"""
Configuration management
"""

import os
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8001, env="API_PORT")
    debug: bool = Field(False, env="DEBUG")
    
    # Ollama Settings
    ollama_host: str = Field("http://localhost:11434", env="OLLAMA_HOST")
    ollama_timeout: int = Field(300, env="OLLAMA_TIMEOUT")
    default_model: str = Field("gpt-oss:20b", env="DEFAULT_MODEL")
    
    # Security Settings
    secret_key: Optional[str] = Field(None, env="SECRET_KEY")
    admin_password: Optional[str] = Field(None, env="ADMIN_PASSWORD")
    enable_authentication: bool = Field(False, env="ENABLE_AUTH")
    rate_limit_per_minute: int = Field(20, env="RATE_LIMIT_PER_MINUTE")
    
    # Browser Settings
    browser_type: str = Field("playwright", env="BROWSER_TYPE")  # or "selenium"
    browser_headless: bool = Field(True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(30, env="BROWSER_TIMEOUT")
    
    # File System Settings
    upload_directory: str = Field("uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    allowed_file_types: str = Field("txt,pdf,doc,docx,json,csv,py,js,html,css", env="ALLOWED_FILE_TYPES")
    
    # System Settings
    enable_pc_control: bool = Field(True, env="ENABLE_PC_CONTROL")
    enable_web_browsing: bool = Field(True, env="ENABLE_WEB_BROWSING")
    max_command_timeout: int = Field(300, env="MAX_COMMAND_TIMEOUT")
    
    # Logging Settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field("ai_control.log", env="LOG_FILE")
    log_rotation: str = Field("10 MB", env="LOG_ROTATION")
    log_retention: str = Field("30 days", env="LOG_RETENTION")
    
    # Network Settings
    cors_origins: str = Field("*", env="CORS_ORIGINS")
    trust_proxy_headers: bool = Field(True, env="TRUST_PROXY_HEADERS")
    
    # Performance Settings
    worker_threads: int = Field(4, env="WORKER_THREADS")
    memory_limit_mb: int = Field(2048, env="MEMORY_LIMIT_MB")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"
    browser_headless: bool = False
    enable_authentication: bool = False


class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    log_level: str = "INFO"
    browser_headless: bool = True
    enable_authentication: bool = True
    cors_origins: str = "https://yourdomain.com"


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "development":
        return DevelopmentSettings()
    else:
        return Settings()


def create_directories(settings: Settings):
    """Create necessary directories"""
    try:
        # Create upload directory
        upload_dir = Path(settings.upload_directory)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        if settings.log_file:
            log_dir = Path(settings.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temp directory for browser downloads
        temp_dir = Path("temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
    except Exception as e:
        print(f"Warning: Could not create directories: {e}")


def validate_settings(settings: Settings) -> bool:
    """Validate settings configuration"""
    try:
        # Check required directories exist or can be created
        create_directories(settings)
        
        # Validate file size limits
        if settings.max_file_size <= 0:
            raise ValueError("max_file_size must be positive")
        
        # Validate timeouts
        if settings.ollama_timeout <= 0:
            raise ValueError("ollama_timeout must be positive")
        
        if settings.browser_timeout <= 0:
            raise ValueError("browser_timeout must be positive")
        
        # Validate rate limits
        if settings.rate_limit_per_minute <= 0:
            raise ValueError("rate_limit_per_minute must be positive")
        
        return True
        
    except Exception as e:
        print(f"Settings validation failed: {e}")
        return False


def get_env_info() -> Dict[str, Any]:
    """Get environment information"""
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": os.sys.version,
        "platform": os.name,
        "cwd": os.getcwd(),
        "user": os.getenv("USER", os.getenv("USERNAME", "unknown")),
        "home": str(Path.home()),
        "env_vars": {
            key: value for key, value in os.environ.items()
            if key.startswith(('API_', 'OLLAMA_', 'BROWSER_', 'ENABLE_'))
        }
    }


# Global settings instance
settings = get_settings()

# Validate settings on import
if not validate_settings(settings):
    print("Warning: Settings validation failed. Some features may not work correctly.")

# Create directories
create_directories(settings)
