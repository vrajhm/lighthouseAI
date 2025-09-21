"""Structured logging configuration for Lighthouse.ai"""

import logging
import re
import sys
from typing import Any, Dict, Optional
import structlog
from structlog.stdlib import LoggerFactory

from lighthouse.config.settings import get_settings


class PIIRedactor:
    """Redacts personally identifiable information from log messages"""
    
    # Common PII patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
    PASSWORD_PATTERN = re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+', re.IGNORECASE)
    
    @classmethod
    def redact(cls, message: str) -> str:
        """Redact PII from a log message"""
        if not message:
            return message
            
        # Redact email addresses
        message = cls.EMAIL_PATTERN.sub('[EMAIL_REDACTED]', message)
        
        # Redact phone numbers
        message = cls.PHONE_PATTERN.sub('[PHONE_REDACTED]', message)
        
        # Redact SSNs
        message = cls.SSN_PATTERN.sub('[SSN_REDACTED]', message)
        
        # Redact credit card numbers
        message = cls.CREDIT_CARD_PATTERN.sub('[CARD_REDACTED]', message)
        
        # Redact passwords
        message = cls.PASSWORD_PATTERN.sub(r'\1=[PASSWORD_REDACTED]', message)
        
        return message


def setup_logging() -> None:
    """Setup structured logging with PII redaction"""
    settings = get_settings()
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Custom PII redaction processor
            lambda logger, method_name, event_dict: {
                **event_dict,
                'event': PIIRedactor.redact(str(event_dict.get('event', '')))
            },
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Set specific logger levels
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("TTS").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for this class"""
        return get_logger(self.__class__.__name__)


def log_function_call(func_name: str, **kwargs) -> None:
    """Log a function call with parameters (PII redacted)"""
    logger = get_logger("function_calls")
    logger.info(f"Calling {func_name}", **kwargs)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an error with context"""
    logger = get_logger("errors")
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True
    )


def log_performance(operation: str, duration: float, **kwargs) -> None:
    """Log performance metrics"""
    logger = get_logger("performance")
    logger.info(
        f"Performance: {operation}",
        duration_ms=duration * 1000,
        **kwargs
    )


# Initialize logging when module is imported
setup_logging()
