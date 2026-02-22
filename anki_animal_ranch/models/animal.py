"""
Animal model - Represents animals on the farm.

Animals have a lifecycle (baby -> teen -> adult), need care,
produce products, and can be sold at market.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..core.constants import (
    ANIMAL_BASE_SALE_PRICES,
    ANIMAL_GROWTH_RATES,
    ANIMAL_PRODUCTION_INTERVALS,
    ANIMAL_PRODUCTS,
    ANIMAL_SIZES,
    GROWTH_STAGE_THRESHOLDS,
    AnimalSize,
    AnimalType,
    GrowthStage,
    ProductType,
)

if TYPE_CHECKING:
    from .product import Product


def generate_id() -> str:
    """Generate a unique ID for an entity."""
    return str(uuid.uuid4())


@dataclass
class Animal:
    """
    Represents an animal on the farm.
    
    Animals grow over time based on their health (fed → healthy → quality products).
    Product quality is determined by health at production time.
    
    Feed System:
        - Feed is consumed daily (auto from inventory)
        - Fed animals have full hunger (100%)
        - Unfed animals lose hunger → health decays
        - Health determines product quality tier
    
    Attributes:
        id: Unique identifier
        type: The type of animal (chicken, pig, cow)
        name: Optional pet name
        age_hours: Total age in game hours
        maturity: Growth progress from 0.0 to 1.0
        health: Current health from 0.0 to 1.0 (affects product quality)
        hunger: Fullness level from 0.0 to 1.0 (1.0 = full, set by feed system)
        building_id: ID of the building this animal is in
        hours_since_production: Hours since last production cycle
    """
    
    type: AnimalType
    id: str = field(default_factory=generate_id)
    name: str = ""
    age_hours: float = 0.0
    maturity: float = 0.0
    health: float = 1.0
    hunger: float = 1.0
    building_id: str = ""
    hours_since_production: float = 0.0
    
    # Animation state (not saved)
    _current_animation: str = field(default="idle", repr=False)
    _animation_frame: int = field(default=0, repr=False)
    _target_position: tuple[float, float] | None = field(default=None, repr=False)
    
    def __post_init__(self) -> None:
        """Validate initial values."""
        self.maturity = max(0.0, min(1.0, self.maturity))
        self.health = max(0.0, min(1.0, self.health))
        self.hunger = max(0.0, min(1.0, self.hunger))
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def growth_stage(self) -> GrowthStage:
        """Get the current growth stage based on maturity."""
        if self.maturity >= GROWTH_STAGE_THRESHOLDS[GrowthStage.ADULT]:
            return GrowthStage.ADULT
        elif self.maturity >= GROWTH_STAGE_THRESHOLDS[GrowthStage.TEEN]:
            return GrowthStage.TEEN
        return GrowthStage.BABY
    
    @property
    def is_mature(self) -> bool:
        """Check if the animal is mature enough to produce (adult stage)."""
        return self.growth_stage == GrowthStage.ADULT
    
    @property
    def can_produce(self) -> bool:
        """Check if the animal can produce products."""
        return self.is_mature and self.health > 0.3
    
    @property
    def size(self) -> AnimalSize:
        """Get the size category of this animal."""
        return ANIMAL_SIZES[self.type]
    
    @property
    def size_units(self) -> int:
        """Get the number of capacity units this animal takes."""
        return self.size.value
    
    @property
    def product_type(self) -> ProductType:
        """Get the type of product this animal produces."""
        return ANIMAL_PRODUCTS[self.type]
    
    @property
    def production_interval(self) -> int:
        """Get hours between production cycles."""
        return ANIMAL_PRODUCTION_INTERVALS[self.type]
    
    @property
    def can_produce_now(self) -> bool:
        """Check if production is ready."""
        return (
            self.can_produce and 
            self.hours_since_production >= self.production_interval
        )
    
    @property
    def growth_rate(self) -> float:
        """
        Get the current growth rate (maturity per hour).

        Growth rate is affected by health.
        """
        base_rate = ANIMAL_GROWTH_RATES[self.type]
        return base_rate * self.health
    
    @property
    def sale_value(self) -> int:
        """
        Calculate the current sale value.
        
        Value depends on maturity and health.
        """
        base_price = ANIMAL_BASE_SALE_PRICES[self.type]
        maturity_factor = max(0.3, self.maturity)  # Minimum 30% value
        health_factor = max(0.5, self.health)  # Minimum 50% of health value
        
        return int(base_price * maturity_factor * health_factor)
    
    @property
    def display_name(self) -> str:
        """Get the display name (pet name or type name)."""
        if self.name:
            return self.name
        return self.type.value.capitalize()
    
    # =========================================================================
    # Update Methods
    # =========================================================================
    
    def update(self, hours_passed: float) -> None:
        """
        Update the animal state for elapsed time.
        
        Args:
            hours_passed: Number of game hours that have passed
        """
        self.age_hours += hours_passed
        
        # Growth (only if not fully mature)
        if self.maturity < 1.0:
            growth = self.growth_rate * hours_passed
            self.maturity = min(1.0, self.maturity + growth)
        
        # Hunger decreases over time
        hunger_decay = 0.02 * hours_passed  # Lose ~50% hunger per day
        self.hunger = max(0.0, self.hunger - hunger_decay)
        
        # Health decreases if hungry
        if self.hunger < 0.3:
            health_decay = 0.01 * hours_passed * (0.3 - self.hunger) / 0.3
            self.health = max(0.0, self.health - health_decay)
        
        # Production timer
        if self.can_produce:
            self.hours_since_production += hours_passed
    
    def feed(self, amount: float = 1.0) -> None:
        """
        Feed the animal.
        
        Args:
            amount: Amount to feed (0.0 to 1.0, typically 1.0 for full feeding)
        """
        self.hunger = min(1.0, self.hunger + amount)
    
    def heal(self, amount: float = 0.5) -> None:
        """
        Heal the animal (veterinary treatment).
        
        Args:
            amount: Amount to heal (0.0 to 1.0)
        """
        self.health = min(1.0, self.health + amount)
    
    def collect_product(self) -> bool:
        """
        Attempt to collect a product.
        
        Returns:
            True if a product was collected, False otherwise
        """
        if self.can_produce_now:
            self.hours_since_production = 0.0
            return True
        return False
    
    # =========================================================================
    # Animation Methods
    # =========================================================================
    
    def set_animation(self, animation: str) -> None:
        """Set the current animation."""
        if animation != self._current_animation:
            self._current_animation = animation
            self._animation_frame = 0
    
    def set_target_position(self, x: float, y: float) -> None:
        """Set a target position for wandering animation."""
        self._target_position = (x, y)
        self.set_animation("walk")
    
    def clear_target(self) -> None:
        """Clear the movement target."""
        self._target_position = None
        self.set_animation("idle")
    
    @property
    def target_position(self) -> tuple[float, float] | None:
        """Get the current target position."""
        return self._target_position
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "age_hours": self.age_hours,
            "maturity": self.maturity,
            "health": self.health,
            "hunger": self.hunger,
            "building_id": self.building_id,
            "hours_since_production": self.hours_since_production,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Animal:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            type=AnimalType(data["type"]),
            name=data.get("name", ""),
            age_hours=data.get("age_hours", 0.0),
            maturity=data.get("maturity", 0.0),
            health=data.get("health", 1.0),
            hunger=data.get("hunger", 1.0),
            building_id=data.get("building_id", ""),
            hours_since_production=data.get("hours_since_production", 0.0),
        )
    
    def __str__(self) -> str:
        return f"{self.display_name} ({self.growth_stage.value}, {self.maturity:.0%} mature)"
    
    def __repr__(self) -> str:
        return f"Animal(id={self.id!r}, type={self.type}, maturity={self.maturity:.2f})"
