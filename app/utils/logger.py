"""
Logging configuration
"""

import sys
import logging
from pathlib import Path
from loguru import logger
from app.utils.config import get_settings


def setup_logging():
    """Setup loguru logging configuration"""
    try:
        settings = get_settings()
        
        # Remove default handler
        logger.remove()
        
        # Console handler
        logger.add(
            sys.stderr,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # File handler (if specified)
        if settings.log_file:
            log_path = Path(settings.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                str(log_path),
                level=settings.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                rotation=settings.log_rotation,
                retention=settings.log_retention,
                compression="zip"
            )
        
        # Suppress some noisy loggers
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("playwright").setLevel(logging.WARNING)
        logging.getLogger("selenium").setLevel(logging.WARNING)
        
        logger.info("🚀 Logging configured successfully")
        
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        # Fallback to basic logging
        logger.add(sys.stderr, level="INFO")


def get_logger(name: str):
    """Get a logger with the specified name"""
    return logger.bind(name=name)


# Performance logging helpers
def log_performance(func_name: str, duration: float, details: str = ""):
    """Log performance metrics"""
    logger.info(f"⏱️ {func_name} took {duration:.2f}s {details}")


def log_error_with_context(error: Exception, context: str = ""):
    """Log error with additional context"""
    logger.error(f"❌ Error {context}: {type(error).__name__}: {str(error)}")


def log_security_event(event_type: str, details: str, severity: str = "info"):
    """Log security events"""
    if severity == "critical":
        logger.critical(f"🚨 SECURITY [{event_type}]: {details}")
    elif severity == "warning":
        logger.warning(f"⚠️ SECURITY [{event_type}]: {details}")
    else:
        logger.info(f"🔒 SECURITY [{event_type}]: {details}")


def log_user_action(action: str, user: str = "unknown", details: str = ""):
    """Log user actions for audit trail"""
    logger.info(f"👤 USER [{user}] {action} {details}")


def log_api_request(method: str, path: str, status_code: int, duration: float):
    """Log API requests"""
    if status_code >= 400:
        logger.warning(f"🌐 {method} {path} -> {status_code} ({duration:.2f}s)")
    else:
        logger.info(f"🌐 {method} {path} -> {status_code} ({duration:.2f}s)")


def log_system_resource(resource_type: str, usage: float, threshold: float = 80.0):
    """Log system resource usage"""
    if usage > threshold:
        logger.warning(f"⚠️ High {resource_type} usage: {usage:.1f}%")
    else:
        logger.debug(f"📊 {resource_type} usage: {usage:.1f}%")
