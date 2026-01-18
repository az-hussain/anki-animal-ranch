"""
A* pathfinding for character movement.

Provides efficient pathfinding on the tile grid.
"""

from __future__ import annotations

import heapq
from .logger import get_logger
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..rendering.tile_grid import TileGrid

logger = get_logger(__name__)


@dataclass(order=True)
class PathNode:
    """A node in the pathfinding search."""
    f_score: float  # Total estimated cost (g + h)
    position: tuple[int, int] = field(compare=False)
    g_score: float = field(compare=False)  # Cost from start
    parent: PathNode | None = field(default=None, compare=False)


def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    """
    Calculate heuristic distance (Manhattan distance).
    
    Args:
        a: Start position (x, y)
        b: End position (x, y)
        
    Returns:
        Estimated distance
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    is_walkable: Callable[[int, int], bool],
    max_iterations: int = 1000,
    allow_diagonal: bool = False,
) -> list[tuple[int, int]] | None:
    """
    Find a path from start to goal using A*.
    
    Args:
        start: Starting position (x, y)
        goal: Target position (x, y)
        is_walkable: Function that returns True if a tile is walkable
        max_iterations: Maximum search iterations
        allow_diagonal: Whether diagonal movement is allowed
        
    Returns:
        List of positions from start to goal, or None if no path found
    """
    # Quick checks
    if start == goal:
        return [start]
    
    if not is_walkable(goal[0], goal[1]):
        # Find nearest walkable tile to goal
        goal = _find_nearest_walkable(goal, is_walkable)
        if goal is None:
            return None
    
    # Directions (orthogonal only by default)
    directions = [
        (0, -1),   # North
        (1, 0),    # East
        (0, 1),    # South
        (-1, 0),   # West
    ]
    
    if allow_diagonal:
        directions.extend([
            (-1, -1),  # NW
            (1, -1),   # NE
            (1, 1),    # SE
            (-1, 1),   # SW
        ])
    
    # Diagonal movement cost
    diagonal_cost = 1.414  # sqrt(2)
    
    # Initialize
    start_node = PathNode(
        f_score=heuristic(start, goal),
        position=start,
        g_score=0,
    )
    
    open_set: list[PathNode] = [start_node]
    closed_set: set[tuple[int, int]] = set()
    g_scores: dict[tuple[int, int], float] = {start: 0}
    
    iterations = 0
    
    while open_set and iterations < max_iterations:
        iterations += 1
        
        # Get node with lowest f_score
        current = heapq.heappop(open_set)
        
        if current.position == goal:
            # Found the path - reconstruct it
            return _reconstruct_path(current)
        
        if current.position in closed_set:
            continue
        
        closed_set.add(current.position)
        
        # Explore neighbors
        for dx, dy in directions:
            neighbor_pos = (current.position[0] + dx, current.position[1] + dy)
            
            if neighbor_pos in closed_set:
                continue
            
            if not is_walkable(neighbor_pos[0], neighbor_pos[1]):
                continue
            
            # Calculate cost
            is_diagonal = dx != 0 and dy != 0
            move_cost = diagonal_cost if is_diagonal else 1.0
            
            tentative_g = current.g_score + move_cost
            
            if neighbor_pos in g_scores and tentative_g >= g_scores[neighbor_pos]:
                continue
            
            g_scores[neighbor_pos] = tentative_g
            f_score = tentative_g + heuristic(neighbor_pos, goal)
            
            neighbor_node = PathNode(
                f_score=f_score,
                position=neighbor_pos,
                g_score=tentative_g,
                parent=current,
            )
            
            heapq.heappush(open_set, neighbor_node)
    
    # No path found
    logger.debug(f"No path found from {start} to {goal} after {iterations} iterations")
    return None


def _reconstruct_path(end_node: PathNode) -> list[tuple[int, int]]:
    """Reconstruct path from end node."""
    path = []
    current: PathNode | None = end_node
    
    while current is not None:
        path.append(current.position)
        current = current.parent
    
    path.reverse()
    return path


def _find_nearest_walkable(
    target: tuple[int, int],
    is_walkable: Callable[[int, int], bool],
    max_radius: int = 5,
) -> tuple[int, int] | None:
    """
    Find the nearest walkable tile to a target.
    
    Uses a spiral search pattern.
    """
    for radius in range(1, max_radius + 1):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) == radius or abs(dy) == radius:
                    pos = (target[0] + dx, target[1] + dy)
                    if is_walkable(pos[0], pos[1]):
                        return pos
    return None


def smooth_path(path: list[tuple[int, int]]) -> list[tuple[float, float]]:
    """
    Convert a grid path to smooth world coordinates.
    
    Adds 0.5 to center on tiles and can smooth corners.
    
    Args:
        path: List of grid coordinates
        
    Returns:
        List of world coordinates (centered on tiles)
    """
    if not path:
        return []
    
    return [(x + 0.5, y + 0.5) for x, y in path]


def simplify_path(path: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Simplify a path by removing unnecessary waypoints.
    
    Keeps only waypoints where direction changes.
    
    Args:
        path: Original path
        
    Returns:
        Simplified path
    """
    if len(path) <= 2:
        return path
    
    simplified = [path[0]]
    
    for i in range(1, len(path) - 1):
        prev = path[i - 1]
        curr = path[i]
        next_pos = path[i + 1]
        
        # Check if direction changes
        dir1 = (curr[0] - prev[0], curr[1] - prev[1])
        dir2 = (next_pos[0] - curr[0], next_pos[1] - curr[1])
        
        if dir1 != dir2:
            simplified.append(curr)
    
    simplified.append(path[-1])
    return simplified


class PathFollower:
    """
    Manages following a path over time.
    
    Provides smooth interpolation between waypoints.
    """
    
    def __init__(self, speed: float = 2.0):
        """
        Initialize the path follower.
        
        Args:
            speed: Movement speed in tiles per second
        """
        self.speed = speed
        self._path: list[tuple[float, float]] = []
        self._current_index = 0
        self._position = (0.0, 0.0)
        self._is_moving = False
    
    @property
    def is_moving(self) -> bool:
        return self._is_moving
    
    @property
    def position(self) -> tuple[float, float]:
        return self._position
    
    @property
    def current_target(self) -> tuple[float, float] | None:
        if self._current_index < len(self._path):
            return self._path[self._current_index]
        return None
    
    @property
    def direction(self) -> str:
        """Get current facing direction."""
        target = self.current_target
        if target is None:
            return "south"
        
        dx = target[0] - self._position[0]
        dy = target[1] - self._position[1]
        
        if abs(dx) > abs(dy):
            return "east" if dx > 0 else "west"
        else:
            return "south" if dy > 0 else "north"
    
    def set_path(self, path: list[tuple[int, int]], start_pos: tuple[float, float] | None = None) -> None:
        """
        Set a new path to follow.
        
        Args:
            path: Grid path to follow
            start_pos: Starting position (defaults to first path point)
        """
        self._path = smooth_path(path)
        self._current_index = 0
        
        if start_pos is not None:
            self._position = start_pos
        elif self._path:
            self._position = self._path[0]
            self._current_index = 1
        
        self._is_moving = len(self._path) > 1
    
    def stop(self) -> None:
        """Stop following the path."""
        self._is_moving = False
        self._path = []
        self._current_index = 0
    
    def update(self, delta_seconds: float) -> tuple[float, float]:
        """
        Update position along the path.
        
        Args:
            delta_seconds: Time elapsed in seconds
            
        Returns:
            New position
        """
        if not self._is_moving or self._current_index >= len(self._path):
            self._is_moving = False
            return self._position
        
        target = self._path[self._current_index]
        
        # Calculate distance to target
        dx = target[0] - self._position[0]
        dy = target[1] - self._position[1]
        distance = (dx * dx + dy * dy) ** 0.5
        
        # Calculate movement this frame
        move_distance = self.speed * delta_seconds
        
        if move_distance >= distance:
            # Reached waypoint
            self._position = target
            self._current_index += 1
            
            if self._current_index >= len(self._path):
                self._is_moving = False
            else:
                # Continue with remaining movement
                remaining = move_distance - distance
                if remaining > 0:
                    return self.update(remaining / self.speed)
        else:
            # Partial movement
            ratio = move_distance / distance
            self._position = (
                self._position[0] + dx * ratio,
                self._position[1] + dy * ratio,
            )
        
        return self._position
