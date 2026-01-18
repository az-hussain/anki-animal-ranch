"""
Tile grid system for the farm terrain.

Manages the grid of ground tiles that make up the farm.
"""

from __future__ import annotations

from ..utils.logger import get_logger
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Iterator

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor

from ..core.constants import TILE_HEIGHT, TILE_WIDTH, ZONE_HEIGHT, ZONE_WIDTH
from .sprite import TileSprite

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QGraphicsScene

logger = get_logger(__name__)


class TileType(Enum):
    """Types of terrain tiles."""
    GRASS = auto()
    GRASS_FLOWERS = auto()
    DIRT = auto()
    DIRT_PATH = auto()
    WATER = auto()
    LOCKED = auto()  # Unpurchased zone


@dataclass
class Tile:
    """
    Represents a single tile in the grid.
    
    Attributes:
        x: Grid X coordinate
        y: Grid Y coordinate
        type: Type of terrain
        walkable: Whether characters can walk on this tile
        buildable: Whether buildings can be placed here
        sprite: The visual sprite for this tile
    """
    x: int
    y: int
    type: TileType = TileType.GRASS
    walkable: bool = True
    buildable: bool = True
    sprite: TileSprite | None = None
    
    # Building reference (if a building occupies this tile)
    building_id: str | None = None
    
    @property
    def is_occupied(self) -> bool:
        """Check if this tile is occupied by a building."""
        return self.building_id is not None


# Color mapping for tile types
TILE_COLORS: dict[TileType, QColor] = {
    TileType.GRASS: QColor(90, 160, 90),          # Green
    TileType.GRASS_FLOWERS: QColor(100, 170, 100),  # Lighter green
    TileType.DIRT: QColor(139, 119, 101),         # Brown
    TileType.DIRT_PATH: QColor(160, 140, 120),    # Lighter brown
    TileType.WATER: QColor(70, 130, 180),         # Blue
    TileType.LOCKED: QColor(80, 80, 80),          # Dark gray
}


class TileGrid:
    """
    Manages the grid of tiles that make up the farm terrain.
    
    The grid is divided into zones, which can be unlocked progressively.
    Each zone is ZONE_WIDTH x ZONE_HEIGHT tiles.
    """
    
    def __init__(
        self,
        zones_wide: int = 3,
        zones_tall: int = 4,
        unlocked_zones: int = 1,
    ):
        """
        Initialize the tile grid.
        
        Args:
            zones_wide: Number of zones horizontally
            zones_tall: Number of zones vertically
            unlocked_zones: Number of zones initially unlocked
        """
        self.zones_wide = zones_wide
        self.zones_tall = zones_tall
        self.total_zones = zones_wide * zones_tall
        self._unlocked_zones = min(unlocked_zones, self.total_zones)
        
        # Calculate total grid size
        self.width = zones_wide * ZONE_WIDTH
        self.height = zones_tall * ZONE_HEIGHT
        
        # Create tile array
        self._tiles: list[list[Tile]] = []
        self._create_tiles()
        
        # Scene reference (set when added to scene)
        self._scene: QGraphicsScene | None = None
        
        logger.info(f"Created tile grid: {self.width}x{self.height} tiles, "
                   f"{self.zones_wide}x{self.zones_tall} zones")
    
    def _create_tiles(self) -> None:
        """Create the tile grid."""
        self._tiles = []
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Determine zone for this tile
                zone_x = x // ZONE_WIDTH
                zone_y = y // ZONE_HEIGHT
                zone_index = zone_y * self.zones_wide + zone_x
                
                # Determine tile type
                if zone_index >= self._unlocked_zones:
                    tile_type = TileType.LOCKED
                    walkable = False
                    buildable = False
                else:
                    # Random grass variation
                    if random.random() < 0.15:
                        tile_type = TileType.GRASS_FLOWERS
                    else:
                        tile_type = TileType.GRASS
                    walkable = True
                    buildable = True
                
                tile = Tile(
                    x=x,
                    y=y,
                    type=tile_type,
                    walkable=walkable,
                    buildable=buildable,
                )
                row.append(tile)
            self._tiles.append(row)
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def unlocked_zones(self) -> int:
        return self._unlocked_zones
    
    @unlocked_zones.setter
    def unlocked_zones(self, value: int) -> None:
        old_value = self._unlocked_zones
        self._unlocked_zones = max(1, min(value, self.total_zones))
        
        if self._unlocked_zones != old_value:
            self._update_zone_tiles()
    
    # =========================================================================
    # Tile Access
    # =========================================================================
    
    def get_tile(self, x: int, y: int) -> Tile | None:
        """
        Get the tile at grid coordinates.
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            
        Returns:
            The tile, or None if out of bounds
        """
        if not self.is_valid_position(x, y):
            return None
        return self._tiles[y][x]
    
    def set_tile_type(self, x: int, y: int, tile_type: TileType) -> bool:
        """
        Set the type of a tile.
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            tile_type: New tile type
            
        Returns:
            True if successful
        """
        tile = self.get_tile(x, y)
        if tile is None:
            return False
        
        tile.type = tile_type
        tile.walkable = tile_type not in (TileType.WATER, TileType.LOCKED)
        tile.buildable = tile_type in (TileType.GRASS, TileType.GRASS_FLOWERS, TileType.DIRT)
        
        # Update sprite color
        if tile.sprite:
            tile.sprite.set_placeholder(TILE_COLORS[tile_type], "diamond")
        
        return True
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if coordinates are within the grid."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable."""
        tile = self.get_tile(x, y)
        return tile is not None and tile.walkable and not tile.is_occupied
    
    def is_buildable(self, x: int, y: int) -> bool:
        """Check if a building can be placed at this position."""
        tile = self.get_tile(x, y)
        return tile is not None and tile.buildable and not tile.is_occupied
    
    def can_place_building(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> bool:
        """
        Check if a building footprint can be placed.
        
        Args:
            x: Top-left X coordinate
            y: Top-left Y coordinate
            width: Building width in tiles
            height: Building height in tiles
            
        Returns:
            True if all tiles are buildable
        """
        for dy in range(height):
            for dx in range(width):
                if not self.is_buildable(x + dx, y + dy):
                    return False
        return True
    
    def mark_building(
        self,
        building_id: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> bool:
        """
        Mark tiles as occupied by a building.
        
        Args:
            building_id: ID of the building
            x: Top-left X coordinate
            y: Top-left Y coordinate
            width: Building width
            height: Building height
            
        Returns:
            True if successful
        """
        if not self.can_place_building(x, y, width, height):
            return False
        
        for dy in range(height):
            for dx in range(width):
                tile = self.get_tile(x + dx, y + dy)
                if tile:
                    tile.building_id = building_id
        
        return True
    
    def clear_building(self, building_id: str) -> None:
        """Remove building reference from all tiles."""
        for row in self._tiles:
            for tile in row:
                if tile.building_id == building_id:
                    tile.building_id = None
    
    # =========================================================================
    # Zone Management
    # =========================================================================
    
    def get_zone_index(self, x: int, y: int) -> int:
        """Get the zone index for a tile position."""
        zone_x = x // ZONE_WIDTH
        zone_y = y // ZONE_HEIGHT
        return zone_y * self.zones_wide + zone_x
    
    def is_zone_unlocked(self, zone_index: int) -> bool:
        """Check if a zone is unlocked."""
        return zone_index < self._unlocked_zones
    
    def is_tile_unlocked(self, x: int, y: int) -> bool:
        """Check if a tile's zone is unlocked."""
        zone_index = self.get_zone_index(x, y)
        return self.is_zone_unlocked(zone_index)
    
    def _update_zone_tiles(self) -> None:
        """Update tile states after zone unlock."""
        for y in range(self.height):
            for x in range(self.width):
                tile = self._tiles[y][x]
                zone_index = self.get_zone_index(x, y)
                
                if zone_index < self._unlocked_zones:
                    if tile.type == TileType.LOCKED:
                        # Unlock tile
                        if random.random() < 0.15:
                            new_type = TileType.GRASS_FLOWERS
                        else:
                            new_type = TileType.GRASS
                        
                        tile.type = new_type
                        tile.walkable = True
                        tile.buildable = True
                        
                        if tile.sprite:
                            tile.sprite.is_locked = False
                else:
                    if tile.type != TileType.LOCKED:
                        tile.type = TileType.LOCKED
                        tile.walkable = False
                        tile.buildable = False
                        
                        if tile.sprite:
                            tile.sprite.is_locked = True
    
    # =========================================================================
    # Scene Integration
    # =========================================================================
    
    def add_to_scene(self, scene: QGraphicsScene) -> None:
        """
        Add all tile sprites to a graphics scene.
        
        Args:
            scene: The QGraphicsScene to add to
        """
        self._scene = scene
        
        for y in range(self.height):
            for x in range(self.width):
                tile = self._tiles[y][x]
                
                # Create sprite
                sprite = TileSprite(x, y)
                
                # Set locked state (shows green with gray overlay)
                if tile.type == TileType.LOCKED:
                    sprite.is_locked = True
                
                tile.sprite = sprite
                scene.addItem(sprite)
        
        logger.info(f"Added {self.width * self.height} tile sprites to scene")
    
    def set_grid_visible(self, visible: bool) -> None:
        """
        Show or hide the grid lines on all tiles.
        
        Args:
            visible: True to show grid lines, False to hide
        """
        for row in self._tiles:
            for tile in row:
                if tile.sprite:
                    tile.sprite.show_border = visible
    
    def remove_from_scene(self) -> None:
        """Remove all tile sprites from the scene."""
        if self._scene is None:
            return
        
        for row in self._tiles:
            for tile in row:
                if tile.sprite:
                    self._scene.removeItem(tile.sprite)
                    tile.sprite = None
        
        self._scene = None
    
    # =========================================================================
    # Iteration
    # =========================================================================
    
    def __iter__(self) -> Iterator[Tile]:
        """Iterate over all tiles."""
        for row in self._tiles:
            yield from row
    
    def iter_zone(self, zone_index: int) -> Iterator[Tile]:
        """Iterate over tiles in a specific zone."""
        zone_x = zone_index % self.zones_wide
        zone_y = zone_index // self.zones_wide
        
        start_x = zone_x * ZONE_WIDTH
        start_y = zone_y * ZONE_HEIGHT
        end_x = start_x + ZONE_WIDTH
        end_y = start_y + ZONE_HEIGHT
        
        for y in range(start_y, min(end_y, self.height)):
            for x in range(start_x, min(end_x, self.width)):
                yield self._tiles[y][x]
    
    def iter_neighbors(self, x: int, y: int, include_diagonals: bool = False) -> Iterator[Tile]:
        """Iterate over neighboring tiles."""
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        if include_diagonals:
            directions.extend([(-1, -1), (1, -1), (1, 1), (-1, 1)])
        
        for dx, dy in directions:
            tile = self.get_tile(x + dx, y + dy)
            if tile is not None:
                yield tile
