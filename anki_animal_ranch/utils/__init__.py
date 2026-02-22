"""
Utility functions for Anki Animal Ranch.
"""

from .logger import (
    get_log_file_path,
    get_logger,
    get_recent_logs,
    setup_file_logging,
    setup_logging,
)
from .math_utils import (
    angle_between,
    clamp,
    direction_from_angle,
    distance,
    get_sorting_key,
    grid_to_screen,
    grid_to_world,
    lerp,
    manhattan_distance,
    normalize_angle,
    screen_to_grid,
    screen_to_world,
    world_to_grid,
    world_to_screen,
)
__all__ = [
    # Logging
    "setup_logging",
    "setup_file_logging",
    "get_logger",
    "get_log_file_path",
    "get_recent_logs",
    # Math utilities
    "world_to_screen",
    "screen_to_world",
    "world_to_grid",
    "grid_to_world",
    "grid_to_screen",
    "screen_to_grid",
    "distance",
    "manhattan_distance",
    "lerp",
    "clamp",
    "normalize_angle",
    "angle_between",
    "direction_from_angle",
    "get_sorting_key",
]
