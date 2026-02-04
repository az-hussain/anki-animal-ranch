"""
Farm model - Main container for all farm state.

The Farm class is the central data structure that contains
all game state: animals, buildings, etc.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Iterator

from ..core.constants import (
    ANIMAL_FEED_MAP,
    FEED_CONSUMPTION_PER_DAY,
    FEED_PRICES,
    INITIAL_MONEY,
    ZONE_UNLOCK_COSTS,
    AnimalType,
    BuildingType,
    FeedType,
    Season,
)
from .animal import Animal
from .building import Building
from .decoration import Decoration
from .player import Player
from .product import Product


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


@dataclass
class FarmStatistics:
    """
    Tracks lifetime farm statistics.
    
    Used for achievements and leaderboard ranking.
    """
    total_money_earned: int = 0
    total_animals_raised: int = 0
    total_animals_sold: int = 0
    total_products_sold: int = 0
    total_cards_answered: int = 0
    highest_money_held: int = 0
    days_played: int = 0
    
    # Per-type statistics
    animals_raised_by_type: dict[str, int] = field(default_factory=dict)
    animals_sold_by_type: dict[str, int] = field(default_factory=dict)
    products_sold_by_type: dict[str, int] = field(default_factory=dict)
    
    def record_sale(self, amount: int, item_type: str, is_animal: bool = False) -> None:
        """Record a sale transaction."""
        self.total_money_earned += amount
        
        if is_animal:
            self.total_animals_sold += 1
            self.animals_sold_by_type[item_type] = \
                self.animals_sold_by_type.get(item_type, 0) + 1
        else:
            self.total_products_sold += 1
            self.products_sold_by_type[item_type] = \
                self.products_sold_by_type.get(item_type, 0) + 1
    
    def record_animal_raised(self, animal_type: str) -> None:
        """Record an animal reaching maturity."""
        self.total_animals_raised += 1
        self.animals_raised_by_type[animal_type] = \
            self.animals_raised_by_type.get(animal_type, 0) + 1
    
    def update_highest_money(self, current: int) -> None:
        """Update the highest money record if applicable."""
        self.highest_money_held = max(self.highest_money_held, current)
    
    def to_dict(self) -> dict:
        return {
            "total_money_earned": self.total_money_earned,
            "total_animals_raised": self.total_animals_raised,
            "total_animals_sold": self.total_animals_sold,
            "total_products_sold": self.total_products_sold,
            "total_cards_answered": self.total_cards_answered,
            "highest_money_held": self.highest_money_held,
            "days_played": self.days_played,
            "animals_raised_by_type": self.animals_raised_by_type.copy(),
            "animals_sold_by_type": self.animals_sold_by_type.copy(),
            "products_sold_by_type": self.products_sold_by_type.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> FarmStatistics:
        stats = cls()
        stats.total_money_earned = data.get("total_money_earned", 0)
        stats.total_animals_raised = data.get("total_animals_raised", 0)
        stats.total_animals_sold = data.get("total_animals_sold", 0)
        stats.total_products_sold = data.get("total_products_sold", 0)
        stats.total_cards_answered = data.get("total_cards_answered", 0)
        stats.highest_money_held = data.get("highest_money_held", 0)
        stats.days_played = data.get("days_played", 0)
        stats.animals_raised_by_type = data.get("animals_raised_by_type", {})
        stats.animals_sold_by_type = data.get("animals_sold_by_type", {})
        stats.products_sold_by_type = data.get("products_sold_by_type", {})
        return stats


@dataclass
class Farm:
    """
    Main farm state container.
    
    This class holds all game state and provides methods for
    managing farm entities.
    
    Attributes:
        id: Unique farm identifier
        name: Farm name (for display)
        owner_id: User ID of the farm owner
        money: Current money balance
        unlocked_zones: Number of zones unlocked
        player: The player's inventory
        animals: All animals on the farm (id -> Animal)
        buildings: All buildings (id -> Building)
        decorations: All decorations (id -> Decoration)
        products: Stored products (id -> Product)
        statistics: Lifetime statistics
    """
    
    id: str = field(default_factory=generate_id)
    name: str = "My Farm"
    owner_id: str = ""
    money: int = INITIAL_MONEY
    unlocked_zones: int = 1
    
    player: Player = field(default_factory=Player)
    
    animals: dict[str, Animal] = field(default_factory=dict)
    buildings: dict[str, Building] = field(default_factory=dict)
    decorations: dict[str, Decoration] = field(default_factory=dict)
    products: dict[str, Product] = field(default_factory=dict)
    
    # Feed inventory (FeedType.value -> quantity)
    feed_inventory: dict[str, int] = field(default_factory=dict)
    
    statistics: FarmStatistics = field(default_factory=FarmStatistics)
    
    # =========================================================================
    # Money Management
    # =========================================================================
    
    def add_money(self, amount: int, reason: str = "") -> bool:
        """
        Add money to the farm balance.
        
        Args:
            amount: Amount to add (positive)
            reason: Reason for the transaction (for logging)
            
        Returns:
            True if successful
        """
        if amount < 0:
            return False
        
        self.money += amount
        self.statistics.update_highest_money(self.money)
        return True
    
    def spend_money(self, amount: int, reason: str = "") -> bool:
        """
        Spend money from the farm balance.
        
        Args:
            amount: Amount to spend (positive)
            reason: Reason for the transaction
            
        Returns:
            True if successful (had enough money)
        """
        if amount < 0 or amount > self.money:
            return False
        
        self.money -= amount
        return True
    
    def can_afford(self, amount: int) -> bool:
        """Check if the farm can afford an expense."""
        return self.money >= amount
    
    # =========================================================================
    # Feed Management
    # =========================================================================
    
    def get_feed_amount(self, feed_type: FeedType) -> int:
        """Get the current amount of a specific feed type."""
        return self.feed_inventory.get(feed_type.value, 0)
    
    def add_feed(self, feed_type: FeedType, amount: int) -> None:
        """Add feed to inventory."""
        current = self.feed_inventory.get(feed_type.value, 0)
        self.feed_inventory[feed_type.value] = current + amount
    
    def consume_feed(self, feed_type: FeedType, amount: int) -> bool:
        """
        Consume feed from inventory.
        
        Returns:
            True if there was enough feed, False if not enough
        """
        current = self.feed_inventory.get(feed_type.value, 0)
        if current >= amount:
            self.feed_inventory[feed_type.value] = current - amount
            return True
        # Consume what we have
        self.feed_inventory[feed_type.value] = 0
        return False
    
    def buy_feed(self, feed_type: FeedType, bundle_size: int) -> bool:
        """
        Buy a bundle of feed.
        
        Args:
            feed_type: Type of feed to buy
            bundle_size: Number of units to buy (100, 250, 500)
            
        Returns:
            True if purchase successful
        """
        base_price = FEED_PRICES.get(feed_type, 50)
        # Price is per 100 units, scale accordingly
        total_cost = (base_price * bundle_size) // 100
        
        if not self.spend_money(total_cost, f"Buy {bundle_size} {feed_type.value}"):
            return False
        
        self.add_feed(feed_type, bundle_size)
        return True
    
    def get_feed_status(self) -> dict[FeedType, dict]:
        """
        Get feed status for all feed types.
        
        Returns:
            Dict with feed type -> {amount, animals_count, days_remaining}
        """
        status = {}
        
        for feed_type in FeedType:
            amount = self.get_feed_amount(feed_type)
            
            # Count animals that eat this feed
            animal_count = sum(
                1 for animal in self.animals.values()
                if ANIMAL_FEED_MAP.get(animal.type) == feed_type
            )
            
            # Calculate days remaining
            daily_consumption = FEED_CONSUMPTION_PER_DAY.get(feed_type, 1) * animal_count
            days_remaining = amount / daily_consumption if daily_consumption > 0 else float('inf')
            
            status[feed_type] = {
                "amount": amount,
                "animal_count": animal_count,
                "daily_consumption": daily_consumption,
                "days_remaining": days_remaining,
            }
        
        return status
    
    def is_feed_low(self, feed_type: FeedType, threshold_days: int = 10) -> bool:
        """Check if feed is running low (less than threshold days remaining)."""
        status = self.get_feed_status().get(feed_type, {})
        days_remaining = status.get("days_remaining", float('inf'))
        return days_remaining < threshold_days and status.get("animal_count", 0) > 0
    
    # =========================================================================
    # Zone Management
    # =========================================================================
    
    @property
    def next_zone_cost(self) -> int:
        """Get the cost to unlock the next zone."""
        if self.unlocked_zones >= len(ZONE_UNLOCK_COSTS):
            return 0
        return ZONE_UNLOCK_COSTS[self.unlocked_zones]
    
    @property
    def can_unlock_zone(self) -> bool:
        """Check if another zone can be unlocked."""
        return (
            self.unlocked_zones < len(ZONE_UNLOCK_COSTS) and
            self.can_afford(self.next_zone_cost)
        )
    
    def unlock_zone(self) -> bool:
        """
        Unlock the next zone.
        
        Returns:
            True if successful
        """
        if not self.can_unlock_zone:
            return False
        
        cost = self.next_zone_cost
        if not self.spend_money(cost, "Zone unlock"):
            return False
        
        self.unlocked_zones += 1
        return True
    
    # =========================================================================
    # Animal Management
    # =========================================================================
    
    def add_animal(self, animal: Animal) -> bool:
        """
        Add an animal to the farm.
        
        Args:
            animal: The animal to add
            
        Returns:
            True if successful
        """
        if animal.id in self.animals:
            return False
        
        self.animals[animal.id] = animal
        return True
    
    def remove_animal(self, animal_id: str) -> Animal | None:
        """
        Remove an animal from the farm.
        
        Args:
            animal_id: ID of the animal to remove
            
        Returns:
            The removed animal, or None if not found
        """
        animal = self.animals.pop(animal_id, None)
        
        # Also remove from any building
        if animal and animal.building_id:
            building = self.buildings.get(animal.building_id)
            if building:
                building.remove_animal(animal_id)
        
        return animal
    
    def get_animal(self, animal_id: str) -> Animal | None:
        """Get an animal by ID."""
        return self.animals.get(animal_id)
    
    def get_animals_in_building(self, building_id: str) -> list[Animal]:
        """Get all animals in a specific building."""
        return [
            animal for animal in self.animals.values()
            if animal.building_id == building_id
        ]
    
    def get_animals_by_type(self, animal_type: AnimalType) -> list[Animal]:
        """Get all animals of a specific type."""
        return [
            animal for animal in self.animals.values()
            if animal.type == animal_type
        ]
    
    # =========================================================================
    # Building Management
    # =========================================================================
    
    def add_building(self, building: Building) -> bool:
        """
        Add a building to the farm.
        
        Args:
            building: The building to add
            
        Returns:
            True if successful
        """
        if building.id in self.buildings:
            return False
        
        # TODO: Check for tile collisions
        
        self.buildings[building.id] = building
        return True
    
    def remove_building(self, building_id: str) -> Building | None:
        """
        Remove a building from the farm.
        
        Note: This doesn't handle animals in the building!
        
        Args:
            building_id: ID of the building to remove
            
        Returns:
            The removed building, or None if not found
        """
        return self.buildings.pop(building_id, None)
    
    def get_building(self, building_id: str) -> Building | None:
        """Get a building by ID."""
        return self.buildings.get(building_id)
    
    def get_buildings_by_type(self, building_type: BuildingType) -> list[Building]:
        """Get all buildings of a specific type."""
        return [
            b for b in self.buildings.values()
            if b.type == building_type
        ]
    
    def get_building_at(self, x: int, y: int) -> Building | None:
        """Get the building at a specific tile position."""
        for building in self.buildings.values():
            if (x, y) in building.tiles_occupied:
                return building
        return None
    
    # =========================================================================
    # Decoration Management
    # =========================================================================
    
    def add_decoration(self, decoration: Decoration) -> bool:
        """
        Add a decoration to the farm.
        
        Args:
            decoration: The decoration to add
            
        Returns:
            True if successful
        """
        if decoration.id in self.decorations:
            return False
        
        self.decorations[decoration.id] = decoration
        return True
    
    def remove_decoration(self, decoration_id: str) -> Decoration | None:
        """
        Remove a decoration from the farm.
        
        Args:
            decoration_id: ID of the decoration to remove
            
        Returns:
            The removed decoration, or None if not found
        """
        return self.decorations.pop(decoration_id, None)
    
    def get_decoration(self, decoration_id: str) -> Decoration | None:
        """Get a decoration by ID."""
        return self.decorations.get(decoration_id)
    
    # =========================================================================
    # Product Management
    # =========================================================================
    
    def add_product(self, product: Product) -> bool:
        """
        Add a product to storage.
        
        Attempts to stack with existing products of same type/quality.
        """
        # Try to stack with existing
        for existing in self.products.values():
            if existing.type == product.type and existing.quality == product.quality:
                if existing.stack(product):
                    return True
        
        # Add as new
        self.products[product.id] = product
        return True
    
    def remove_product(self, product_id: str) -> Product | None:
        """Remove a product from storage."""
        return self.products.pop(product_id, None)
    
    def get_product(self, product_id: str) -> Product | None:
        """Get a product by ID."""
        return self.products.get(product_id)
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> dict:
        """Serialize the entire farm state to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "money": self.money,
            "unlocked_zones": self.unlocked_zones,
            "player": self.player.to_dict(),
            "animals": {aid: a.to_dict() for aid, a in self.animals.items()},
            "buildings": {bid: b.to_dict() for bid, b in self.buildings.items()},
            "decorations": {did: d.to_dict() for did, d in self.decorations.items()},
            "products": {pid: p.to_dict() for pid, p in self.products.items()},
            "feed_inventory": self.feed_inventory.copy(),
            "statistics": self.statistics.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Farm:
        """Deserialize a farm from a dictionary."""
        farm = cls(
            id=data.get("id", generate_id()),
            name=data.get("name", "My Farm"),
            owner_id=data.get("owner_id", ""),
            money=data.get("money", INITIAL_MONEY),
            unlocked_zones=data.get("unlocked_zones", 1),
        )
        
        # Note: current_time is no longer stored in Farm
        # Time is derived from farm.statistics.total_cards_answered
        
        if "player" in data:
            farm.player = Player.from_dict(data["player"])
        
        if "animals" in data:
            farm.animals = {
                aid: Animal.from_dict(adata)
                for aid, adata in data["animals"].items()
            }
        
        if "buildings" in data:
            farm.buildings = {
                bid: Building.from_dict(bdata)
                for bid, bdata in data["buildings"].items()
            }
        
        if "decorations" in data:
            farm.decorations = {
                did: Decoration.from_dict(ddata)
                for did, ddata in data["decorations"].items()
            }
        
        # Note: "workers" and "vehicles" keys in old save files are ignored
        
        if "products" in data:
            farm.products = {
                pid: Product.from_dict(pdata)
                for pid, pdata in data["products"].items()
            }
        
        if "feed_inventory" in data:
            farm.feed_inventory = data["feed_inventory"].copy()
        
        if "statistics" in data:
            farm.statistics = FarmStatistics.from_dict(data["statistics"])
        
        return farm
    
    @classmethod
    def create_new(cls, name: str = "My Farm", owner_id: str = "") -> Farm:
        """
        Create a new farm with default starting state.
        
        Args:
            name: Name for the farm
            owner_id: Owner's user ID
            
        Returns:
            A new Farm instance with starting resources
        """
        return cls(
            name=name,
            owner_id=owner_id,
        )
    
    def __str__(self) -> str:
        return f"Farm '{self.name}' (${self.money}, {len(self.animals)} animals)"
    
    def __repr__(self) -> str:
        return f"Farm(id={self.id!r}, name={self.name!r}, money={self.money})"
