"""
Save Manager - Handles saving and loading game state.

Saves game data to JSON files in the Anki profile folder (when running as addon)
or to a local folder (when running standalone).

Time is derived from farm.statistics.total_cards_answered, so no separate
time_system serialization is needed.
"""

from __future__ import annotations

import json
from ..utils.logger import get_logger
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.farm import Farm

logger = get_logger(__name__)

# Save file version for migration support
SAVE_VERSION = 2  # Bumped: removed time_system, time derived from card count
SAVE_FILENAME = "anki_animal_ranch_save.json"
BACKUP_FILENAME = "anki_animal_ranch_save_backup.json"


def get_save_directory() -> Path:
    """
    Get the directory where save files should be stored.
    
    When running as Anki addon: Uses Anki profile folder
    When running standalone: Uses ~/.anki_animal_ranch/
    
    Returns:
        Path to save directory
    """
    try:
        # Try to get Anki profile path
        from aqt import mw
        if mw and mw.pm and mw.pm.profileFolder():
            return Path(mw.pm.profileFolder())
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Could not get Anki profile folder: {e}")
    
    # Fallback to home directory
    save_dir = Path.home() / ".anki_animal_ranch"
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir


class SaveManager:
    """
    Manages saving and loading of game state.
    
    Features:
    - JSON-based save format (human-readable, debuggable)
    - Automatic backup before saving
    - Version tracking for future migrations
    - Graceful handling of corrupted saves
    """
    
    def __init__(self, save_dir: Path | None = None):
        """
        Initialize the save manager.
        
        Args:
            save_dir: Custom save directory (uses default if None)
        """
        self._save_dir = save_dir or get_save_directory()
        self._save_path = self._save_dir / SAVE_FILENAME
        self._backup_path = self._save_dir / BACKUP_FILENAME
        
        logger.info(f"Save directory: {self._save_dir}")
    
    @property
    def save_path(self) -> Path:
        """Get the path to the save file."""
        return self._save_path
    
    @property
    def save_exists(self) -> bool:
        """Check if a save file exists."""
        return self._save_path.exists()
    
    @property
    def backup_exists(self) -> bool:
        """Check if a backup save exists."""
        return self._backup_path.exists()
    
    def save(self, farm: Farm, app_version: str | None = None) -> bool:
        """
        Save the current game state.
        
        Time is derived from farm.statistics.total_cards_answered,
        so only the farm needs to be saved.
        
        Args:
            farm: The farm state to save
            app_version: Current app version (for changelog tracking)
            
        Returns:
            True if save was successful
        """
        try:
            # Create backup of existing save
            if self._save_path.exists():
                self._create_backup()
            
            # Build save data
            save_data = {
                "version": SAVE_VERSION,
                "saved_at": datetime.now().isoformat(),
                "farm": farm.to_dict(),
            }
            
            # Track app version for changelog
            if app_version:
                save_data["last_seen_version"] = app_version
            
            # Ensure directory exists
            self._save_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to temp file first (atomic save)
            temp_path = self._save_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            # Move temp to final location
            temp_path.replace(self._save_path)
            
            logger.info(f"Game saved to {self._save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return False
    
    def load(self) -> Farm | None:
        """
        Load game state from save file.
        
        Time is derived from farm.statistics.total_cards_answered.
        Initialize TimeSystem with this value after loading.
        
        Returns:
            Farm if successful, None otherwise
        """
        # Import here to avoid circular imports
        from ..models.farm import Farm
        
        # Try main save first
        save_data = self._load_file(self._save_path)
        
        # If main save fails, try backup
        if save_data is None and self._backup_path.exists():
            logger.warning("Main save corrupted, trying backup...")
            save_data = self._load_file(self._backup_path)
        
        if save_data is None:
            logger.info("No valid save file found")
            return None
        
        try:
            # Check version for migrations
            version = save_data.get("version", 1)
            if version > SAVE_VERSION:
                logger.warning(
                    f"Save file is from a newer version ({version}), "
                    f"current version is {SAVE_VERSION}"
                )
            
            # Migrate if needed
            save_data = self._migrate(save_data, version)
            
            # Deserialize farm
            farm_data = save_data.get("farm", {})
            farm = Farm.from_dict(farm_data)
            
            saved_at = save_data.get("saved_at", "unknown")
            logger.info(f"Game loaded from save (saved at: {saved_at})")
            
            return farm
            
        except Exception as e:
            logger.error(f"Failed to deserialize save data: {e}")
            return None
    
    def _load_file(self, path: Path) -> dict | None:
        """
        Load and parse a save file.
        
        Args:
            path: Path to the save file
            
        Returns:
            Parsed save data, or None if failed
        """
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in save file {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading save file {path}: {e}")
            return None
    
    def _create_backup(self) -> bool:
        """
        Create a backup of the current save file.
        
        Returns:
            True if backup was created successfully
        """
        try:
            if self._save_path.exists():
                # Read current save
                with open(self._save_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Write to backup
                with open(self._backup_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                logger.debug(f"Created backup at {self._backup_path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
        return False
    
    def _migrate(self, data: dict, from_version: int) -> dict:
        """
        Migrate save data from an older version.
        
        Args:
            data: The save data to migrate
            from_version: The version the data is from
            
        Returns:
            Migrated save data
        """
        # Version 1 -> 2: Remove time_system, time derived from card count
        # No actual data migration needed - we just ignore the old time_system
        # and use farm.statistics.total_cards_answered instead
        
        if from_version < 2:
            logger.info("Migrating save from v1 to v2 (time from card count)")
            # If old save has time_system with total_cards_answered,
            # ensure farm.statistics.total_cards_answered is set correctly
            time_system = data.get("time_system", {})
            old_card_count = time_system.get("total_cards_answered", 0)
            
            farm_data = data.get("farm", {})
            stats = farm_data.get("statistics", {})
            current_card_count = stats.get("total_cards_answered", 0)
            
            # Use the higher of the two counts (in case they diverged)
            if old_card_count > current_card_count:
                if "statistics" not in farm_data:
                    farm_data["statistics"] = {}
                farm_data["statistics"]["total_cards_answered"] = old_card_count
                data["farm"] = farm_data
                logger.info(f"Migrated card count: {old_card_count}")
            
            from_version = 2
        
        return data
    
    def delete_save(self) -> bool:
        """
        Delete the save file (for starting fresh).
        
        Returns:
            True if deletion was successful
        """
        try:
            if self._save_path.exists():
                self._save_path.unlink()
                logger.info("Save file deleted")
            if self._backup_path.exists():
                self._backup_path.unlink()
                logger.info("Backup file deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete save: {e}")
            return False
    
    def get_last_seen_version(self) -> str | None:
        """
        Get the last seen app version from the save file.
        
        Returns:
            Version string, or None if no save or no version recorded
        """
        if not self._save_path.exists():
            return None
        
        try:
            with open(self._save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("last_seen_version")
        except Exception as e:
            logger.error(f"Failed to read last seen version: {e}")
            return None
    
    def update_last_seen_version(self, version: str) -> bool:
        """
        Update only the last_seen_version in the save file.
        
        This is used after showing the changelog to avoid re-showing it.
        
        Args:
            version: The current app version
            
        Returns:
            True if successful
        """
        if not self._save_path.exists():
            return False
        
        try:
            # Read current save
            with open(self._save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Update version
            data["last_seen_version"] = version
            
            # Write back
            with open(self._save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated last seen version to {version}")
            return True
        except Exception as e:
            logger.error(f"Failed to update last seen version: {e}")
            return False
    
    def get_save_info(self) -> dict | None:
        """
        Get information about the current save without fully loading it.
        
        Returns:
            Dict with save info, or None if no save exists
        """
        if not self._save_path.exists():
            return None
        
        try:
            with open(self._save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            farm_data = data.get("farm", {})
            
            return {
                "version": data.get("version", 1),
                "saved_at": data.get("saved_at", "unknown"),
                "last_seen_version": data.get("last_seen_version"),
                "farm_name": farm_data.get("name", "Unknown"),
                "money": farm_data.get("money", 0),
                "animal_count": len(farm_data.get("animals", {})),
                "building_count": len(farm_data.get("buildings", {})),
            }
        except Exception as e:
            logger.error(f"Failed to read save info: {e}")
            return None


# Global save manager instance
_save_manager: SaveManager | None = None


def get_save_manager() -> SaveManager:
    """Get the global save manager instance."""
    global _save_manager
    if _save_manager is None:
        _save_manager = SaveManager()
    return _save_manager
