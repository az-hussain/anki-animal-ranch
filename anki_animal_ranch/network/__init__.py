"""
Network and cloud features.

Handles:
- Cloud save synchronization (Supabase)
- Friend system
- Farm visits
"""

from .supabase_client import (
    is_online_available,
    check_username_available,
    create_account,
    sync_farm,
    fetch_farm,
    SyncResult,
)

__all__ = [
    "is_online_available",
    "check_username_available",
    "create_account",
    "sync_farm",
    "fetch_farm",
    "SyncResult",
]
