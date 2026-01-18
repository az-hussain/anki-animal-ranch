"""
Account manager for Anki Animal Ranch.

Handles local account data (account.json) and friends list (friends_list.json).
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Account file names
ACCOUNT_FILENAME = "account.json"
FRIENDS_FILENAME = "friends_list.json"

# Username validation
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20
USERNAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


@dataclass
class Account:
    """User account data."""
    username: str
    pkey: str  # Secret UUID for authentication
    
    def to_dict(self) -> dict:
        return {"username": self.username, "pkey": self.pkey}
    
    @classmethod
    def from_dict(cls, data: dict) -> Account:
        return cls(username=data["username"], pkey=data["pkey"])


class AccountManager:
    """
    Manages user account and friends list.
    
    Account data is stored locally and used to authenticate with Supabase.
    Friends list is just usernames of visited farms.
    """
    
    def __init__(self, data_dir: Path):
        """
        Initialize account manager.
        
        Args:
            data_dir: Directory to store account files
        """
        self._data_dir = data_dir
        self._account: Optional[Account] = None
        self._friends: list[str] = []
        self._loaded = False
    
    @property
    def account_path(self) -> Path:
        return self._data_dir / ACCOUNT_FILENAME
    
    @property
    def friends_path(self) -> Path:
        return self._data_dir / FRIENDS_FILENAME
    
    @property
    def has_account(self) -> bool:
        """Check if user has created an account."""
        self._ensure_loaded()
        return self._account is not None
    
    @property
    def account(self) -> Optional[Account]:
        """Get current account."""
        self._ensure_loaded()
        return self._account
    
    @property
    def username(self) -> Optional[str]:
        """Get current username."""
        self._ensure_loaded()
        return self._account.username if self._account else None
    
    @property
    def pkey(self) -> Optional[str]:
        """Get current pkey."""
        self._ensure_loaded()
        return self._account.pkey if self._account else None
    
    @property
    def friends(self) -> list[str]:
        """Get list of friend usernames."""
        self._ensure_loaded()
        return self._friends.copy()
    
    def _ensure_loaded(self) -> None:
        """Load data from disk if not already loaded."""
        if self._loaded:
            return
        
        self._load_account()
        self._load_friends()
        self._loaded = True
    
    def _load_account(self) -> None:
        """Load account from disk."""
        if not self.account_path.exists():
            self._account = None
            return
        
        try:
            with open(self.account_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._account = Account.from_dict(data)
            logger.info(f"Loaded account: {self._account.username}")
        except Exception as e:
            logger.error(f"Failed to load account: {e}")
            self._account = None
    
    def _load_friends(self) -> None:
        """Load friends list from disk."""
        if not self.friends_path.exists():
            self._friends = []
            return
        
        try:
            with open(self.friends_path, "r", encoding="utf-8") as f:
                self._friends = json.load(f)
            logger.info(f"Loaded {len(self._friends)} friends")
        except Exception as e:
            logger.error(f"Failed to load friends: {e}")
            self._friends = []
    
    def _save_account(self) -> None:
        """Save account to disk."""
        if self._account is None:
            return
        
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.account_path, "w", encoding="utf-8") as f:
                json.dump(self._account.to_dict(), f, indent=2)
            logger.info(f"Saved account: {self._account.username}")
        except Exception as e:
            logger.error(f"Failed to save account: {e}")
    
    def _save_friends(self) -> None:
        """Save friends list to disk."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.friends_path, "w", encoding="utf-8") as f:
                json.dump(self._friends, f, indent=2)
            logger.debug(f"Saved {len(self._friends)} friends")
        except Exception as e:
            logger.error(f"Failed to save friends: {e}")
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """
        Validate a username.
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username cannot be empty"
        
        if len(username) < USERNAME_MIN_LENGTH:
            return False, f"Username must be at least {USERNAME_MIN_LENGTH} characters"
        
        if len(username) > USERNAME_MAX_LENGTH:
            return False, f"Username must be at most {USERNAME_MAX_LENGTH} characters"
        
        if not USERNAME_PATTERN.match(username):
            return False, "Username can only contain lowercase letters, numbers, and underscores"
        
        return True, ""
    
    def create_account(self, username: str) -> tuple[bool, str, Optional[str]]:
        """
        Create a new account locally.
        
        Does NOT register with Supabase - that's done separately.
        
        Args:
            username: Chosen username
            
        Returns:
            Tuple of (success, error_message, pkey)
        """
        # Validate
        valid, error = self.validate_username(username)
        if not valid:
            return False, error, None
        
        # Generate pkey
        pkey = str(uuid.uuid4())
        
        # Create account
        self._account = Account(username=username, pkey=pkey)
        self._save_account()
        
        logger.info(f"Created local account: {username}")
        return True, "", pkey
    
    def add_friend(self, username: str) -> bool:
        """
        Add a friend to the list.
        
        Args:
            username: Friend's username
            
        Returns:
            True if added, False if already exists
        """
        self._ensure_loaded()
        
        # Normalize
        username = username.lower().strip()
        
        # Don't add self
        if self._account and username == self._account.username:
            return False
        
        # Check if already in list
        if username in self._friends:
            return False
        
        self._friends.append(username)
        self._save_friends()
        
        logger.info(f"Added friend: {username}")
        return True
    
    def remove_friend(self, username: str) -> bool:
        """
        Remove a friend from the list.
        
        Args:
            username: Friend's username
            
        Returns:
            True if removed, False if not found
        """
        self._ensure_loaded()
        
        username = username.lower().strip()
        
        if username not in self._friends:
            return False
        
        self._friends.remove(username)
        self._save_friends()
        
        logger.info(f"Removed friend: {username}")
        return True


# Global instance
_account_manager: Optional[AccountManager] = None


def get_account_manager() -> AccountManager:
    """Get the global account manager instance."""
    global _account_manager
    
    if _account_manager is None:
        # Use same data directory as save manager
        from .save_manager import get_save_manager
        save_manager = get_save_manager()
        _account_manager = AccountManager(save_manager._save_dir)
    
    return _account_manager
