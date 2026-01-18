"""
Player model - Manages player inventory.

Simplified to just handle inventory - no position or movement
since there's no player sprite on the farm.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Player:
    """
    Represents the player's inventory and stats.
    
    Note: This is a simplified player model - there's no visual
    player sprite on the farm, so no position/movement tracking.
    
    Attributes:
        inventory: Items collected (product_key -> quantity)
    """
    
    # Simple inventory (product_type_quality -> quantity, e.g. "egg_good" -> 5)
    inventory: dict[str, int] = field(default_factory=dict)
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def inventory_count(self) -> int:
        """Get total items in inventory."""
        return sum(self.inventory.values())
    
    # =========================================================================
    # Inventory
    # =========================================================================
    
    def add_to_inventory(self, item_type: str, quantity: int = 1) -> int:
        """
        Add items to inventory.
        
        Args:
            item_type: Type of item to add (e.g. "egg_good")
            quantity: Amount to add
            
        Returns:
            Number of items added
        """
        if quantity > 0:
            self.inventory[item_type] = self.inventory.get(item_type, 0) + quantity
        return quantity
    
    def remove_from_inventory(self, item_type: str, quantity: int = 1) -> int:
        """
        Remove items from inventory.
        
        Args:
            item_type: Type of item to remove
            quantity: Amount to remove
            
        Returns:
            Number of items actually removed
        """
        current = self.inventory.get(item_type, 0)
        actual_quantity = min(quantity, current)
        
        if actual_quantity > 0:
            self.inventory[item_type] = current - actual_quantity
            if self.inventory[item_type] <= 0:
                del self.inventory[item_type]
        
        return actual_quantity
    
    def has_item(self, item_type: str, quantity: int = 1) -> bool:
        """Check if player has items in inventory."""
        return self.inventory.get(item_type, 0) >= quantity
    
    def clear_inventory(self) -> dict[str, int]:
        """
        Clear all items from inventory.
        
        Returns:
            Dictionary of cleared items
        """
        items = self.inventory.copy()
        self.inventory.clear()
        return items
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "inventory": self.inventory.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Player:
        """Deserialize from dictionary."""
        player = cls()
        player.inventory = data.get("inventory", {})
        return player
    
    def __str__(self) -> str:
        return f"Player ({self.inventory_count} items)"
    
    def __repr__(self) -> str:
        return f"Player(inventory_count={self.inventory_count})"
