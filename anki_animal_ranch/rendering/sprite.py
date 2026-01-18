"""
Sprite base class and animation system.

Provides the foundation for all animated game objects
rendered in the isometric view.
"""

from __future__ import annotations

from ..utils.logger import get_logger
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject, QStyleOptionGraphicsItem, QWidget

from ..core.constants import (
    DECORATION_INFO,
    FRAME_TIME_MS,
    TILE_HEIGHT,
    TILE_WIDTH,
    DecorationType,
    Direction,
)
from ..utils.math_utils import get_sorting_key, world_to_screen

logger = get_logger(__name__)


class SpriteLayer(Enum):
    """Z-ordering layers for sprites."""
    GROUND = 0       # Ground tiles
    SHADOWS = 1      # Shadow effects
    BUILDINGS = 2    # Buildings (base)
    ITEMS = 3        # Items on ground
    ANIMALS = 4      # Animals
    CHARACTERS = 5   # Player and workers
    EFFECTS = 6      # Particle effects
    UI = 7           # UI elements in world space


@dataclass
class AnimationFrame:
    """A single frame of animation."""
    pixmap: QPixmap | None = None
    duration_ms: int = 100  # Duration to show this frame
    offset_x: int = 0       # Offset from sprite origin
    offset_y: int = 0


@dataclass
class Animation:
    """An animation sequence."""
    name: str
    frames: list[AnimationFrame] = field(default_factory=list)
    loop: bool = True
    on_complete: Callable[[], None] | None = None
    
    @property
    def total_duration(self) -> int:
        """Total duration of the animation in ms."""
        return sum(f.duration_ms for f in self.frames)
    
    @property
    def frame_count(self) -> int:
        return len(self.frames)


class Sprite(QGraphicsObject):
    """
    Base class for all animated sprites in the game.
    
    Sprites are positioned in world coordinates and automatically
    converted to screen coordinates for rendering.
    
    Features:
    - Automatic world-to-screen coordinate conversion
    - Animation system with multiple named animations
    - Automatic Z-ordering based on position
    - Placeholder rendering when no pixmap is set
    """
    
    def __init__(
        self,
        world_x: float = 0.0,
        world_y: float = 0.0,
        width: int = 32,
        height: int = 32,
        layer: SpriteLayer = SpriteLayer.ITEMS,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(parent)
        
        # World position (isometric coordinates)
        self._world_x = world_x
        self._world_y = world_y
        self._world_z = 0.0  # Height offset
        
        # Sprite dimensions
        self._width = width
        self._height = height
        
        # Layer for Z-ordering
        self._layer = layer
        
        # Animation system
        self._animations: dict[str, Animation] = {}
        self._current_animation: str = ""
        self._current_frame: int = 0
        self._frame_time: int = 0  # Time spent on current frame
        self._is_playing: bool = False
        
        # Placeholder color (used when no sprite loaded)
        self._placeholder_color = QColor(200, 200, 200)
        self._placeholder_shape = "rect"  # rect, circle, diamond
        
        # Current pixmap (from animation or static)
        self._static_pixmap: QPixmap | None = None
        
        # Update screen position
        self._update_screen_position()
        self._update_z_value()
        
        # Enable item change notifications
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
    
    # =========================================================================
    # Position Properties
    # =========================================================================
    
    @property
    def world_x(self) -> float:
        return self._world_x
    
    @world_x.setter
    def world_x(self, value: float) -> None:
        if self._world_x != value:
            self._world_x = value
            self._update_screen_position()
            self._update_z_value()
    
    @property
    def world_y(self) -> float:
        return self._world_y
    
    @world_y.setter
    def world_y(self, value: float) -> None:
        if self._world_y != value:
            self._world_y = value
            self._update_screen_position()
            self._update_z_value()
    
    @property
    def world_z(self) -> float:
        return self._world_z
    
    @world_z.setter
    def world_z(self, value: float) -> None:
        if self._world_z != value:
            self._world_z = value
            self._update_z_value()
    
    @property
    def world_pos(self) -> tuple[float, float]:
        return (self._world_x, self._world_y)
    
    def set_world_pos(self, x: float, y: float) -> None:
        """Set world position."""
        if self._world_x != x or self._world_y != y:
            self._world_x = x
            self._world_y = y
            self._update_screen_position()
            self._update_z_value()
    
    def _update_screen_position(self) -> None:
        """Update screen position from world coordinates."""
        screen_x, screen_y = world_to_screen(self._world_x, self._world_y)
        # Center the sprite on the tile
        screen_x -= self._width / 2
        screen_y -= self._height  # Anchor at bottom
        screen_y -= self._world_z * TILE_HEIGHT  # Apply height offset
        self.setPos(screen_x, screen_y)
    
    def _update_z_value(self) -> None:
        """Update Z-value for proper draw order."""
        # Combine layer and position-based sorting
        base_z = self._layer.value * 10000
        position_z = get_sorting_key(self._world_x, self._world_y, self._world_z)
        self.setZValue(base_z + position_z)
    
    # =========================================================================
    # Rendering
    # =========================================================================
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the sprite."""
        return QRectF(0, 0, self._width, self._height)
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Paint the sprite."""
        # Get current pixmap from animation or static
        pixmap = self._get_current_pixmap()
        
        if pixmap is not None and not pixmap.isNull():
            # Draw the pixmap
            painter.drawPixmap(0, 0, self._width, self._height, pixmap)
        else:
            # Draw placeholder
            self._draw_placeholder(painter)
    
    def _get_current_pixmap(self) -> QPixmap | None:
        """Get the current pixmap to display."""
        # Check animation first
        if self._current_animation and self._current_animation in self._animations:
            anim = self._animations[self._current_animation]
            if anim.frames and 0 <= self._current_frame < len(anim.frames):
                return anim.frames[self._current_frame].pixmap
        
        # Fall back to static pixmap
        return self._static_pixmap
    
    def _draw_placeholder(self, painter: QPainter) -> None:
        """Draw a placeholder shape when no sprite is loaded."""
        painter.setPen(QPen(self._placeholder_color.darker(120), 2))
        painter.setBrush(QBrush(self._placeholder_color))
        
        rect = self.boundingRect()
        
        if self._placeholder_shape == "circle":
            painter.drawEllipse(rect)
        elif self._placeholder_shape == "diamond":
            # Isometric diamond
            points = [
                QPointF(rect.width() / 2, 0),
                QPointF(rect.width(), rect.height() / 2),
                QPointF(rect.width() / 2, rect.height()),
                QPointF(0, rect.height() / 2),
            ]
            painter.drawPolygon(QPolygonF(points))
        else:  # rect
            painter.drawRect(rect)
    
    def set_placeholder(self, color: QColor | str, shape: str = "rect") -> None:
        """
        Set the placeholder appearance.
        
        Args:
            color: Color for the placeholder
            shape: Shape type ("rect", "circle", "diamond")
        """
        if isinstance(color, str):
            color = QColor(color)
        self._placeholder_color = color
        self._placeholder_shape = shape
        self.update()
    
    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Set a static pixmap (no animation)."""
        self._static_pixmap = pixmap
        self.update()
    
    # =========================================================================
    # Animation System
    # =========================================================================
    
    def add_animation(self, animation: Animation) -> None:
        """Add an animation to the sprite."""
        self._animations[animation.name] = animation
    
    def play_animation(self, name: str, restart: bool = False) -> bool:
        """
        Play a named animation.
        
        Args:
            name: Name of the animation to play
            restart: If True, restart even if already playing this animation
            
        Returns:
            True if animation started successfully
        """
        if name not in self._animations:
            logger.warning(f"Animation '{name}' not found")
            return False
        
        if name == self._current_animation and self._is_playing and not restart:
            return True
        
        self._current_animation = name
        self._current_frame = 0
        self._frame_time = 0
        self._is_playing = True
        self.update()
        return True
    
    def stop_animation(self) -> None:
        """Stop the current animation."""
        self._is_playing = False
    
    def update_animation(self, delta_ms: int) -> None:
        """
        Update animation state.
        
        Should be called each frame with the elapsed time.
        
        Args:
            delta_ms: Milliseconds since last update
        """
        if not self._is_playing or not self._current_animation:
            return
        
        anim = self._animations.get(self._current_animation)
        if not anim or not anim.frames:
            return
        
        self._frame_time += delta_ms
        current_frame_duration = anim.frames[self._current_frame].duration_ms
        
        # Advance frames as needed
        while self._frame_time >= current_frame_duration:
            self._frame_time -= current_frame_duration
            self._current_frame += 1
            
            # Handle animation end
            if self._current_frame >= len(anim.frames):
                if anim.loop:
                    self._current_frame = 0
                else:
                    self._current_frame = len(anim.frames) - 1
                    self._is_playing = False
                    if anim.on_complete:
                        anim.on_complete()
                    break
            
            current_frame_duration = anim.frames[self._current_frame].duration_ms
        
        self.update()
    
    @property
    def current_animation_name(self) -> str:
        return self._current_animation
    
    @property
    def is_animation_playing(self) -> bool:
        return self._is_playing


class TileSprite(Sprite):
    """
    Specialized sprite for ground tiles.
    
    Tiles are rendered as isometric diamonds.
    """
    
    def __init__(
        self,
        grid_x: int,
        grid_y: int,
        parent: QGraphicsItem | None = None,
    ):
        # Tiles are positioned at grid coordinates
        super().__init__(
            world_x=float(grid_x),
            world_y=float(grid_y),
            width=TILE_WIDTH,
            height=TILE_HEIGHT,
            layer=SpriteLayer.GROUND,
            parent=parent,
        )
        
        self.grid_x = grid_x
        self.grid_y = grid_y
        self._show_border = False  # Hide grid lines by default
        self._is_locked = False  # Whether tile is in a locked zone
        
        # Tile-specific placeholder
        self.set_placeholder(QColor(90, 140, 90), "diamond")  # Grass green
    
    @property
    def show_border(self) -> bool:
        return self._show_border
    
    @show_border.setter
    def show_border(self, value: bool) -> None:
        if self._show_border != value:
            self._show_border = value
            self.update()
    
    @property
    def is_locked(self) -> bool:
        return self._is_locked
    
    @is_locked.setter
    def is_locked(self, value: bool) -> None:
        if self._is_locked != value:
            self._is_locked = value
            self.update()
    
    def _update_screen_position(self) -> None:
        """Tiles position differently - anchor at top of diamond."""
        screen_x, screen_y = world_to_screen(self._world_x, self._world_y)
        # Tiles anchor at the top point of the diamond
        screen_x -= TILE_WIDTH / 2
        self.setPos(screen_x, screen_y)
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Paint the tile with optional border and locked overlay."""
        rect = self.boundingRect()
        
        # Draw the diamond shape
        points = [
            QPointF(rect.width() / 2, 0),
            QPointF(rect.width(), rect.height() / 2),
            QPointF(rect.width() / 2, rect.height()),
            QPointF(0, rect.height() / 2),
        ]
        polygon = QPolygonF(points)
        
        # Always draw grass green base first
        grass_color = QColor(90, 140, 90)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grass_color))
        painter.drawPolygon(polygon)
        
        # If locked, draw semi-transparent gray overlay
        if self._is_locked:
            overlay_color = QColor(60, 60, 60, 160)  # Dark gray with 60% opacity
            painter.setBrush(QBrush(overlay_color))
            painter.drawPolygon(polygon)
        
        # Draw border only if enabled (for placement mode)
        if self._show_border:
            border_color = grass_color.darker(120) if not self._is_locked else QColor(100, 100, 100)
            painter.setPen(QPen(border_color, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(polygon)


class PlacementPreviewSprite(QGraphicsItem):
    """
    Shows a preview of where a building will be placed.
    
    Displays an isometric footprint outline to show which tiles
    the building will occupy.
    """
    
    def __init__(
        self,
        footprint_width: int = 2,
        footprint_height: int = 2,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(parent)
        
        self.footprint_width = footprint_width
        self.footprint_height = footprint_height
        self._valid = True  # Whether placement is valid (green) or not (red)
        
        # Calculate bounding dimensions (make larger to ensure full drawing is visible)
        self._width = (footprint_width + footprint_height) * TILE_WIDTH
        self._height = (footprint_width + footprint_height) * TILE_HEIGHT
        
        # Position tracking
        self._grid_x = 0
        self._grid_y = 0
        
        # Z-order above tiles and buildings (needs to be visible)
        self.setZValue(500)
    
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)
    
    def set_position(self, grid_x: int, grid_y: int) -> None:
        """Set the grid position of the preview."""
        self._grid_x = grid_x
        self._grid_y = grid_y
        
        # Convert to screen coordinates (top-left corner of the footprint)
        screen_x, screen_y = world_to_screen(float(grid_x), float(grid_y))
        # Offset the bounding rect so the diamond is centered correctly
        screen_x -= self._width / 2
        screen_y -= self._height / 4
        self.setPos(screen_x, screen_y)
    
    def set_valid(self, valid: bool) -> None:
        """Set whether placement is valid (affects color)."""
        if self._valid != valid:
            self._valid = valid
            self.update()
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Paint the placement preview."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate isometric corners
        half_tile_w = TILE_WIDTH // 2
        half_tile_h = TILE_HEIGHT // 2
        
        # Center point of bounding rect
        cx = self._width / 2
        cy = self._height / 4  # Offset from top
        
        # Calculate corner positions in isometric projection
        # Top corner of the footprint diamond
        top = QPointF(cx, cy)
        # Right corner
        right = QPointF(cx + self.footprint_width * half_tile_w, 
                       cy + self.footprint_width * half_tile_h)
        # Bottom corner
        bottom = QPointF(cx + (self.footprint_width - self.footprint_height) * half_tile_w, 
                        cy + (self.footprint_width + self.footprint_height) * half_tile_h)
        # Left corner
        left = QPointF(cx - self.footprint_height * half_tile_w, 
                      cy + self.footprint_height * half_tile_h)
        
        # Choose color based on validity
        if self._valid:
            fill_color = QColor(100, 200, 100, 120)  # Green, semi-transparent
            outline_color = QColor(50, 200, 50)
        else:
            fill_color = QColor(200, 100, 100, 120)  # Red, semi-transparent
            outline_color = QColor(200, 50, 50)
        
        # Draw filled footprint
        polygon = QPolygonF([top, right, bottom, left])
        painter.setPen(QPen(outline_color, 3))
        painter.setBrush(QBrush(fill_color))
        painter.drawPolygon(polygon)
        
        # Draw grid lines within the footprint
        painter.setPen(QPen(outline_color.lighter(120), 1, Qt.PenStyle.DashLine))
        
        # Draw internal grid lines
        for i in range(1, self.footprint_width):
            # Vertical lines (going right)
            start_x = cx + i * half_tile_w
            start_y = cy + i * half_tile_h
            end_x = start_x - self.footprint_height * half_tile_w
            end_y = start_y + self.footprint_height * half_tile_h
            painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
        
        for i in range(1, self.footprint_height):
            # Horizontal lines (going left)
            start_x = cx - i * half_tile_w
            start_y = cy + i * half_tile_h
            end_x = start_x + self.footprint_width * half_tile_w
            end_y = start_y + self.footprint_width * half_tile_h
            painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))


class BuildingSprite(Sprite):
    """
    Specialized sprite for buildings.
    
    Buildings have a footprint (multiple tiles) and height.
    """
    
    def __init__(
        self,
        world_x: float,
        world_y: float,
        footprint_width: int = 2,
        footprint_height: int = 2,
        visual_height: int = 80,
        parent: QGraphicsItem | None = None,
    ):
        # Calculate visual width based on footprint
        visual_width = footprint_width * TILE_WIDTH
        
        super().__init__(
            world_x=world_x,
            world_y=world_y,
            width=visual_width,
            height=visual_height,
            layer=SpriteLayer.BUILDINGS,
            parent=parent,
        )
        
        self.footprint_width = footprint_width
        self.footprint_height = footprint_height
        
        # Building placeholder
        self.set_placeholder(QColor(139, 90, 43), "rect")  # Brown


class DecorationSprite(Sprite):
    """
    Specialized sprite for decorative items.
    
    Supports rotation with different visual appearances per direction.
    """
    
    # Color schemes for different decoration types
    DECORATION_COLORS: dict[DecorationType, dict[Direction, QColor]] = {
        # Nature & Plants
        DecorationType.HAY_BALE: {
            Direction.NORTH: QColor(218, 165, 32),
            Direction.EAST: QColor(218, 175, 52),
            Direction.SOUTH: QColor(218, 165, 32),
            Direction.WEST: QColor(198, 155, 22),
        },
        DecorationType.FLOWER_BED: {
            Direction.NORTH: QColor(255, 182, 193),
            Direction.EAST: QColor(255, 192, 203),
            Direction.SOUTH: QColor(255, 182, 193),
            Direction.WEST: QColor(245, 172, 183),
        },
        DecorationType.TREE: {
            Direction.NORTH: QColor(34, 139, 34),
            Direction.EAST: QColor(34, 139, 34),
            Direction.SOUTH: QColor(34, 139, 34),
            Direction.WEST: QColor(34, 139, 34),
        },
        DecorationType.SCARECROW: {
            Direction.NORTH: QColor(139, 90, 43),
            Direction.EAST: QColor(149, 100, 53),
            Direction.SOUTH: QColor(139, 90, 43),
            Direction.WEST: QColor(129, 80, 33),
        },
        DecorationType.PUMPKIN_PATCH: {
            Direction.NORTH: QColor(255, 140, 0),
            Direction.EAST: QColor(255, 150, 20),
            Direction.SOUTH: QColor(255, 140, 0),
            Direction.WEST: QColor(235, 120, 0),
        },
        # Farm Structures
        DecorationType.WINDMILL: {
            Direction.NORTH: QColor(180, 180, 180),
            Direction.EAST: QColor(190, 190, 190),
            Direction.SOUTH: QColor(180, 180, 180),
            Direction.WEST: QColor(170, 170, 170),
        },
        DecorationType.WATER_WELL: {
            Direction.NORTH: QColor(128, 128, 128),
            Direction.EAST: QColor(128, 128, 128),
            Direction.SOUTH: QColor(128, 128, 128),
            Direction.WEST: QColor(128, 128, 128),
        },
        DecorationType.DECORATIVE_SILO: {
            Direction.NORTH: QColor(192, 192, 192),
            Direction.EAST: QColor(192, 192, 192),
            Direction.SOUTH: QColor(192, 192, 192),
            Direction.WEST: QColor(192, 192, 192),
        },
        DecorationType.WOODEN_CART: {
            Direction.NORTH: QColor(139, 90, 43),
            Direction.EAST: QColor(149, 100, 53),
            Direction.SOUTH: QColor(139, 90, 43),
            Direction.WEST: QColor(129, 80, 33),
        },
        # Water Features
        DecorationType.POND: {
            Direction.NORTH: QColor(64, 164, 223),
            Direction.EAST: QColor(64, 164, 223),
            Direction.SOUTH: QColor(64, 164, 223),
            Direction.WEST: QColor(64, 164, 223),
        },
        DecorationType.FOUNTAIN: {
            Direction.NORTH: QColor(100, 180, 220),
            Direction.EAST: QColor(100, 180, 220),
            Direction.SOUTH: QColor(100, 180, 220),
            Direction.WEST: QColor(100, 180, 220),
        },
        DecorationType.WATER_TROUGH: {
            Direction.NORTH: QColor(139, 90, 43),
            Direction.EAST: QColor(149, 100, 53),
            Direction.SOUTH: QColor(139, 90, 43),
            Direction.WEST: QColor(129, 80, 33),
        },
        # Outdoor Living
        DecorationType.BENCH: {
            Direction.NORTH: QColor(160, 82, 45),
            Direction.EAST: QColor(170, 92, 55),
            Direction.SOUTH: QColor(160, 82, 45),
            Direction.WEST: QColor(150, 72, 35),
        },
        DecorationType.PICNIC_TABLE: {
            Direction.NORTH: QColor(160, 82, 45),
            Direction.EAST: QColor(170, 92, 55),
            Direction.SOUTH: QColor(160, 82, 45),
            Direction.WEST: QColor(150, 72, 35),
        },
        DecorationType.LAMP_POST: {
            Direction.NORTH: QColor(50, 50, 50),
            Direction.EAST: QColor(50, 50, 50),
            Direction.SOUTH: QColor(50, 50, 50),
            Direction.WEST: QColor(50, 50, 50),
        },
        # Fun Extras
        DecorationType.GARDEN_GNOME: {
            Direction.NORTH: QColor(255, 0, 0),
            Direction.EAST: QColor(255, 20, 20),
            Direction.SOUTH: QColor(255, 0, 0),
            Direction.WEST: QColor(235, 0, 0),
        },
        DecorationType.MAILBOX: {
            Direction.NORTH: QColor(70, 130, 180),
            Direction.EAST: QColor(80, 140, 190),
            Direction.SOUTH: QColor(70, 130, 180),
            Direction.WEST: QColor(60, 120, 170),
        },
        DecorationType.SIGNPOST: {
            Direction.NORTH: QColor(139, 90, 43),
            Direction.EAST: QColor(149, 100, 53),
            Direction.SOUTH: QColor(139, 90, 43),
            Direction.WEST: QColor(129, 80, 33),
        },
    }
    
    def __init__(
        self,
        world_x: float,
        world_y: float,
        decoration_type: DecorationType,
        direction: Direction = Direction.EAST,
        footprint_width: int = 1,
        footprint_height: int = 1,
        parent: QGraphicsItem | None = None,
    ):
        # Calculate visual dimensions based on footprint
        visual_width = max(footprint_width, footprint_height) * TILE_WIDTH
        visual_height = max(footprint_width, footprint_height) * TILE_HEIGHT + 40
        
        super().__init__(
            world_x=world_x,
            world_y=world_y,
            width=visual_width,
            height=visual_height,
            layer=SpriteLayer.BUILDINGS,
            parent=parent,
        )
        
        self.decoration_type = decoration_type
        self.direction = direction
        self.footprint_width = footprint_width
        self.footprint_height = footprint_height
        self.decoration_id: str | None = None
        
        # Try to load sprite image, fall back to placeholder
        if not self._load_sprite_image():
            self._update_placeholder_color()
    
    def _update_screen_position(self) -> None:
        """Position at the center of the decoration footprint."""
        screen_x, screen_y = world_to_screen(self._world_x, self._world_y)
        # Center horizontally on the tile
        screen_x -= self._width / 2
        # Anchor sprite bottom to the tile - subtract less to move DOWN on screen
        screen_y -= self._height / 2
        self.setPos(screen_x, screen_y)
    
    def _load_sprite_image(self) -> bool:
        """Try to load sprite image from assets. Returns True if successful."""
        import os
        import sys
        from pathlib import Path
        
        # Map decoration types to asset paths
        SPRITE_PATHS = {
            # Nature
            DecorationType.HAY_BALE: "decorations/nature/hay_bale.png",
            DecorationType.FLOWER_BED: "decorations/nature/flower_bed.png",
            DecorationType.TREE: "decorations/nature/tree.png",
            DecorationType.SCARECROW: "decorations/nature/scarecrow.png",
            DecorationType.PUMPKIN_PATCH: "decorations/nature/pumpkin_patch.png",
            # Structures
            DecorationType.WATER_WELL: "decorations/structures/water_well.png",
            DecorationType.WOODEN_CART: "decorations/structures/wooden_cart.png",
            DecorationType.WINDMILL: "decorations/structures/windmill.png",
            DecorationType.DECORATIVE_SILO: "decorations/structures/silo.png",
            # Water
            DecorationType.FOUNTAIN: "decorations/water/fountain.png",
            DecorationType.POND: "decorations/water/pond.png",
            DecorationType.WATER_TROUGH: "decorations/water/water_trough.png",
            # Outdoor
            DecorationType.BENCH: "decorations/outdoor/bench.png",
            DecorationType.PICNIC_TABLE: "decorations/outdoor/picnic_table.png",
            DecorationType.LAMP_POST: "decorations/outdoor/lamp_post.png",
            # Extras
            DecorationType.GARDEN_GNOME: "decorations/extras/garden_gnome.png",
            DecorationType.MAILBOX: "decorations/extras/mailbox.png",
            DecorationType.SIGNPOST: "decorations/extras/signpost.png",
        }
        
        rel_path = SPRITE_PATHS.get(self.decoration_type)
        if not rel_path:
            return False
        
        # Try multiple methods to find the assets directory
        possible_paths = []
        
        # Method 1: Relative to this file
        try:
            this_file = Path(__file__).resolve()
            possible_paths.append(this_file.parent.parent / "assets" / rel_path)
        except:
            pass
        
        # Method 2: Using the module's path
        try:
            import anki_animal_ranch
            module_dir = Path(anki_animal_ranch.__file__).parent
            possible_paths.append(module_dir / "assets" / rel_path)
        except:
            pass
        
        # Method 3: Check if running as Anki addon (numbered folder)
        try:
            for path in sys.path:
                if "addons21" in path:
                    # Try to find our addon folder
                    addons_dir = Path(path)
                    if addons_dir.is_dir():
                        for addon_dir in addons_dir.iterdir():
                            if addon_dir.is_dir():
                                test_path = addon_dir / "assets" / rel_path
                                if test_path.exists():
                                    possible_paths.insert(0, test_path)
        except:
            pass
        
        # Try each possible path
        for sprite_path in possible_paths:
            if sprite_path.exists():
                try:
                    pixmap = QPixmap(str(sprite_path))
                    if not pixmap.isNull():
                        # Update sprite dimensions to match the loaded image
                        self._width = pixmap.width()
                        self._height = pixmap.height()
                        
                        self.set_pixmap(pixmap)
                        logger.info(f"Loaded decoration sprite: {sprite_path.name} ({self._width}x{self._height})")
                        return True
                except Exception as e:
                    logger.warning(f"Error loading sprite {sprite_path}: {e}")
        
        logger.debug(f"Sprite not found for {self.decoration_type.value}, tried: {[str(p) for p in possible_paths]}")
        return False
    
    def _update_placeholder_color(self) -> None:
        """Update placeholder color based on decoration type and direction."""
        colors = self.DECORATION_COLORS.get(self.decoration_type, {})
        color = colors.get(self.direction, QColor(150, 150, 150))
        
        # Choose shape based on decoration type
        info = DECORATION_INFO.get(self.decoration_type, {})
        
        # Use different shapes for different decoration categories
        if self.decoration_type in (DecorationType.TREE, DecorationType.LAMP_POST,
                                     DecorationType.SCARECROW, DecorationType.GARDEN_GNOME,
                                     DecorationType.MAILBOX, DecorationType.SIGNPOST):
            shape = "diamond"  # Tall, narrow items
        elif self.decoration_type in (DecorationType.POND, DecorationType.WINDMILL):
            shape = "diamond"  # Large items
        else:
            shape = "diamond"  # Default
        
        self.set_placeholder(color, shape)
    
    def set_direction(self, direction: Direction) -> None:
        """Set the decoration's facing direction."""
        self.direction = direction
        self._update_placeholder_color()
        self.update()
    
    def rotate_clockwise(self) -> None:
        """Toggle between EAST and WEST facing (flip horizontally)."""
        info = DECORATION_INFO.get(self.decoration_type, {})
        if not info.get("can_rotate", False):
            return
        
        # Only two directions: EAST (default) and WEST (flipped)
        if self.direction == Direction.EAST:
            self.direction = Direction.WEST
        else:
            self.direction = Direction.EAST
        self._update_placeholder_color()
        self.update()
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Paint the decoration sprite."""
        # Check if we have a loaded pixmap - use it instead of placeholder
        pixmap = self._get_current_pixmap()
        if pixmap is not None and not pixmap.isNull():
            # Flip horizontally if facing WEST
            if self.direction == Direction.WEST:
                painter.save()
                # Flip by scaling -1 in X, translate to compensate
                painter.translate(self._width, 0)
                painter.scale(-1, 1)
                painter.drawPixmap(0, 0, self._width, self._height, pixmap)
                painter.restore()
            else:
                painter.drawPixmap(0, 0, self._width, self._height, pixmap)
            return
        
        # Fall back to placeholder drawing
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get color for current direction
        colors = self.DECORATION_COLORS.get(self.decoration_type, {})
        color = colors.get(self.direction, QColor(150, 150, 150))
        
        # Draw isometric base - matching PenSprite approach
        half_tile_w = TILE_WIDTH // 2
        half_tile_h = TILE_HEIGHT // 2
        
        # Center point of sprite, top of content area
        cx = self._width / 2
        cy = 10  # Start drawing from top like PenSprite
        
        # Calculate isometric corners (drawing DOWNWARD from cy like PenSprite)
        # Top corner
        top = QPointF(cx, cy)
        # Right corner  
        right = QPointF(cx + self.footprint_width * half_tile_w, 
                       cy + self.footprint_width * half_tile_h)
        # Bottom corner
        bottom = QPointF(cx + (self.footprint_width - self.footprint_height) * half_tile_w,
                        cy + (self.footprint_width + self.footprint_height) * half_tile_h)
        # Left corner
        left = QPointF(cx - self.footprint_height * half_tile_w,
                      cy + self.footprint_height * half_tile_h)
        
        # Draw ground/shadow
        ground_poly = QPolygonF([top, right, bottom, left])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color.darker(130)))
        painter.drawPolygon(ground_poly)
        
        # Center of the base for placing objects
        base_center_x = cx + (self.footprint_width - self.footprint_height) * half_tile_w / 2
        base_center_y = cy + (self.footprint_width + self.footprint_height) * half_tile_h / 2
        
        # Draw main body (elevated)
        body_height = 25 if self.footprint_width == 1 and self.footprint_height == 1 else 40
        
        # Special shapes for certain decorations
        if self.decoration_type == DecorationType.TREE:
            # Draw tree trunk
            trunk_rect = QRectF(base_center_x - 5, base_center_y - 35, 10, 25)
            painter.setBrush(QBrush(QColor(101, 67, 33)))
            painter.drawRect(trunk_rect)
            
            # Draw foliage (circle)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(base_center_x, base_center_y - 50), 20, 20)
            
        elif self.decoration_type == DecorationType.LAMP_POST:
            # Draw post
            painter.setBrush(QBrush(color))
            painter.drawRect(QRectF(base_center_x - 3, base_center_y - 45, 6, 45))
            
            # Draw lamp
            painter.setBrush(QBrush(QColor(255, 255, 200)))
            painter.drawEllipse(QPointF(base_center_x, base_center_y - 50), 8, 8)
            
        elif self.decoration_type in (DecorationType.POND, DecorationType.FOUNTAIN):
            # Draw water surface (same as ground but lighter)
            painter.setBrush(QBrush(color.lighter(120)))
            painter.setPen(QPen(color.darker(120), 2))
            painter.drawPolygon(ground_poly)
            
            # Add fountain spout for fountain
            if self.decoration_type == DecorationType.FOUNTAIN:
                painter.setBrush(QBrush(QColor(200, 200, 200)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(base_center_x, base_center_y - 5), 6, 6)
                painter.setBrush(QBrush(QColor(150, 200, 255)))
                painter.drawEllipse(QPointF(base_center_x, base_center_y - 15), 4, 8)
                
        elif self.decoration_type == DecorationType.WINDMILL:
            # Draw base rectangle
            base_rect = QRectF(base_center_x - 12, base_center_y - 50, 24, 50)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(130), 1))
            painter.drawRect(base_rect)
            
            # Draw blades (simplified)
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            blade_length = 25
            for angle in [0, 90, 180, 270]:
                painter.save()
                painter.translate(base_center_x, base_center_y - 45)
                painter.rotate(angle + self.direction.value)
                painter.drawRect(-2, 0, 4, blade_length)
                painter.restore()
                
        else:
            # Default: Draw elevated isometric box on top of ground
            # Top face of box
            top_face = [
                QPointF(top.x(), top.y() - body_height),
                QPointF(right.x(), right.y() - body_height),
                QPointF(bottom.x(), bottom.y() - body_height),
                QPointF(left.x(), left.y() - body_height),
            ]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            painter.drawPolygon(QPolygonF(top_face))
            
            # Left side of box
            left_face = [
                QPointF(left.x(), left.y() - body_height),
                QPointF(bottom.x(), bottom.y() - body_height),
                QPointF(bottom.x(), bottom.y()),
                QPointF(left.x(), left.y()),
            ]
            painter.setBrush(QBrush(color.darker(115)))
            painter.drawPolygon(QPolygonF(left_face))
            
            # Right side of box
            right_face = [
                QPointF(right.x(), right.y() - body_height),
                QPointF(bottom.x(), bottom.y() - body_height),
                QPointF(bottom.x(), bottom.y()),
                QPointF(right.x(), right.y()),
            ]
            painter.setBrush(QBrush(color.darker(130)))
            painter.drawPolygon(QPolygonF(right_face))
        
        # Draw direction indicator for rotatable items
        info = DECORATION_INFO.get(self.decoration_type, {})
        if info.get("can_rotate", False):
            # Small arrow showing direction at base center
            painter.setPen(QPen(QColor(255, 255, 255, 150), 2))
            arrow_len = 8
            ay = base_center_y - body_height / 2  # Arrow at mid-height
            if self.direction == Direction.NORTH:
                painter.drawLine(QPointF(base_center_x, ay), QPointF(base_center_x, ay - arrow_len))
            elif self.direction == Direction.SOUTH:
                painter.drawLine(QPointF(base_center_x, ay), QPointF(base_center_x, ay + arrow_len))
            elif self.direction == Direction.EAST:
                painter.drawLine(QPointF(base_center_x, ay), QPointF(base_center_x + arrow_len, ay))
            elif self.direction == Direction.WEST:
                painter.drawLine(QPointF(base_center_x, ay), QPointF(base_center_x - arrow_len, ay))


class PenSprite(Sprite):
    """
    Specialized sprite for animal pens/coops with fence rendering.
    
    Draws an isometric fenced area that animals can wander in.
    """
    
    def __init__(
        self,
        world_x: float,
        world_y: float,
        pen_width: int = 3,
        pen_height: int = 3,
        fence_color: QColor | None = None,
        ground_color: QColor | None = None,
        parent: QGraphicsItem | None = None,
    ):
        # Calculate visual dimensions
        # Pen is drawn as isometric area, so we need to account for that
        visual_width = (pen_width + pen_height) * (TILE_WIDTH // 2) + 4
        visual_height = (pen_width + pen_height) * (TILE_HEIGHT // 2) + 20  # Extra for fence posts
        
        super().__init__(
            world_x=world_x,
            world_y=world_y,
            width=visual_width,
            height=visual_height,
            layer=SpriteLayer.BUILDINGS,
            parent=parent,
        )
        
        self.pen_width = pen_width
        self.pen_height = pen_height
        self.fence_color = fence_color or QColor(139, 90, 43)  # Brown wood
        self.ground_color = ground_color or QColor(160, 140, 100)  # Dirt/hay
        
        # Building ID for tracking
        self.building_id: str = ""
    
    def _update_screen_position(self) -> None:
        """Position at the top corner of the pen area."""
        screen_x, screen_y = world_to_screen(self._world_x, self._world_y)
        # Offset to position correctly
        screen_x -= self._width / 2
        screen_y -= 10  # Small offset for fence height
        self.setPos(screen_x, screen_y)
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the pen."""
        return QRectF(0, 0, self._width, self._height)
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Paint the pen with fence."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate isometric corners relative to sprite origin
        # The pen occupies from (world_x, world_y) to (world_x + pen_width, world_y + pen_height)
        half_tile_w = TILE_WIDTH // 2
        half_tile_h = TILE_HEIGHT // 2
        
        # Center point of the sprite
        cx = self._width / 2
        cy = 10  # Top of pen area
        
        # Calculate corner offsets in isometric projection
        # Top corner (0, 0)
        top = QPointF(cx, cy)
        # Right corner (width, 0)
        right = QPointF(cx + self.pen_width * half_tile_w, cy + self.pen_width * half_tile_h)
        # Bottom corner (width, height)
        bottom = QPointF(cx + (self.pen_width - self.pen_height) * half_tile_w, 
                        cy + (self.pen_width + self.pen_height) * half_tile_h)
        # Left corner (0, height)
        left = QPointF(cx - self.pen_height * half_tile_w, cy + self.pen_height * half_tile_h)
        
        # Draw ground (dirt/hay floor)
        ground_polygon = QPolygonF([top, right, bottom, left])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.ground_color))
        painter.drawPolygon(ground_polygon)
        
        # Draw fence posts and rails
        fence_pen = QPen(self.fence_color.darker(120), 2)
        painter.setPen(fence_pen)
        painter.setBrush(QBrush(self.fence_color))
        
        # Draw fence rails along each edge
        self._draw_fence_edge(painter, top, right, self.pen_width)
        self._draw_fence_edge(painter, right, bottom, self.pen_height)
        self._draw_fence_edge(painter, bottom, left, self.pen_width)
        self._draw_fence_edge(painter, left, top, self.pen_height)
        
        # Draw corner posts (taller)
        post_size = 6
        post_height = 15
        for corner in [top, right, bottom, left]:
            self._draw_fence_post(painter, corner, post_size, post_height)
    
    def _draw_fence_edge(self, painter: QPainter, start: QPointF, end: QPointF, segments: int) -> None:
        """Draw fence posts and rails along an edge."""
        # Draw rail
        rail_offset = -8  # Height of rail above ground
        painter.drawLine(
            QPointF(start.x(), start.y() + rail_offset),
            QPointF(end.x(), end.y() + rail_offset)
        )
        
        # Draw intermediate posts
        if segments > 1:
            for i in range(1, segments):
                t = i / segments
                post_x = start.x() + (end.x() - start.x()) * t
                post_y = start.y() + (end.y() - start.y()) * t
                self._draw_fence_post(painter, QPointF(post_x, post_y), 4, 10)
    
    def _draw_fence_post(self, painter: QPainter, pos: QPointF, width: int, height: int) -> None:
        """Draw a single fence post."""
        painter.setBrush(QBrush(self.fence_color))
        # Draw post as a small rectangle going up
        painter.drawRect(
            int(pos.x() - width / 2),
            int(pos.y() - height),
            width,
            height
        )
    
    def get_animal_bounds(self) -> tuple[float, float, float, float]:
        """
        Get the world coordinate bounds where animals can wander.
        
        Returns:
            (min_x, min_y, max_x, max_y) in world coordinates
        """
        return (
            self._world_x + 0.3,  # Small margin from fence
            self._world_y + 0.3,
            self._world_x + self.pen_width - 0.3,
            self._world_y + self.pen_height - 0.3,
        )


class CharacterSprite(Sprite):
    """
    Specialized sprite for characters (player, workers).
    
    Supports directional animations.
    """
    
    DIRECTIONS = ["south", "north", "east", "west"]
    
    def __init__(
        self,
        world_x: float,
        world_y: float,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(
            world_x=world_x,
            world_y=world_y,
            width=32,
            height=48,  # Characters are taller
            layer=SpriteLayer.CHARACTERS,
            parent=parent,
        )
        
        self._direction = "south"
        
        # Character placeholder - blue for player
        self.set_placeholder(QColor(70, 130, 180), "rect")
    
    @property
    def direction(self) -> str:
        return self._direction
    
    @direction.setter
    def direction(self, value: str) -> None:
        if value in self.DIRECTIONS:
            self._direction = value
            # Update animation if walking
            if self._current_animation.startswith("walk"):
                self.play_animation(f"walk_{value}")
    
    def play_directional_animation(self, base_name: str) -> None:
        """Play an animation for the current direction."""
        anim_name = f"{base_name}_{self._direction}"
        if anim_name in self._animations:
            self.play_animation(anim_name)
        elif base_name in self._animations:
            self.play_animation(base_name)


class AnimalSprite(Sprite):
    """
    Specialized sprite for animals.
    
    Shows different appearances based on growth stage.
    Supports wandering within pen bounds.
    """
    
    def __init__(
        self,
        world_x: float,
        world_y: float,
        animal_type: str = "chicken",
        animal_id: str = "",
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(
            world_x=world_x,
            world_y=world_y,
            width=32,
            height=32,
            layer=SpriteLayer.ANIMALS,
            parent=parent,
        )
        
        self.animal_type = animal_type
        self.animal_id = animal_id
        self._growth_stage = "adult"
        
        # Wandering state
        self._pen_bounds: tuple[float, float, float, float] | None = None
        self._wander_target: tuple[float, float] | None = None
        self._wander_speed = 0.5  # Tiles per second
        self._wander_timer = 0.0
        self._wander_interval = 3000.0  # ms between new wander targets
        self._is_wandering = False
        self._facing_direction = "south"
        
        # Animal placeholder colors (fallback if no sprite)
        self._placeholder_colors = {
            "chicken": QColor(255, 220, 100),  # Yellow
            "pig": QColor(255, 180, 180),      # Pink
            "cow": QColor(139, 90, 43),        # Brown
        }
        self.set_placeholder(self._placeholder_colors.get(animal_type, QColor(200, 200, 200)), "circle")
        
        # Try to load sprite
        self._load_animal_sprite()
    
    @property
    def growth_stage(self) -> str:
        return self._growth_stage
    
    @growth_stage.setter
    def growth_stage(self, value: str) -> None:
        logger.info(f"AnimalSprite.growth_stage setter: {self._growth_stage} -> {value} (animal_id={self.animal_id})")
        if self._growth_stage != value:
            self._growth_stage = value
            loaded = self._load_animal_sprite()
            logger.info(f"  Sprite reload result: {loaded}")
        self.update()
    
    def _load_animal_sprite(self) -> bool:
        """Load sprite based on animal type, growth stage, and direction."""
        import sys
        from pathlib import Path
        
        # Map direction to filename suffix
        dir_map = {"south": "s", "north": "n", "east": "e", "west": "w"}
        dir_suffix = dir_map.get(self._facing_direction, "s")
        
        # Map growth stage to filename
        stage_map = {"baby": "baby", "teen": "teen", "adult": "adult"}
        stage_name = stage_map.get(self._growth_stage, "adult")
        
        # Build relative path: e.g., "animals/chicken/chicken_baby_s.png"
        rel_path = f"animals/{self.animal_type}/{self.animal_type}_{stage_name}_{dir_suffix}.png"
        
        # Try multiple methods to find the assets directory
        possible_paths = []
        
        # Method 1: Relative to this file
        try:
            this_file = Path(__file__).resolve()
            possible_paths.append(this_file.parent.parent / "assets" / rel_path)
        except:
            pass
        
        # Method 2: Using the module's path
        try:
            import anki_animal_ranch
            module_dir = Path(anki_animal_ranch.__file__).parent
            possible_paths.append(module_dir / "assets" / rel_path)
        except:
            pass
        
        # Method 3: Check if running as Anki addon (numbered folder)
        try:
            for path in sys.path:
                if "addons21" in path:
                    addons_dir = Path(path)
                    if addons_dir.is_dir():
                        for addon_dir in addons_dir.iterdir():
                            if addon_dir.is_dir():
                                test_path = addon_dir / "assets" / rel_path
                                if test_path.exists():
                                    possible_paths.insert(0, test_path)
        except:
            pass
        
        # Try each possible path
        for sprite_path in possible_paths:
            if sprite_path.exists():
                try:
                    pixmap = QPixmap(str(sprite_path))
                    if not pixmap.isNull():
                        self._width = pixmap.width()
                        self._height = pixmap.height()
                        self.set_pixmap(pixmap)
                        self.prepareGeometryChange()
                        self._update_screen_position()
                        return True
                except Exception as e:
                    logger.warning(f"Error loading animal sprite {sprite_path}: {e}")
        
        # Fallback to placeholder
        self.set_pixmap(None)
        self.set_placeholder(
            self._placeholder_colors.get(self.animal_type, QColor(200, 200, 200)), 
            "circle"
        )
        return False
    
    def set_pen_bounds(self, min_x: float, min_y: float, max_x: float, max_y: float) -> None:
        """
        Set the bounds where this animal can wander.
        
        Args:
            min_x, min_y: Top-left corner of pen
            max_x, max_y: Bottom-right corner of pen
        """
        self._pen_bounds = (min_x, min_y, max_x, max_y)
        self._is_wandering = True
        # Pick initial target
        self._pick_wander_target()
    
    def _pick_wander_target(self) -> None:
        """Pick a new random position to wander toward."""
        import random
        
        if self._pen_bounds is None:
            return
        
        min_x, min_y, max_x, max_y = self._pen_bounds
        
        # Random position within bounds
        self._wander_target = (
            random.uniform(min_x, max_x),
            random.uniform(min_y, max_y),
        )
        
        # Update facing direction based on target
        if self._wander_target:
            dx = self._wander_target[0] - self._world_x
            dy = self._wander_target[1] - self._world_y
            
            if abs(dx) > abs(dy):
                new_direction = "east" if dx > 0 else "west"
            else:
                new_direction = "south" if dy > 0 else "north"
            
            # Reload sprite if direction changed
            if new_direction != self._facing_direction:
                self._facing_direction = new_direction
                self._load_animal_sprite()
        
        # Reset timer with some randomness
        import random
        self._wander_timer = random.uniform(2000, 5000)
    
    def update_wandering(self, delta_ms: float) -> None:
        """
        Update wandering behavior.
        
        Should be called each frame.
        
        Args:
            delta_ms: Milliseconds since last update
        """
        if not self._is_wandering or self._pen_bounds is None:
            return
        
        # Update wander timer
        self._wander_timer -= delta_ms
        if self._wander_timer <= 0:
            self._pick_wander_target()
        
        # Move toward target
        if self._wander_target:
            dx = self._wander_target[0] - self._world_x
            dy = self._wander_target[1] - self._world_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance > 0.1:
                # Move toward target
                delta_seconds = delta_ms / 1000.0
                move_distance = self._wander_speed * delta_seconds
                
                if move_distance >= distance:
                    # Arrived
                    self.set_world_pos(self._wander_target[0], self._wander_target[1])
                    self._wander_target = None
                else:
                    # Partial move
                    ratio = move_distance / distance
                    new_x = self._world_x + dx * ratio
                    new_y = self._world_y + dy * ratio
                    
                    # Clamp to bounds
                    min_x, min_y, max_x, max_y = self._pen_bounds
                    new_x = max(min_x, min(max_x, new_x))
                    new_y = max(min_y, min(max_y, new_y))
                    
                    self.set_world_pos(new_x, new_y)
    
    def stop_wandering(self) -> None:
        """Stop the animal from wandering."""
        self._is_wandering = False
        self._wander_target = None


class FloatingEffectSprite(Sprite):
    """
    A sprite that floats upward and fades out.
    
    Used for production feedback (floating egg icon, +money, etc.)
    """
    
    def __init__(
        self,
        world_x: float,
        world_y: float,
        text: str = "🥚",
        color: QColor = QColor(255, 255, 255),
        duration_ms: int = 1500,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(
            world_x=world_x,
            world_y=world_y,
            width=40,
            height=40,
            layer=SpriteLayer.EFFECTS,
            parent=parent,
        )
        
        self._text = text
        self._color = color
        self._duration_ms = duration_ms
        self._elapsed_ms = 0.0
        self._start_y = world_y
        self._float_height = 2.5  # World units to float up
        self._is_finished = False
    
    @property
    def is_finished(self) -> bool:
        """Check if the effect has completed."""
        return self._is_finished
    
    def update_effect(self, delta_ms: float) -> None:
        """
        Update the floating effect.
        
        Args:
            delta_ms: Milliseconds since last update
        """
        if self._is_finished:
            return
        
        self._elapsed_ms += delta_ms
        
        if self._elapsed_ms >= self._duration_ms:
            self._is_finished = True
            self.hide()
            return
        
        # Calculate progress (0 to 1)
        progress = self._elapsed_ms / self._duration_ms
        
        # Float upward (ease out)
        float_progress = 1 - (1 - progress) ** 2  # Ease out quad
        offset_y = -self._float_height * float_progress
        
        # Update world position (moving up in isometric space)
        self._world_z = self._float_height * float_progress
        self._update_screen_position()
        
        # Update opacity (fade out in last 25%)
        if progress > 0.75:
            fade_progress = (progress - 0.75) / 0.25
            self.setOpacity(1.0 - fade_progress)
        
        self.update()
    
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Draw the floating text/emoji."""
        # Draw background glow
        rect = self.boundingRect()
        center = rect.center()
        
        # Semi-transparent background
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 18, 18)
        
        # Draw text/emoji
        painter.setPen(QPen(self._color))
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)