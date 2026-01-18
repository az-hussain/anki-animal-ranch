"""
Growth and Production System.

Handles animal aging, maturation, and product generation
based on game time advancement.
"""

from __future__ import annotations

from ..utils.logger import get_logger
import random
from typing import TYPE_CHECKING

from ..core.constants import (
    ANIMAL_FEED_MAP,
    ANIMAL_GROWTH_RATES,
    ANIMAL_PRODUCTION_INTERVALS,
    ANIMAL_PRODUCTS,
    FEED_CONSUMPTION_PER_DAY,
    GROWTH_STAGE_THRESHOLDS,
    HEALTH_DECAY_RATE_UNFED,
    HEALTH_QUALITY_THRESHOLDS,
    HEALTH_RECOVERY_RATE_FED,
    HOURS_PER_DAY,
    AnimalType,
    Events,
    FeedType,
    GrowthStage,
    ProductQuality,
    ProductType,
)
from ..core.event_bus import event_bus

if TYPE_CHECKING:
    from ..models.animal import Animal
    from ..models.farm import Farm
    from ..models.product import Product

logger = get_logger(__name__)


class GrowthSystem:
    """
    Manages animal growth and product generation.
    
    This system:
    - Ages animals based on time passed
    - Tracks maturity progression
    - Generates products when animals are ready
    - Publishes events for UI updates
    """
    
    def __init__(self, farm: Farm):
        """
        Initialize the growth system.
        
        Args:
            farm: The farm to manage
        """
        self.farm = farm
        self._pending_products: list[tuple[str, ProductType, int]] = []  # (animal_id, product_type, quantity)
        self._accumulated_hours: float = 0.0  # Track partial hours for daily feed consumption
    
    def update(self, hours_passed: float) -> list[dict]:
        """
        Update all animals for elapsed time.
        
        Args:
            hours_passed: Number of game hours that have passed
            
        Returns:
            List of events that occurred (for UI feedback)
        """
        events = []
        
        # Handle daily feed consumption
        self._accumulated_hours += hours_passed
        while self._accumulated_hours >= HOURS_PER_DAY:
            self._accumulated_hours -= HOURS_PER_DAY
            self._consume_daily_feed()
        
        for animal in self.farm.animals.values():
            animal_events = self._update_animal(animal, hours_passed)
            events.extend(animal_events)
        
        return events
    
    def _consume_daily_feed(self) -> None:
        """
        Consume one day's worth of feed for all animals.
        
        Called once per game day. Updates animal hunger based on feed availability.
        """
        # Group animals by feed type
        animals_by_feed: dict[FeedType, list] = {}
        for animal in self.farm.animals.values():
            feed_type = ANIMAL_FEED_MAP.get(animal.type)
            if feed_type:
                if feed_type not in animals_by_feed:
                    animals_by_feed[feed_type] = []
                animals_by_feed[feed_type].append(animal)
        
        # Consume feed for each type
        for feed_type, animals in animals_by_feed.items():
            consumption_per_animal = FEED_CONSUMPTION_PER_DAY.get(feed_type, 1)
            total_needed = consumption_per_animal * len(animals)
            available = self.farm.get_feed_amount(feed_type)
            
            if available >= total_needed:
                # Enough feed for everyone
                self.farm.consume_feed(feed_type, total_needed)
                for animal in animals:
                    animal.hunger = 1.0  # Full
            elif available > 0:
                # Partial feed - distribute evenly
                self.farm.consume_feed(feed_type, available)
                feed_ratio = available / total_needed
                for animal in animals:
                    animal.hunger = max(0.3, feed_ratio)  # At least 30% if some feed
                logger.warning(f"Low on {feed_type.value}! Only {available}/{total_needed} available")
            else:
                # No feed - animals go hungry
                for animal in animals:
                    animal.hunger = max(0.0, animal.hunger - 0.3)  # Lose 30% hunger per day unfed
                logger.warning(f"Out of {feed_type.value}! Animals are hungry!")
    
    def _update_animal(self, animal: Animal, hours_passed: float) -> list[dict]:
        """
        Update a single animal.
        
        Args:
            animal: The animal to update
            hours_passed: Hours of game time passed
            
        Returns:
            List of events for this animal
        """
        events = []
        
        # Get building for production bonus
        building = self.farm.buildings.get(animal.building_id) if animal.building_id else None
        production_bonus = building.production_bonus if building else 1.0
        
        # Update age
        animal.age_hours += hours_passed
        
        # Update health based on hunger
        if animal.hunger < 0.3:
            # Starving - health decays
            health_decay = HEALTH_DECAY_RATE_UNFED * hours_passed * (1 - animal.hunger / 0.3)
            animal.health = max(0.1, animal.health - health_decay)  # Min 10% health
        elif animal.hunger > 0.5:
            # Well-fed - health recovers
            health_recovery = HEALTH_RECOVERY_RATE_FED * hours_passed
            animal.health = min(1.0, animal.health + health_recovery)
        
        # Update maturity (growth)
        old_stage = animal.growth_stage
        growth_rate = ANIMAL_GROWTH_RATES.get(animal.type, 0.01)
        
        # Growth is affected by health (not happiness anymore - simplified)
        care_modifier = animal.health
        effective_growth = growth_rate * care_modifier * hours_passed
        
        animal.maturity = min(1.0, animal.maturity + effective_growth)
        
        # Check for stage change
        new_stage = animal.growth_stage
        if new_stage != old_stage:
            events.append({
                "type": "growth_stage_changed",
                "animal_id": animal.id,
                "animal_type": animal.type.value,
                "old_stage": old_stage.value,
                "new_stage": new_stage.value,
            })
            logger.info(f"{animal.type.value} grew to {new_stage.value}!")
            
            # Publish event
            event_bus.publish(
                Events.ANIMAL_MATURED,
                animal_id=animal.id,
                animal_type=animal.type,
                stage=new_stage,
            )
        
        # Check for production (only mature animals)
        if animal.is_mature:
            production_interval = ANIMAL_PRODUCTION_INTERVALS.get(animal.type, 6)
            animal.hours_since_production += hours_passed
            
            if animal.hours_since_production >= production_interval:
                # Produce! Quality based on health
                product = self._produce(animal, production_bonus)
                if product:
                    events.append({
                        "type": "product_produced",
                        "animal_id": animal.id,
                        "animal_type": animal.type.value,
                        "product_type": product["type"],
                        "quantity": product["quantity"],
                        "quality": product["quality"],
                    })
                
                animal.hours_since_production = 0.0
        
        return events
    
    def _produce(self, animal: Animal, bonus: float = 1.0) -> dict | None:
        """
        Generate a product from an animal.
        
        Args:
            animal: The producing animal
            bonus: Production bonus multiplier
            
        Returns:
            Dict with product info, or None if production failed
        """
        product_type = ANIMAL_PRODUCTS.get(animal.type)
        if not product_type:
            return None
        
        # Determine quality based on animal health
        quality = self._get_quality_from_health(animal.health)
        
        # Base quantity (could be affected by building upgrades, etc.)
        base_quantity = 1
        
        # Higher health = chance for extra (replaces happiness bonus)
        if animal.health > 0.9 and random.random() < 0.3:
            base_quantity += 1
        
        # Apply bonus
        quantity = int(base_quantity * bonus)
        quantity = max(1, quantity)
        
        # Add to farm inventory with quality suffix
        # Format: "egg_good", "milk_premium", etc.
        product_key = f"{product_type.value}_{quality.value}"
        current = self.farm.player.inventory.get(product_key, 0)
        self.farm.player.inventory[product_key] = current + quantity
        
        quality_emoji = self._get_quality_emoji(quality)
        logger.info(f"{animal.type.value} produced {quantity} {quality_emoji} {quality.value} {product_type.value}!")
        
        # Publish event
        event_bus.publish(
            Events.ANIMAL_PRODUCED,
            animal_id=animal.id,
            animal_type=animal.type,
            product_type=product_type,
            quantity=quantity,
            quality=quality,
        )
        
        return {
            "type": product_type.value,
            "quantity": quantity,
            "quality": quality.value,
        }
    
    def _get_quality_from_health(self, health: float) -> ProductQuality:
        """
        Determine product quality based on animal health.
        
        Args:
            health: Animal health (0.0 to 1.0)
            
        Returns:
            ProductQuality tier
        """
        # Check from highest to lowest quality
        for quality in [ProductQuality.ARTISAN, ProductQuality.PREMIUM, ProductQuality.GOOD]:
            threshold = HEALTH_QUALITY_THRESHOLDS.get(quality, 0.0)
            if health >= threshold:
                return quality
        return ProductQuality.BASIC
    
    def _get_quality_emoji(self, quality: ProductQuality) -> str:
        """Get emoji representation of quality."""
        return {
            ProductQuality.BASIC: "⭐",
            ProductQuality.GOOD: "⭐⭐",
            ProductQuality.PREMIUM: "⭐⭐⭐",
            ProductQuality.ARTISAN: "⭐⭐⭐⭐",
        }.get(quality, "⭐")
    
    def feed_animal(self, animal_id: str) -> bool:
        """
        Feed an animal to restore hunger.
        
        Args:
            animal_id: ID of animal to feed
            
        Returns:
            True if feeding was successful
        """
        animal = self.farm.animals.get(animal_id)
        if not animal:
            return False
        
        animal.hunger = min(1.0, animal.hunger + 0.5)
        
        return True
    
    def get_production_status(self, animal_id: str) -> dict:
        """
        Get production status for an animal.
        
        Args:
            animal_id: ID of animal
            
        Returns:
            Dict with production info
        """
        animal = self.farm.animals.get(animal_id)
        if not animal:
            return {}
        
        interval = ANIMAL_PRODUCTION_INTERVALS.get(animal.type, 6)
        progress = animal.hours_since_production / interval if interval > 0 else 0
        
        return {
            "is_mature": animal.is_mature,
            "maturity": animal.maturity,
            "growth_stage": animal.growth_stage.value,
            "production_progress": min(1.0, progress),
            "hours_until_production": max(0, interval - animal.hours_since_production),
            "product_type": ANIMAL_PRODUCTS.get(animal.type, ProductType.EGG).value,
        }
