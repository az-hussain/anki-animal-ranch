"""
Data persistence and storage.

Handles:
- Local save/load (JSON)
- Account management
- Friends list
"""

from .save_manager import SaveManager, get_save_manager
from .account_manager import AccountManager, get_account_manager

__all__ = [
    "SaveManager",
    "get_save_manager",
    "AccountManager",
    "get_account_manager",
]
