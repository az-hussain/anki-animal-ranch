"""
Building model - Represents farm buildings.

Buildings house animals, store products, and provide
various farm functionality. They can be upgraded to
increase capacity and efficiency.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..core.constants import (
    ANIMAL_SIZES,
    BUILDING_CAPACITIES,
    BUILDING_FOOTPRINTS,
    BUILDING_PRODUCTION_BONUSES,
    BUILDING_UPGRADE_COSTS,
    MAX_BUILDING_LEVEL,
    AnimalType,
    BuildingType,
)

if TYPE_CHECKING:
    from .animal import Animal


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


@dataclass
class Building:
    """
    Represents a building on the farm.
    
    Buildings provide housing for animals, storage for products,
    and various farm facilities. They occupy space on the farm
    grid and can be upgraded for increased capacity.
    
    Attributes:
        id: Unique identifier
        type: The type of building
        level: Current upgrade level (1-4)
        position: Grid position (x, y) of the top-left corner
        animals: List of animal IDs housed in this building
        cleanliness: Cleanliness level from 0.0 to 1.0
        name: Optional custom name for the building
    """
    
    type: BuildingType
    position: tuple[int, int]
    id: str = field(default_factory=generate_id)
    level: int = 1
    animals: list[str] = field(default_factory=list)
    cleanliness: float = 1.0
    name: str = ""
    
    def __post_init__(self) -> None:
        """Validate initial values."""
        self.level = max(1, min(MAX_BUILDING_LEVEL, self.level))
        self.cleanliness = max(0.0, min(1.0, self.cleanliness))
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def capacity(self) -> int:
        """
        Get the current animal capacity in 'animal units'.
        
        Small animals = 1 unit, Medium = 2, Large = 3
        """
        if self.type not in BUILDING_CAPACITIES:
            return 0
        return BUILDING_CAPACITIES[self.type][self.level - 1]
    
    @property
    def current_occupancy(self) -> int:
        """Get the number of animals currently housed."""
        return len(self.animals)
    
    @property
    def is_full(self) -> bool:
        """Check if the building is at capacity."""
        return self.current_occupancy >= self.capacity
    
    @property
    def occupancy_ratio(self) -> float:
        """Get the occupancy as a ratio (0.0 to 1.0)."""
        if self.capacity == 0:
            return 0.0
        return self.current_occupancy / self.capacity
    
    @property
    def footprint(self) -> tuple[int, int]:
        """Get the building footprint (width, height) in tiles."""
        return BUILDING_FOOTPRINTS.get(self.type, (2, 2))
    
    @property
    def tiles_occupied(self) -> list[tuple[int, int]]:
        """Get list of all tiles occupied by this building."""
        tiles = []
        width, height = self.footprint
        for dx in range(width):
            for dy in range(height):
                tiles.append((self.position[0] + dx, self.position[1] + dy))
        return tiles
    
    @property
    def center_position(self) -> tuple[float, float]:
        """Get the center position of the building."""
        width, height = self.footprint
        return (
            self.position[0] + width / 2,
            self.position[1] + height / 2,
        )
    
    @property
    def production_bonus(self) -> float:
        """Get the production bonus for animals in this building."""
        return BUILDING_PRODUCTION_BONUSES[self.level - 1]
    
    @property
    def can_upgrade(self) -> bool:
        """Check if the building can be upgraded."""
        return self.level < MAX_BUILDING_LEVEL
    
    @property
    def upgrade_cost(self) -> int:
        """Get the cost to upgrade to the next level."""
        if not self.can_upgrade:
            return 0
        base_cost = BUILDING_UPGRADE_COSTS.get(self.type, 1000)
        return base_cost * self.level
    
    @property
    def is_animal_housing(self) -> bool:
        """Check if this building can house animals."""
        return self.type in (BuildingType.COOP, BuildingType.PIGSTY, BuildingType.BARN)
    
    @property
    def allowed_animal_type(self) -> AnimalType | None:
        """Get the type of animal this building can house."""
        mapping = {
            BuildingType.COOP: AnimalType.CHICKEN,
            BuildingType.PIGSTY: AnimalType.PIG,
            BuildingType.BARN: AnimalType.COW,
        }
        return mapping.get(self.type)
    
    @property
    def display_name(self) -> str:
        """Get the display name."""
        if self.name:
            return self.name
        return f"{self.type.value.replace('_', ' ').title()} (Lv.{self.level})"
    
    # =========================================================================
    # Animal Management
    # =========================================================================
    
    def can_add_animal(self, animal_type: AnimalType) -> bool:
        """
        Check if an animal of the given type can be added.
        
        Args:
            animal_type: The type of animal to add
            
        Returns:
            True if the animal can be added
        """
        # Check if building type matches
        if self.allowed_animal_type != animal_type:
            return False
        
        # Check capacity (each animal takes 1 slot)
        return not self.is_full
    
    def add_animal(self, animal_id: str) -> bool:
        """
        Add an animal to this building.
        
        Args:
            animal_id: The ID of the animal to add
            
        Returns:
            True if the animal was added successfully
        """
        if self.is_full:
            return False
        if animal_id in self.animals:
            return False
        
        self.animals.append(animal_id)
        return True
    
    def remove_animal(self, animal_id: str) -> bool:
        """
        Remove an animal from this building.
        
        Args:
            animal_id: The ID of the animal to remove
            
        Returns:
            True if the animal was removed
        """
        if animal_id not in self.animals:
            return False
        
        self.animals.remove(animal_id)
        return True
    
    # =========================================================================
    # Update Methods
    # =========================================================================
    
    def update(self, hours_passed: float) -> None:
        """
        Update the building state for elapsed time.
        
        Args:
            hours_passed: Number of game hours that have passed
        """
        # Cleanliness decreases over time based on occupancy
        if self.current_occupancy > 0:
            decay_rate = 0.01 * (self.occupancy_ratio + 0.5)
            self.cleanliness = max(0.0, self.cleanliness - decay_rate * hours_passed)
    
    def clean(self, amount: float = 1.0) -> None:
        """
        Clean the building.
        
        Args:
            amount: Amount to clean (0.0 to 1.0)
        """
        self.cleanliness = min(1.0, self.cleanliness + amount)
    
    def upgrade(self) -> bool:
        """
        Upgrade the building to the next level.
        
        Returns:
            True if the upgrade was successful
        """
        if not self.can_upgrade:
            return False
        
        self.level += 1
        return True
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "level": self.level,
            "position": list(self.position),
            "animals": self.animals.copy(),
            "cleanliness": self.cleanliness,
            "name": self.name,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Building:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            type=BuildingType(data["type"]),
            level=data.get("level", 1),
            position=tuple(data["position"]),
            animals=data.get("animals", []),
            cleanliness=data.get("cleanliness", 1.0),
            name=data.get("name", ""),
        )
    
    def __str__(self) -> str:
        return f"{self.display_name} at {self.position}"
    
    def __repr__(self) -> str:
        return f"Building(id={self.id!r}, type={self.type}, level={self.level})"
