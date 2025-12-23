"""
Structured JSON Logging with Contextual Information
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from mongodb.api.config.settings import settings
import traceback


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add source location
        log_record['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }
        
        # Add application info
        log_record['app'] = {
            'name': settings.app_name,
            'version': settings.app_version,
            'environment': settings.environment
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Remove default fields that we've replaced
        if 'message' in log_record:
            log_record['msg'] = log_record.pop('message')


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""
    
    _context: Dict[str, Any] = {}
    
    @classmethod
    def set_context(cls, **kwargs):
        """Set context for current request"""
        cls._context.update(kwargs)
    
    @classmethod
    def clear_context(cls):
        """Clear request context"""
        cls._context = {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in self._context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    level: str = None,
    log_format: str = None,
    log_file: str = None
) -> logging.Logger:
    """
    Setup structured logging for the application
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 'json' or 'text'
        log_file: Optional file path for logging
    """
    level = level or settings.log_level
    log_format = log_format or settings.log_format
    log_file = log_file or settings.log_file
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Create formatter based on format type
    if log_format == 'json':
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding context to logs"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.previous_context = {}
    
    def __enter__(self):
        self.previous_context = RequestContextFilter._context.copy()
        RequestContextFilter.set_context(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        RequestContextFilter._context = self.previous_context
        return False


# ========================================
# Logging Utilities
# ========================================

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    **extra
):
    """Log HTTP request with structured data"""
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            'http': {
                'method': method,
                'path': path,
                'status_code': status_code,
                'duration_ms': round(duration_ms, 2)
            },
            'user_id': user_id,
            **extra
        }
    )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    collection: str,
    duration_ms: float,
    document_count: int = 0,
    **extra
):
    """Log database operation with structured data"""
    logger.debug(
        f"DB {operation} on {collection}",
        extra={
            'database': {
                'operation': operation,
                'collection': collection,
                'duration_ms': round(duration_ms, 2),
                'document_count': document_count
            },
            **extra
        }
    )


def log_crawl_event(
    logger: logging.Logger,
    source: str,
    articles_found: int,
    articles_new: int,
    duration_seconds: float,
    success: bool,
    error: Optional[str] = None
):
    """Log crawler event with structured data"""
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"Crawled {source}: {articles_new} new / {articles_found} total",
        extra={
            'crawler': {
                'source': source,
                'articles_found': articles_found,
                'articles_new': articles_new,
                'duration_seconds': round(duration_seconds, 2),
                'success': success,
                'error': error
            }
        }
    )


# Legacy compatibility functions
def log_error(error):
    """Log error (legacy compatibility)"""
    logger = logging.getLogger("DisasterMonitor")
    logger.error(f"Error: {error}")


def log_event(event):
    """Log event (legacy compatibility)"""
    logger = logging.getLogger("DisasterMonitor")
    logger.info(f"Event: {event}")


# Initialize logging on module import
logger = setup_logging()