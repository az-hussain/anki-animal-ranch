"""
Save Manager - Handles saving and loading game state.

Saves game data to JSON files in the Anki profile folder (when running as addon)
or to a local folder (when running standalone).
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
    from ..core.time_system import TimeSystem

logger = get_logger(__name__)

# Save file version for migration support
SAVE_VERSION = 1
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
    
    def save(
        self,
        farm: Farm,
        time_system: TimeSystem,
    ) -> bool:
        """
        Save the current game state.
        
        Args:
            farm: The farm state to save
            time_system: The time system state to save
            
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
                "time_system": time_system.to_dict(),
            }
            
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
    
    def load(self) -> tuple[Farm, TimeSystem] | None:
        """
        Load game state from save file.
        
        Returns:
            Tuple of (Farm, TimeSystem) if successful, None otherwise
        """
        # Import here to avoid circular imports
        from ..models.farm import Farm
        from ..core.time_system import TimeSystem
        
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
            
            # Deserialize time system
            time_data = save_data.get("time_system", {})
            time_system = TimeSystem.from_dict(time_data)
            
            saved_at = save_data.get("saved_at", "unknown")
            logger.info(f"Game loaded from save (saved at: {saved_at})")
            
            return farm, time_system
            
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
        # Currently at version 1, no migrations needed yet
        # Future migrations would go here:
        #
        # if from_version < 2:
        #     data = self._migrate_v1_to_v2(data)
        #     from_version = 2
        #
        # if from_version < 3:
        #     data = self._migrate_v2_to_v3(data)
        #     from_version = 3
        
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
