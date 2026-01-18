"""
Mathematical utilities for isometric rendering.

Provides coordinate conversion functions between:
- Screen coordinates (pixels)
- World coordinates (isometric tile units)
- Grid coordinates (integer tile indices)
"""

from __future__ import annotations

import math
from typing import Tuple

from ..core.constants import TILE_HEIGHT, TILE_WIDTH


def world_to_screen(world_x: float, world_y: float) -> Tuple[float, float]:
    """
    Convert world (isometric) coordinates to screen (pixel) coordinates.
    
    In isometric projection:
    - X axis goes right and down
    - Y axis goes left and down
    
    Args:
        world_x: X position in world units
        world_y: Y position in world units
        
    Returns:
        Tuple of (screen_x, screen_y) in pixels
    """
    screen_x = (world_x - world_y) * (TILE_WIDTH / 2)
    screen_y = (world_x + world_y) * (TILE_HEIGHT / 2)
    return (screen_x, screen_y)


def screen_to_world(screen_x: float, screen_y: float) -> Tuple[float, float]:
    """
    Convert screen (pixel) coordinates to world (isometric) coordinates.
    
    This is the inverse of world_to_screen.
    
    Args:
        screen_x: X position in pixels
        screen_y: Y position in pixels
        
    Returns:
        Tuple of (world_x, world_y) in world units
    """
    world_x = (screen_x / (TILE_WIDTH / 2) + screen_y / (TILE_HEIGHT / 2)) / 2
    world_y = (screen_y / (TILE_HEIGHT / 2) - screen_x / (TILE_WIDTH / 2)) / 2
    return (world_x, world_y)


def world_to_grid(world_x: float, world_y: float) -> Tuple[int, int]:
    """
    Convert world coordinates to grid (tile) coordinates.
    
    Args:
        world_x: X position in world units
        world_y: Y position in world units
        
    Returns:
        Tuple of (grid_x, grid_y) as integers
    """
    return (int(math.floor(world_x)), int(math.floor(world_y)))


def grid_to_world(grid_x: int, grid_y: int) -> Tuple[float, float]:
    """
    Convert grid (tile) coordinates to world coordinates.
    
    Returns the center of the tile.
    
    Args:
        grid_x: X tile index
        grid_y: Y tile index
        
    Returns:
        Tuple of (world_x, world_y) at tile center
    """
    return (float(grid_x) + 0.5, float(grid_y) + 0.5)


def grid_to_screen(grid_x: int, grid_y: int) -> Tuple[float, float]:
    """
    Convert grid coordinates directly to screen coordinates.
    
    Returns the screen position of the tile's top corner (for rendering).
    
    Args:
        grid_x: X tile index
        grid_y: Y tile index
        
    Returns:
        Tuple of (screen_x, screen_y) in pixels
    """
    return world_to_screen(float(grid_x), float(grid_y))


def screen_to_grid(screen_x: float, screen_y: float) -> Tuple[int, int]:
    """
    Convert screen coordinates to grid coordinates.
    
    Useful for determining which tile was clicked.
    
    Args:
        screen_x: X position in pixels
        screen_y: Y position in pixels
        
    Returns:
        Tuple of (grid_x, grid_y) as integers
    """
    world = screen_to_world(screen_x, screen_y)
    return world_to_grid(world[0], world[1])


def distance(
    x1: float, y1: float,
    x2: float, y2: float
) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        x1, y1: First point
        x2, y2: Second point
        
    Returns:
        Distance between the points
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def manhattan_distance(
    x1: int, y1: int,
    x2: int, y2: int
) -> int:
    """
    Calculate Manhattan distance between two grid points.
    
    Useful for pathfinding heuristics.
    
    Args:
        x1, y1: First grid point
        x2, y2: Second grid point
        
    Returns:
        Manhattan distance
    """
    return abs(x2 - x1) + abs(y2 - y1)


def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        a: Start value
        b: End value
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated value
    """
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value to a range.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def normalize_angle(angle: float) -> float:
    """
    Normalize an angle to the range [0, 2π).
    
    Args:
        angle: Angle in radians
        
    Returns:
        Normalized angle
    """
    two_pi = 2 * math.pi
    while angle < 0:
        angle += two_pi
    while angle >= two_pi:
        angle -= two_pi
    return angle


def angle_between(
    x1: float, y1: float,
    x2: float, y2: float
) -> float:
    """
    Calculate angle from point 1 to point 2.
    
    Args:
        x1, y1: Source point
        x2, y2: Target point
        
    Returns:
        Angle in radians
    """
    return math.atan2(y2 - y1, x2 - x1)


def direction_from_angle(angle: float) -> str:
    """
    Convert an angle to a cardinal direction.
    
    Args:
        angle: Angle in radians
        
    Returns:
        Direction string: 'north', 'south', 'east', 'west',
        'northeast', 'northwest', 'southeast', 'southwest'
    """
    angle = normalize_angle(angle)
    
    # 8 directions, each covering 45 degrees (π/4 radians)
    pi = math.pi
    eighth = pi / 4
    
    if angle < eighth or angle >= 7 * eighth:
        return 'east'
    elif angle < 3 * eighth:
        return 'southeast'
    elif angle < 5 * eighth:
        return 'south'
    elif angle < 7 * eighth:
        return 'southwest'
    elif angle < 9 * eighth:
        return 'west'
    elif angle < 11 * eighth:
        return 'northwest'
    elif angle < 13 * eighth:
        return 'north'
    else:
        return 'northeast'


def get_sorting_key(world_x: float, world_y: float, z: float = 0) -> float:
    """
    Calculate a sorting key for isometric depth ordering.
    
    Objects with higher keys should be drawn later (on top).
    
    Args:
        world_x: X position in world units
        world_y: Y position in world units
        z: Z position (height) for multi-level sorting
        
    Returns:
        Sorting key value
    """
    # In isometric, objects further "down-right" are drawn later
    # We add x + y as the base, with z for vertical ordering
    return world_x + world_y + (z * 0.001)
