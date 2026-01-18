"""
Decoration model - Represents decorative items placed on the farm.

Decorations are non-functional buildings that add visual appeal to the farm.
They support rotation for different viewing angles.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from ..core.constants import (
    DECORATION_COSTS,
    DECORATION_FOOTPRINTS,
    DECORATION_INFO,
    DecorationType,
    Direction,
)


@dataclass
class Decoration:
    """
    Represents a decorative item on the farm.
    
    Attributes:
        id: Unique identifier
        type: Type of decoration
        position: Grid position (x, y)
        direction: Facing direction (affects sprite rendering)
    """
    
    type: DecorationType
    position: tuple[int, int] = (0, 0)
    direction: Direction = Direction.EAST  # Default facing (WEST = flipped)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # ==========================================================================
    # Properties
    # ==========================================================================
    
    @property
    def display_name(self) -> str:
        """Get display name for this decoration."""
        info = DECORATION_INFO.get(self.type, {})
        return info.get("name", self.type.value.replace("_", " ").title())
    
    @property
    def emoji(self) -> str:
        """Get emoji for this decoration."""
        info = DECORATION_INFO.get(self.type, {})
        return info.get("emoji", "🏠")
    
    @property
    def cost(self) -> int:
        """Get purchase cost."""
        return DECORATION_COSTS.get(self.type, 100)
    
    @property
    def footprint(self) -> tuple[int, int]:
        """Get base footprint (width, height) in tiles."""
        return DECORATION_FOOTPRINTS.get(self.type, (1, 1))
    
    @property
    def rotated_footprint(self) -> tuple[int, int]:
        """
        Get footprint adjusted for current rotation.
        
        For EAST and WEST directions, width and height are swapped.
        """
        width, height = self.footprint
        if self.direction in (Direction.EAST, Direction.WEST):
            return (height, width)
        return (width, height)
    
    @property
    def can_rotate(self) -> bool:
        """Check if this decoration type supports rotation."""
        info = DECORATION_INFO.get(self.type, {})
        return info.get("can_rotate", False)
    
    # ==========================================================================
    # Methods
    # ==========================================================================
    
    def rotate_clockwise(self) -> None:
        """Toggle between EAST (default) and WEST (flipped) facing."""
        if not self.can_rotate:
            return
        
        # Simple toggle between two directions
        if self.direction == Direction.EAST:
            self.direction = Direction.WEST
        else:
            self.direction = Direction.EAST
    
    def rotate_counter_clockwise(self) -> None:
        """Toggle between EAST (default) and WEST (flipped) facing."""
        # Same as clockwise for 2-direction rotation
        self.rotate_clockwise()
    
    # ==========================================================================
    # Serialization
    # ==========================================================================
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize decoration to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "position": list(self.position),
            "direction": self.direction.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Decoration:
        """Deserialize decoration from dictionary."""
        # Normalize old directions (NORTH=0, SOUTH=180) to new system (EAST=90, WEST=270)
        dir_value = data.get("direction", 90)
        if dir_value in (0, 180):  # Convert old NORTH/SOUTH to EAST
            dir_value = 90
        return cls(
            id=data["id"],
            type=DecorationType(data["type"]),
            position=tuple(data["position"]),
            direction=Direction(dir_value),
        )
