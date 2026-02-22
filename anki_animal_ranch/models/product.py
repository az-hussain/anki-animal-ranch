"""
Product model - Represents products produced by animals.

Products have quality tiers and freshness that affect their value.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from ..core.constants import (
    PRODUCT_BASE_PRICES,
    PRODUCT_FRESHNESS_DECAY_RATES,
    PRODUCT_QUALITY_MULTIPLIERS,
    ProductQuality,
    ProductType,
)


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


@dataclass
class Product:
    """
    Represents a product produced by an animal.
    
    Products can be collected and sold at market. Their value
    depends on type, quality, and freshness.
    
    Attributes:
        id: Unique identifier
        type: The type of product (egg, milk, truffle)
        quality: Quality tier affecting value
        quantity: Number of units
        freshness: Freshness from 0.0 to 1.0 (decays over time)
        source_animal_id: ID of the animal that produced this
        produced_at: Game time when produced (for tracking)
    """
    
    type: ProductType
    id: str = field(default_factory=generate_id)
    quality: ProductQuality = ProductQuality.BASIC
    quantity: int = 1
    freshness: float = 1.0
    source_animal_id: str = ""
    produced_at: float = 0.0  # Total game hours when produced
    
    def __post_init__(self) -> None:
        """Validate initial values."""
        self.quantity = max(1, self.quantity)
        self.freshness = max(0.0, min(1.0, self.freshness))
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def base_price(self) -> int:
        """Get the base price for this product type."""
        return PRODUCT_BASE_PRICES[self.type]
    
    @property
    def quality_multiplier(self) -> float:
        """Get the quality multiplier for value calculation."""
        return PRODUCT_QUALITY_MULTIPLIERS[self.quality]
    
    @property
    def freshness_multiplier(self) -> float:
        """
        Get the freshness multiplier for value calculation.
        
        Fresh products (>0.8) get full value.
        Stale products (<0.3) lose significant value.
        """
        if self.freshness >= 0.8:
            return 1.0
        elif self.freshness >= 0.5:
            return 0.85
        elif self.freshness >= 0.3:
            return 0.7
        else:
            return 0.5
    
    @property
    def unit_value(self) -> int:
        """Get the value per unit."""
        return int(
            self.base_price * 
            self.quality_multiplier * 
            self.freshness_multiplier
        )
    
    @property
    def total_value(self) -> int:
        """Get the total value (unit value × quantity)."""
        return self.unit_value * self.quantity
    
    @property
    def is_spoiled(self) -> bool:
        """Check if the product is spoiled (unsellable)."""
        return self.freshness <= 0.0
    
    @property
    def quality_stars(self) -> int:
        """Get quality as number of stars (1-4)."""
        return {
            ProductQuality.BASIC: 1,
            ProductQuality.GOOD: 2,
            ProductQuality.PREMIUM: 3,
            ProductQuality.ARTISAN: 4,
        }[self.quality]
    
    @property
    def display_name(self) -> str:
        """Get the display name with quality."""
        quality_prefix = {
            ProductQuality.BASIC: "",
            ProductQuality.GOOD: "Good ",
            ProductQuality.PREMIUM: "Premium ",
            ProductQuality.ARTISAN: "Artisan ",
        }[self.quality]
        
        type_name = self.type.value.capitalize()
        return f"{quality_prefix}{type_name}"
    
    # =========================================================================
    # Update Methods
    # =========================================================================
    
    def update(self, hours_passed: float) -> None:
        """
        Update freshness based on elapsed time.
        
        Args:
            hours_passed: Number of game hours that have passed
        """
        # Products lose freshness over time (rates defined in constants.PRODUCT_FRESHNESS_DECAY_RATES)
        decay = PRODUCT_FRESHNESS_DECAY_RATES.get(self.type.value, 0.02) * hours_passed
        self.freshness = max(0.0, self.freshness - decay)
    
    def stack(self, other: Product) -> bool:
        """
        Stack another product onto this one.
        
        Products can only stack if they're the same type and quality.
        
        Args:
            other: The product to stack
            
        Returns:
            True if stacking was successful
        """
        if other.type != self.type or other.quality != self.quality:
            return False
        
        # Average the freshness weighted by quantity
        total_quantity = self.quantity + other.quantity
        self.freshness = (
            (self.freshness * self.quantity + other.freshness * other.quantity) /
            total_quantity
        )
        self.quantity = total_quantity
        return True
    
    def split(self, amount: int) -> Product | None:
        """
        Split off a portion of this product stack.
        
        Args:
            amount: Number of units to split off
            
        Returns:
            New Product with the split amount, or None if invalid
        """
        if amount <= 0 or amount >= self.quantity:
            return None
        
        new_product = Product(
            type=self.type,
            quality=self.quality,
            quantity=amount,
            freshness=self.freshness,
            source_animal_id=self.source_animal_id,
            produced_at=self.produced_at,
        )
        
        self.quantity -= amount
        return new_product
    
    # =========================================================================
    # Class Methods
    # =========================================================================
    
    @classmethod
    def create_from_animal(
        cls,
        animal_type,  # AnimalType - avoiding circular import
        care_quality: float,
        building_bonus: float = 1.0,
        current_time: float = 0.0,
    ) -> Product:
        """
        Create a product from an animal based on care quality.
        
        Args:
            animal_type: The type of animal producing
            care_quality: The animal's care quality (0.0 to 1.0)
            building_bonus: Production bonus from building level
            current_time: Current game time in hours
            
        Returns:
            A new Product with quality based on care
        """
        from ..core.constants import ANIMAL_PRODUCTS, HEALTH_QUALITY_THRESHOLDS

        product_type = ANIMAL_PRODUCTS[animal_type]

        # Determine quality based on care
        quality = ProductQuality.BASIC
        for q in [ProductQuality.ARTISAN, ProductQuality.PREMIUM, ProductQuality.GOOD]:
            if care_quality >= HEALTH_QUALITY_THRESHOLDS[q]:
                quality = q
                break
        
        return cls(
            type=product_type,
            quality=quality,
            quantity=1,
            freshness=1.0,
            produced_at=current_time,
        )
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "quality": self.quality.value,
            "quantity": self.quantity,
            "freshness": self.freshness,
            "source_animal_id": self.source_animal_id,
            "produced_at": self.produced_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Product:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            type=ProductType(data["type"]),
            quality=ProductQuality(data["quality"]),
            quantity=data.get("quantity", 1),
            freshness=data.get("freshness", 1.0),
            source_animal_id=data.get("source_animal_id", ""),
            produced_at=data.get("produced_at", 0.0),
        )
    
    def __str__(self) -> str:
        return f"{self.display_name} x{self.quantity} ({self.freshness:.0%} fresh)"
    
    def __repr__(self) -> str:
        return f"Product(type={self.type}, quality={self.quality}, qty={self.quantity})"
