"""
Logging configuration for Anki Animal Ranch.

Sets up logging to both console and a rotating log file.
The log file is stored in the same location as save files (Anki profile folder).
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file settings
LOG_FILENAME = "anki_animal_ranch.log"
MAX_LOG_SIZE_BYTES = 100 * 1024  # 100 KB (~1000-2000 lines)
BACKUP_COUNT = 1  # Keep 1 backup file

# Global state
_file_handler: Optional[RotatingFileHandler] = None
_console_configured = False
_file_handler_initialized = False


def _get_anki_profile_folder() -> Optional[Path]:
    """
    Try to get the Anki profile folder.
    
    Returns:
        Path to Anki profile folder, or None if not available
    """
    try:
        from aqt import mw
        if mw and mw.pm and mw.pm.profileFolder():
            return Path(mw.pm.profileFolder())
    except ImportError:
        pass
    except Exception:
        pass
    return None


def _get_fallback_folder() -> Path:
    """Get the fallback folder for logs when Anki isn't available."""
    data_dir = Path.home() / ".anki_animal_ranch"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def setup_file_logging() -> Optional[Path]:
    """
    Set up file logging to the Anki profile folder.
    
    This should be called when the game window opens, at which point
    Anki is fully initialized and the profile folder is available.
    
    Returns:
        Path to log file, or None if setup failed
    """
    global _file_handler, _file_handler_initialized
    
    if _file_handler_initialized:
        return get_log_file_path()
    
    logger = logging.getLogger("anki_animal_ranch")
    
    # Remove any existing file handlers
    for handler in logger.handlers[:]:
        if isinstance(handler, RotatingFileHandler):
            logger.removeHandler(handler)
            handler.close()
    
    # Try to get Anki profile folder first, fall back to home directory
    log_dir = _get_anki_profile_folder()
    if log_dir is None:
        log_dir = _get_fallback_folder()
    
    try:
        log_path = log_dir / LOG_FILENAME
        
        _file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        _file_handler.setLevel(logging.DEBUG)
        _file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(_file_handler)
        
        _file_handler_initialized = True
        logger.info(f"Log file: {log_path}")
        
        return log_path
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")
        return None


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure console logging for the application.
    
    File logging is set up separately via setup_file_logging() when
    the game window opens.
    
    Args:
        level: Default log level
        
    Returns:
        The root logger for the application
    """
    global _console_configured
    
    logger = logging.getLogger("anki_animal_ranch")
    logger.setLevel(logging.DEBUG)
    
    # Only set up console handler once
    if not _console_configured:
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(console_handler)
        
        logger.propagate = False
        _console_configured = True
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance
    """
    # Ensure console is configured
    setup_logging()
    
    # Return appropriate logger
    if name.startswith("anki_animal_ranch"):
        return logging.getLogger(name)
    else:
        return logging.getLogger(f"anki_animal_ranch.{name}")


def get_log_file_path() -> Path | None:
    """
    Get the path to the current log file.
    
    Returns:
        Path to log file, or None if file logging isn't set up
    """
    if not _file_handler_initialized:
        return None
    
    # Return the path based on where we'd create it
    log_dir = _get_anki_profile_folder()
    if log_dir is None:
        log_dir = _get_fallback_folder()
    
    log_path = log_dir / LOG_FILENAME
    if log_path.exists():
        return log_path
    return None


def get_recent_logs(lines: int = 100) -> str:
    """
    Get the most recent log entries.
    
    Useful for including in crash reports.
    
    Args:
        lines: Number of lines to retrieve
        
    Returns:
        String containing recent log entries
    """
    log_path = get_log_file_path()
    if log_path is None or not log_path.exists():
        return "No log file found"
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return "".join(recent)
    except Exception as e:
        return f"Error reading log file: {e}"
