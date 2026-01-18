"""
Camera system for the isometric view.

Handles panning, zooming, and view bounds.
"""

from __future__ import annotations

from ..utils.logger import get_logger
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QTransform

from ..core.constants import (
    DEFAULT_ZOOM,
    MAX_ZOOM,
    MIN_ZOOM,
    TILE_HEIGHT,
    TILE_WIDTH,
    ZOOM_STEP,
)
from ..utils.math_utils import screen_to_world, world_to_screen

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QGraphicsView

logger = get_logger(__name__)


@dataclass
class CameraBounds:
    """Defines the boundaries the camera can view."""
    min_x: float = -1000
    min_y: float = -1000
    max_x: float = 10000
    max_y: float = 10000
    
    def clamp(self, x: float, y: float) -> tuple[float, float]:
        """Clamp a position to within bounds."""
        x = max(self.min_x, min(self.max_x, x))
        y = max(self.min_y, min(self.max_y, y))
        return (x, y)


class Camera:
    """
    Camera controller for the isometric view.
    
    Manages:
    - Zoom level
    - Pan position
    - View boundaries
    - Smooth transitions
    """
    
    def __init__(self, view: QGraphicsView | None = None):
        """
        Initialize the camera.
        
        Args:
            view: The QGraphicsView to control (can be set later)
        """
        self._view = view
        
        # Zoom state
        self._zoom = DEFAULT_ZOOM
        self._target_zoom = DEFAULT_ZOOM
        
        # Position (center of view in scene coordinates)
        self._position = QPointF(0, 0)
        self._target_position = QPointF(0, 0)
        
        # Bounds
        self._bounds = CameraBounds()
        
        # Smooth transitions (disabled for now - causes unexpected drift)
        self._smooth_factor = 0.15  # 0-1, higher = faster
        self._use_smooth = False  # Disabled to prevent camera drift bugs
        
        # Panning state
        self._is_panning = False
        self._pan_start: QPointF | None = None
        self._pan_start_scene: QPointF | None = None
    
    @property
    def view(self) -> QGraphicsView | None:
        return self._view
    
    @view.setter
    def view(self, value: QGraphicsView | None) -> None:
        self._view = value
        if value is not None:
            self._apply_transform()
    
    @property
    def zoom(self) -> float:
        return self._zoom
    
    @zoom.setter
    def zoom(self, value: float) -> None:
        self._target_zoom = max(MIN_ZOOM, min(MAX_ZOOM, value))
        if not self._use_smooth:
            self._zoom = self._target_zoom
            self._apply_transform()
    
    @property
    def position(self) -> QPointF:
        return QPointF(self._position)
    
    @position.setter
    def position(self, value: QPointF) -> None:
        x, y = self._bounds.clamp(value.x(), value.y())
        self._target_position = QPointF(x, y)
        if not self._use_smooth:
            self._position = self._target_position
            self._apply_view_center()
    
    @property
    def bounds(self) -> CameraBounds:
        return self._bounds
    
    @bounds.setter
    def bounds(self, value: CameraBounds) -> None:
        self._bounds = value
        # Re-clamp current position
        x, y = self._bounds.clamp(self._position.x(), self._position.y())
        self._position = QPointF(x, y)
        self._target_position = QPointF(x, y)
    
    # =========================================================================
    # Zoom Controls
    # =========================================================================
    
    def zoom_in(self, steps: int = 1) -> None:
        """Zoom in by the specified number of steps."""
        self.zoom = self._target_zoom + (ZOOM_STEP * steps)
    
    def zoom_out(self, steps: int = 1) -> None:
        """Zoom out by the specified number of steps."""
        self.zoom = self._target_zoom - (ZOOM_STEP * steps)
    
    def zoom_at(self, zoom: float, screen_point: QPointF) -> None:
        """
        Zoom toward/away from a specific screen point.
        
        This keeps the point under the cursor stationary during zoom.
        
        Args:
            zoom: Target zoom level
            screen_point: Point in view coordinates to zoom toward
        """
        if self._view is None:
            return
        
        # Get scene point before zoom
        scene_point = self._view.mapToScene(screen_point.toPoint())
        
        # Apply zoom
        self.zoom = zoom
        
        # Calculate offset to keep scene_point at same screen position
        if self._use_smooth:
            # Will be handled in update()
            pass
        else:
            self._apply_transform()
            # Recenter on the scene point
            new_screen = self._view.mapFromScene(scene_point)
            delta = screen_point - QPointF(new_screen)
            self.pan(-delta.x(), -delta.y())
    
    def reset_zoom(self) -> None:
        """Reset zoom to default level."""
        self.zoom = DEFAULT_ZOOM
    
    # =========================================================================
    # Pan Controls
    # =========================================================================
    
    def pan(self, dx: float, dy: float) -> None:
        """
        Pan the camera by the specified screen pixels.
        
        Args:
            dx: Horizontal pan (positive = right)
            dy: Vertical pan (positive = down)
        """
        # Convert screen delta to scene delta (accounting for zoom)
        scene_dx = dx / self._zoom
        scene_dy = dy / self._zoom
        
        new_x = self._position.x() + scene_dx
        new_y = self._position.y() + scene_dy
        
        # Clamp to bounds
        new_x, new_y = self._bounds.clamp(new_x, new_y)
        
        # Update both position and target to prevent smooth drift
        self._position = QPointF(new_x, new_y)
        self._target_position = QPointF(new_x, new_y)
        self._apply_view_center()
    
    def pan_to_world(self, world_x: float, world_y: float) -> None:
        """
        Pan to center on a world position.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
        """
        screen_x, screen_y = world_to_screen(world_x, world_y)
        self.position = QPointF(screen_x, screen_y)
    
    def start_pan(self, screen_point: QPointF) -> None:
        """Start a drag pan operation."""
        self._is_panning = True
        self._pan_start = screen_point
        if self._view:
            self._pan_start_scene = self._view.mapToScene(screen_point.toPoint())
    
    def update_pan(self, screen_point: QPointF) -> None:
        """Update drag pan with new mouse position."""
        if not self._is_panning or self._pan_start is None:
            return
        
        delta = screen_point - self._pan_start
        self._pan_start = screen_point
        
        # Pan in opposite direction of drag
        self.pan(-delta.x(), -delta.y())
    
    def end_pan(self) -> None:
        """End a drag pan operation."""
        self._is_panning = False
        self._pan_start = None
        self._pan_start_scene = None
    
    # =========================================================================
    # Following
    # =========================================================================
    
    def follow(self, world_x: float, world_y: float, immediate: bool = False) -> None:
        """
        Follow a target position.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            immediate: If True, snap immediately instead of smooth follow
        """
        screen_x, screen_y = world_to_screen(world_x, world_y)
        self._target_position = QPointF(screen_x, screen_y)
        
        if immediate or not self._use_smooth:
            self._position = self._target_position
            self._apply_view_center()
    
    # =========================================================================
    # Update & Apply
    # =========================================================================
    
    def update(self, delta_ms: int) -> None:
        """
        Update camera for smooth transitions.
        
        Should be called each frame.
        
        Args:
            delta_ms: Milliseconds since last update
        """
        if not self._use_smooth:
            return
        
        # Calculate lerp factor based on time
        t = min(1.0, self._smooth_factor * (delta_ms / 16.0))
        
        # Smooth zoom
        if abs(self._zoom - self._target_zoom) > 0.001:
            self._zoom = self._lerp(self._zoom, self._target_zoom, t)
            self._apply_transform()
        
        # Smooth position
        if (abs(self._position.x() - self._target_position.x()) > 0.1 or
            abs(self._position.y() - self._target_position.y()) > 0.1):
            self._position = QPointF(
                self._lerp(self._position.x(), self._target_position.x(), t),
                self._lerp(self._position.y(), self._target_position.y(), t),
            )
            self._apply_view_center()
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation."""
        return a + (b - a) * t
    
    def _apply_transform(self) -> None:
        """Apply current zoom to the view."""
        if self._view is None:
            return
        
        transform = QTransform()
        transform.scale(self._zoom, self._zoom)
        self._view.setTransform(transform)
    
    def _apply_view_center(self) -> None:
        """Center the view on current position."""
        if self._view is None:
            return
        
        self._view.centerOn(self._position)
    
    # =========================================================================
    # Utility
    # =========================================================================
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        """
        Convert screen coordinates to world coordinates.
        
        Accounts for current camera transform.
        """
        if self._view is None:
            return screen_to_world(screen_x, screen_y)
        
        # Map from view to scene
        scene_point = self._view.mapToScene(int(screen_x), int(screen_y))
        
        # Convert scene to world
        return screen_to_world(scene_point.x(), scene_point.y())
    
    def get_visible_world_bounds(self) -> tuple[float, float, float, float]:
        """
        Get the world coordinate bounds currently visible.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) in world coordinates
        """
        if self._view is None:
            return (0, 0, 10, 10)
        
        # Get viewport rect in scene coordinates
        viewport_rect = self._view.mapToScene(self._view.viewport().rect()).boundingRect()
        
        # Convert corners to world coordinates
        corners = [
            screen_to_world(viewport_rect.left(), viewport_rect.top()),
            screen_to_world(viewport_rect.right(), viewport_rect.top()),
            screen_to_world(viewport_rect.left(), viewport_rect.bottom()),
            screen_to_world(viewport_rect.right(), viewport_rect.bottom()),
        ]
        
        min_x = min(c[0] for c in corners)
        max_x = max(c[0] for c in corners)
        min_y = min(c[1] for c in corners)
        max_y = max(c[1] for c in corners)
        
        return (min_x, min_y, max_x, max_y)
    
    def set_bounds_from_grid(self, width: int, height: int, padding: int = 2) -> None:
        """
        Set camera bounds based on grid size.
        
        Args:
            width: Grid width in tiles
            height: Grid height in tiles
            padding: Extra tiles of padding around edges
        """
        # In isometric projection, we need to check all 4 corners to find true bounds
        # Top corner (0, 0)
        top = world_to_screen(-padding, -padding)
        # Right corner (width, 0)
        right = world_to_screen(width + padding, -padding)
        # Bottom corner (width, height)
        bottom = world_to_screen(width + padding, height + padding)
        # Left corner (0, height)
        left = world_to_screen(-padding, height + padding)
        
        # Find actual min/max from all corners
        min_x = min(top[0], right[0], bottom[0], left[0])
        max_x = max(top[0], right[0], bottom[0], left[0])
        min_y = min(top[1], right[1], bottom[1], left[1])
        max_y = max(top[1], right[1], bottom[1], left[1])
        
        self._bounds = CameraBounds(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
        )
