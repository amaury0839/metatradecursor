"""Structured logging setup"""

import logging
import sys
from pathlib import Path
from typing import Optional
import structlog

# Lazy import to avoid circular dependency
_config = None

def get_config_safe():
    """Get config with fallback for cloud deployment"""
    global _config
    if _config is not None:
        return _config
    
    try:
        from app.core.config import get_config
        _config = get_config()
        return _config
    except Exception as e:
        # Return a fallback config for cloud deployment
        class FallbackConfig:
            class logging:
                log_level = "INFO"
                log_file = "/tmp/trading_bot.log"  # Cloud-safe log path
        
        _config = FallbackConfig()
        return _config


def setup_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Setup structured logger with file and console handlers
    
    Args:
        name: Logger name (default: 'trading_bot')
    
    Returns:
        Configured structlog logger
    """
    try:
        config = get_config_safe()
        
        # Create logs directory if needed
        log_file_path = Path(config.logging.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure standard logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, config.logging.log_level.upper(), logging.INFO),
        )
        
        # Add file handler
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer() if config.logging.log_level == "DEBUG" 
                else structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, config.logging.log_level.upper(), logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    except Exception as e:
        # Fallback for cloud deployment
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
        )
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    logger_name = name or "trading_bot"
    return structlog.get_logger(logger_name)
