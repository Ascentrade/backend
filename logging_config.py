"""
Logging configuration for the application.
Provides colorful console logging with datetime, severity, module name, and log text.
"""
import os
import logging
import sys
import re
from datetime import datetime
from typing import Dict, Optional
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform color support
colorama.init(autoreset=True)


class ApiTokenFilter(logging.Filter):
    """
    Filter to mask API tokens in log messages.
    Replaces api_token=... with api_token=xxx in log messages.
    """
    # Pattern to match api_token= followed by token value (until &, space, quote, or end)
    API_TOKEN_PATTERN = re.compile(r'api_token=([^&\s"\'<>]+)', re.IGNORECASE)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize API tokens in log messages."""
        if hasattr(record, 'msg') and record.msg:
            # Convert to string if not already
            msg = str(record.msg)
            # Replace api_token=... with api_token=xxx
            msg = self.API_TOKEN_PATTERN.sub('api_token=xxx', msg)
            record.msg = msg
        
        # Also sanitize args if present
        if hasattr(record, 'args') and record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    arg = self.API_TOKEN_PATTERN.sub('api_token=xxx', arg)
                sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        
        return True


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    # Color mapping for different log levels
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def format(self, record: logging.LogRecord) -> str:
        # Get the color for this log level
        log_color = self.COLORS.get(record.levelname, '')
        reset_color = Style.RESET_ALL
        
        # Format the timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get the module/file name (shortened path)
        module_name = record.name
        if '.' in module_name:
            # Show the last two parts of the module path for better readability
            parts = module_name.split('.')
            if len(parts) > 2:
                module_name = '.'.join(parts[-2:])
        
        # Format the log level with color
        level_name = f"{log_color}{record.levelname:8}{reset_color}"
        
        # Format the message
        message = record.getMessage()
        
        # Sanitize API tokens in the formatted message (extra safety)
        api_token_pattern = re.compile(r'api_token=([^&\s"\'<>]+)', re.IGNORECASE)
        message = api_token_pattern.sub('api_token=xxx', message)
        
        # Build the final log line
        log_line = f"{timestamp} | {level_name} | {module_name:30} | {message}"
        
        # Sanitize API tokens in the final log line as well (catches URLs and other contexts)
        log_line = api_token_pattern.sub('api_token=xxx', log_line)
        
        # Add exception info if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            # Sanitize exception text too
            exc_text = api_token_pattern.sub('api_token=xxx', exc_text)
            log_line += '\n' + exc_text
        
        return log_line


def _level_to_int(level: str) -> int:
    numeric_level = getattr(logging, (level or "").upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level!r}")
    return numeric_level


def _parse_logger_level_overrides(raw: Optional[str]) -> Dict[str, str]:
    """
    Parse comma-separated logger overrides like:
      "uvicorn.access=WARNING,sqlalchemy.engine.Engine=WARNING"
    """
    if not raw:
        return {}

    overrides: Dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(
                f"Invalid LOG_LEVEL_OVERRIDES entry {part!r}. Expected 'logger.name=LEVEL'."
            )
        logger_name, level = part.split("=", 1)
        logger_name = logger_name.strip()
        level = level.strip().upper()
        if not logger_name:
            raise ValueError(
                f"Invalid LOG_LEVEL_OVERRIDES entry {part!r}. Logger name cannot be empty."
            )
        _level_to_int(level)  # validate level
        overrides[logger_name] = level
    return overrides


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up application-wide logging configuration.
    
    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, reads from environment variable LOG_LEVEL, defaults to INFO.
    """
    
    # Get log level from parameter or environment variable, default to INFO
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    numeric_level = _level_to_int(log_level)

    # Per-logger overrides are provided via .env as a single env var like:
    # LOG_LEVEL_OVERRIDES="uvicorn.access=WARNING,sqlalchemy.engine.Engine=WARNING"
    # (LOG_LEVELS is accepted as an alias)
    raw_overrides = os.environ.get("LOG_LEVEL_OVERRIDES") or os.environ.get("LOG_LEVELS")
    env_overrides = _parse_logger_level_overrides(raw_overrides)

    # Defaults (can be overridden via LOG_LEVEL_OVERRIDES in .env)
    default_overrides: Dict[str, str] = {
        # Cut down uvicorn access log spam by default
        "uvicorn.access": "WARNING",
        # Cut down SQLAlchemy statement logging by default
        "sqlalchemy.engine.Engine": "WARNING",
        # Some setups refer to this shorter name; harmless if unused
        "engine.Engine": "WARNING",
    }

    effective_overrides: Dict[str, str] = {**default_overrides, **env_overrides}
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    # Don't filter at the handler level; let logger levels decide.
    console_handler.setLevel(logging.NOTSET)
    
    # Add API token filter to sanitize sensitive information
    api_token_filter = ApiTokenFilter()
    console_handler.addFilter(api_token_filter)
    
    # Set the colored formatter
    formatter = ColoredFormatter()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(console_handler)
    
    # Apply common defaults for noisy subsystems (can be overridden by env)
    logging.getLogger("sqlalchemy.pool").setLevel(_level_to_int(effective_overrides.get("sqlalchemy.pool", "INFO")))
    logging.getLogger("sqlalchemy.dialects").setLevel(_level_to_int(effective_overrides.get("sqlalchemy.dialects", "INFO")))
    
    # Uvicorn loggers
    uvicorn_logger_names = ["uvicorn", "uvicorn.error", "uvicorn.access"]
    for logger_name in uvicorn_logger_names:
        uvicorn_logger = logging.getLogger(logger_name)
        # Clear existing handlers to avoid duplicate logs or default formatting
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = False
        uvicorn_logger.addHandler(console_handler)
        uvicorn_logger.setLevel(_level_to_int(effective_overrides.get(logger_name, log_level)))
    
    # FastAPI logger
    fastapi_logger = logging.getLogger('fastapi')
    fastapi_logger.setLevel(_level_to_int(effective_overrides.get("fastapi", log_level)))
    fastapi_logger.handlers = []
    fastapi_logger.propagate = False
    fastapi_logger.addHandler(console_handler)

    # Finally apply any remaining overrides (including the two defaults requested)
    for logger_name, level_str in effective_overrides.items():
        logging.getLogger(logger_name).setLevel(_level_to_int(level_str))
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
