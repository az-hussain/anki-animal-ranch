"""
Placement and visit state containers for MainWindow.

Replaces the 11 scattered boolean/optional flags on MainWindow with two
explicit dataclasses. Import and use these instead of direct flag access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..core.constants import BuildingType, DecorationType, Direction

if TYPE_CHECKING:
    from ..models.farm import Farm


@dataclass
class PlacementState:
    """
    All state for building/decoration placement and move operations.

    active=True while the user is placing or moving something.
    Exactly one of (building_type, decoration_type) is set during active placement.
    Exactly one of (move_building_id, move_decoration_id) is set during a move.
    preview_sprite holds the ghost sprite shown under the cursor.
    """

    active: bool = False
    building_type: BuildingType | None = None
    decoration_type: DecorationType | None = None
    direction: Direction = field(default_factory=lambda: Direction.EAST)
    move_building_id: str | None = None
    move_decoration_id: str | None = None
    preview_sprite: Any | None = None  # BuildingSprite | DecorationSprite during placement

    @property
    def is_moving(self) -> bool:
        """True when moving an existing building or decoration (not placing a new one)."""
        return self.move_building_id is not None or self.move_decoration_id is not None

    def reset(self) -> None:
        """Clear all placement state after completion or cancellation."""
        self.active = False
        self.building_type = None
        self.decoration_type = None
        self.direction = Direction.EAST
        self.move_building_id = None
        self.move_decoration_id = None
        self.preview_sprite = None


@dataclass
class VisitState:
    """
    All state for the friend-farm visit feature.

    active=True while viewing a friend's farm.
    home_farm and home_unlocked_zones hold the saved home data so we
    can restore when the user clicks 'Return Home'.
    """

    active: bool = False
    username: str | None = None
    home_farm: Farm | None = None
    home_unlocked_zones: int | None = None

    def reset(self) -> None:
        """Clear visit state after returning home."""
        self.active = False
        self.username = None
        self.home_farm = None
        self.home_unlocked_zones = None
