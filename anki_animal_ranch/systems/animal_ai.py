"""
Animal AI system - handles animal behaviors like wandering.
"""

from __future__ import annotations

from ..utils.logger import get_logger
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..rendering.sprite import AnimalSprite

logger = get_logger(__name__)


@dataclass
class WanderingBehavior:
    """
    Simple wandering behavior for animals.
    
    Animals pick a random point within their bounds and walk to it,
    then idle for a bit before picking a new target.
    """
    
    # Bounds the animal can wander in (world coordinates)
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 2.0
    max_y: float = 2.0
    
    # Movement
    speed: float = 0.5  # Tiles per second
    
    # Timing
    idle_time_min: float = 2.0  # Minimum seconds to idle
    idle_time_max: float = 5.0  # Maximum seconds to idle
    
    # State
    target_x: float = 0.0
    target_y: float = 0.0
    is_moving: bool = False
    idle_timer: float = 0.0
    
    def set_bounds(self, min_x: float, min_y: float, max_x: float, max_y: float) -> None:
        """Set the wandering bounds."""
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
    
    def pick_new_target(self) -> None:
        """Pick a new random target within bounds."""
        # Add small margin to keep animals away from fence edges
        margin = 0.3
        self.target_x = random.uniform(self.min_x + margin, self.max_x - margin)
        self.target_y = random.uniform(self.min_y + margin, self.max_y - margin)
        self.is_moving = True
    
    def start_idle(self) -> None:
        """Start idling for a random duration."""
        self.is_moving = False
        self.idle_timer = random.uniform(self.idle_time_min, self.idle_time_max)
    
    def update(self, current_x: float, current_y: float, delta_seconds: float) -> tuple[float, float, str]:
        """
        Update the wandering behavior.
        
        Args:
            current_x: Current X position
            current_y: Current Y position
            delta_seconds: Time elapsed
            
        Returns:
            Tuple of (new_x, new_y, direction) where direction is 'idle', 'north', 'south', 'east', 'west'
        """
        if not self.is_moving:
            # Idling
            self.idle_timer -= delta_seconds
            if self.idle_timer <= 0:
                self.pick_new_target()
            return (current_x, current_y, "idle")
        
        # Moving toward target
        dx = self.target_x - current_x
        dy = self.target_y - current_y
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < 0.1:
            # Reached target, start idling
            self.start_idle()
            return (self.target_x, self.target_y, "idle")
        
        # Move toward target
        move_distance = self.speed * delta_seconds
        if move_distance >= distance:
            # Will arrive this frame
            self.start_idle()
            return (self.target_x, self.target_y, "idle")
        
        # Partial movement
        ratio = move_distance / distance
        new_x = current_x + dx * ratio
        new_y = current_y + dy * ratio
        
        # Determine direction for animation
        if abs(dx) > abs(dy):
            direction = "east" if dx > 0 else "west"
        else:
            direction = "south" if dy > 0 else "north"
        
        return (new_x, new_y, direction)


class AnimalAI:
    """
    Manages AI behaviors for all animals in the game.
    """
    
    def __init__(self):
        self._behaviors: dict[str, WanderingBehavior] = {}
        self._sprites: dict[str, AnimalSprite] = {}
    
    def register_animal(
        self,
        animal_id: str,
        sprite: AnimalSprite,
        bounds: tuple[float, float, float, float],
    ) -> None:
        """
        Register an animal for AI management.
        
        Args:
            animal_id: Unique animal ID
            sprite: The animal's sprite
            bounds: (min_x, min_y, max_x, max_y) wandering bounds
        """
        behavior = WanderingBehavior()
        behavior.set_bounds(*bounds)
        
        # Start at a random position within bounds and idle
        behavior.target_x = sprite.world_x
        behavior.target_y = sprite.world_y
        behavior.start_idle()
        
        self._behaviors[animal_id] = behavior
        self._sprites[animal_id] = sprite
        
        logger.debug(f"Registered animal {animal_id} with bounds {bounds}")
    
    def unregister_animal(self, animal_id: str) -> None:
        """Remove an animal from AI management."""
        self._behaviors.pop(animal_id, None)
        self._sprites.pop(animal_id, None)
    
    def update(self, delta_seconds: float) -> None:
        """
        Update all animal behaviors.
        
        Args:
            delta_seconds: Time elapsed in seconds
        """
        for animal_id, behavior in self._behaviors.items():
            sprite = self._sprites.get(animal_id)
            if sprite is None:
                continue
            
            # Update behavior
            new_x, new_y, direction = behavior.update(
                sprite.world_x,
                sprite.world_y,
                delta_seconds,
            )
            
            # Update sprite position
            sprite.set_world_pos(new_x, new_y)
            
            # Update animation direction (when we have animations)
            # For now, we could change placeholder color based on direction
    
    def set_animal_bounds(self, animal_id: str, bounds: tuple[float, float, float, float]) -> None:
        """Update an animal's wandering bounds."""
        if animal_id in self._behaviors:
            self._behaviors[animal_id].set_bounds(*bounds)
