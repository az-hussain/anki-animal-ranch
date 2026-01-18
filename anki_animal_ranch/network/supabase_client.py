"""
Supabase client for Anki Animal Ranch.

Handles direct communication with Supabase REST API using urllib (built-in).
No external dependencies required - works in Anki's Python environment.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Optional
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Supabase configuration (hardcoded - publishable key is safe to expose)
SUPABASE_URL = "https://pioiqgyssilvgchqktuh.supabase.co"
SUPABASE_KEY = "sb_publishable_c7TOVItzGcgQpNiOVWZjTQ_RfPk52pd"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    error: Optional[str] = None
    data: Optional[Any] = None


def _make_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[dict] = None,
    extra_headers: Optional[dict] = None,
) -> tuple[bool, Any, Optional[str]]:
    """
    Make a request to Supabase REST API.
    
    Args:
        endpoint: API endpoint (e.g., "/rest/v1/farms")
        method: HTTP method
        data: JSON data to send
        extra_headers: Additional headers
        
    Returns:
        Tuple of (success, response_data, error_message)
    """
    url = f"{SUPABASE_URL}{endpoint}"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    
    if extra_headers:
        headers.update(extra_headers)
    
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = response.read().decode("utf-8")
            if result:
                return True, json.loads(result), None
            return True, None, None
            
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except:
            pass
        error_msg = f"HTTP {e.code}: {e.reason}"
        if error_body:
            try:
                error_data = json.loads(error_body)
                if "message" in error_data:
                    error_msg = error_data["message"]
            except:
                pass
        logger.error(f"Supabase HTTP error: {error_msg}")
        return False, None, error_msg
        
    except urllib.error.URLError as e:
        error_msg = f"Network error: {e.reason}"
        logger.error(f"Supabase URL error: {error_msg}")
        return False, None, error_msg
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Supabase request error: {error_msg}")
        return False, None, error_msg


def is_online_available() -> bool:
    """
    Check if online features are available.
    
    We assume online by default and let actual operations fail gracefully.
    This avoids false negatives from strict health checks.
    """
    # Always return True - let actual API calls handle errors
    # This is simpler and more reliable than a health check
    return True


def check_username_available(username: str) -> SyncResult:
    """
    Check if a username is available.
    
    Args:
        username: Username to check
        
    Returns:
        SyncResult with success=True if available, False if taken or error
    """
    endpoint = f"/rest/v1/farms?username=eq.{urllib.parse.quote(username)}&select=username"
    
    success, data, error = _make_request(endpoint, "GET")
    
    if not success:
        return SyncResult(False, error or "Failed to check username")
    
    if data and len(data) > 0:
        return SyncResult(False, "Username already taken")
    
    return SyncResult(True)


def create_account(username: str, pkey: str, farm_json: dict) -> SyncResult:
    """
    Create a new account in Supabase.
    
    Args:
        username: Unique username
        pkey: Secret UUID key
        farm_json: Initial farm data
        
    Returns:
        SyncResult indicating success/failure
    """
    endpoint = "/rest/v1/farms"
    
    data = {
        "username": username,
        "pkey": pkey,
        "farm_json": farm_json,
    }
    
    success, result, error = _make_request(endpoint, "POST", data)
    
    if not success:
        if error and ("duplicate" in error.lower() or "unique" in error.lower()):
            return SyncResult(False, "Username already taken")
        return SyncResult(False, error or "Failed to create account")
    
    logger.info(f"Created account for {username}")
    return SyncResult(True, data=result)


def sync_farm(username: str, pkey: str, farm_json: dict) -> SyncResult:
    """
    Sync farm data to Supabase.
    
    Only updates if username AND pkey match (security).
    
    Args:
        username: Account username
        pkey: Secret key for authentication
        farm_json: Farm data to sync
        
    Returns:
        SyncResult indicating success/failure
    """
    # URL-encode username and pkey for the query
    endpoint = (
        f"/rest/v1/farms"
        f"?username=eq.{urllib.parse.quote(username)}"
        f"&pkey=eq.{urllib.parse.quote(pkey)}"
    )
    
    data = {"farm_json": farm_json}
    
    success, result, error = _make_request(endpoint, "PATCH", data)
    
    if not success:
        return SyncResult(False, error or "Failed to sync farm")
    
    # Check if update affected any rows
    if result and len(result) > 0:
        logger.debug(f"Synced farm for {username}")
        return SyncResult(True)
    else:
        # No rows updated - either username doesn't exist or pkey wrong
        logger.warning(f"Farm sync failed for {username} - no matching record")
        return SyncResult(False, "Sync failed - invalid credentials")


def fetch_farm(username: str) -> SyncResult:
    """
    Fetch a friend's farm data.
    
    Args:
        username: Friend's username
        
    Returns:
        SyncResult with farm_json in data field if successful
    """
    endpoint = (
        f"/rest/v1/farms"
        f"?username=eq.{urllib.parse.quote(username)}"
        f"&select=username,farm_json,updated_at"
    )
    
    success, result, error = _make_request(endpoint, "GET")
    
    if not success:
        return SyncResult(False, error or "Failed to fetch farm")
    
    if result and len(result) > 0:
        farm_data = result[0]
        logger.info(f"Fetched farm for {username}")
        return SyncResult(True, data=farm_data)
    else:
        return SyncResult(False, "User not found")
