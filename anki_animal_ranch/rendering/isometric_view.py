"""
Isometric view - Main game rendering viewport.

This is the central rendering component that displays the
isometric farm world using Qt's Graphics View framework.
"""

from __future__ import annotations

from ..utils.logger import get_logger
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QKeyEvent, QMouseEvent, QPainter, QPen, QPolygonF, QWheelEvent
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QWidget

from ..core.constants import (
    FRAME_TIME_MS,
    TILE_HEIGHT,
    TILE_WIDTH,
    ZONE_HEIGHT,
    ZONE_WIDTH,
)
from ..utils.math_utils import screen_to_grid, screen_to_world
from .camera import Camera
from .sprite import (
    AnimalSprite,
    BuildingSprite,
    CharacterSprite,
    FloatingEffectSprite,
    PlacementPreviewSprite,
    Sprite,
    SpriteLayer,
    TileSprite,
)
from .tile_grid import TileGrid

if TYPE_CHECKING:
    from ..models.farm import Farm

logger = get_logger(__name__)


class IsometricView(QGraphicsView):
    """
    Main isometric rendering viewport.
    
    Displays the farm world with:
    - Tile-based terrain
    - Buildings
    - Animals
    - Characters (workers)
    - Effects
    
    Signals:
        tile_clicked: Emitted when a tile is clicked (grid_x, grid_y)
        tile_right_clicked: Emitted on right-click (grid_x, grid_y)
        sprite_clicked: Emitted when a sprite is clicked (sprite)
    """
    
    # Signals
    tile_clicked = pyqtSignal(int, int)
    tile_right_clicked = pyqtSignal(int, int)
    sprite_clicked = pyqtSignal(object)
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        
        # Create scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # Scene background
        self._scene.setBackgroundBrush(QBrush(QColor(60, 90, 60)))  # Dark green
        
        # Camera
        self._camera = Camera(self)
        
        # Tile grid
        self._grid: TileGrid | None = None
        
        # Sprite collections
        self._sprites: dict[str, Sprite] = {}
        self._floating_effects: list[FloatingEffectSprite] = []
        
        # Interaction state
        self._is_dragging = False
        self._drag_start: QPointF | None = None
        self._drag_button: Qt.MouseButton | None = None
        
        # Animation timer
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._on_animation_tick)
        self._last_tick_time = 0
        
        # Click handler (for custom click behavior)
        self._click_handler: Callable[[int, int], None] | None = None
        
        # Keyboard state for WASD panning
        self._keys_pressed: set[int] = set()
        self._pan_speed = 8.0  # Pixels per frame
        
        # Zone hover highlight
        self._hovered_zone: int = -1
        self._zone_highlight: QGraphicsItemGroup | None = None
        self._zone_label: QGraphicsTextItem | None = None
        
        # Building placement preview
        self._placement_preview: PlacementPreviewSprite | None = None
        
        # Placement preview update timer (polls mouse position)
        self._placement_timer = QTimer(self)
        self._placement_timer.timeout.connect(self._poll_placement_position)
        
        # Configure view
        self._setup_view()
        
        # Enable keyboard focus and mouse tracking
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        
        logger.info("IsometricView initialized")
    
    def _setup_view(self) -> None:
        """Configure view settings."""
        # Rendering hints
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Disable scrollbars (we use camera for navigation)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Optimization
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState)
        
        # Mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Drag mode
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        # Transform anchor
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def camera(self) -> Camera:
        return self._camera
    
    @property
    def grid(self) -> TileGrid | None:
        return self._grid
    
    # =========================================================================
    # Initialization
    # =========================================================================
    
    def initialize_grid(
        self,
        zones_wide: int = 3,
        zones_tall: int = 4,
        unlocked_zones: int = 1,
    ) -> None:
        """
        Initialize the tile grid.
        
        Args:
            zones_wide: Number of zones horizontally
            zones_tall: Number of zones vertically
            unlocked_zones: Number of zones initially unlocked
        """
        from ..utils.math_utils import world_to_screen
        
        # Remove existing grid
        if self._grid is not None:
            self._grid.remove_from_scene()
        
        # Create new grid
        self._grid = TileGrid(zones_wide, zones_tall, unlocked_zones)
        self._grid.add_to_scene(self._scene)
        
        # Calculate proper isometric scene bounds
        # In isometric projection, we need to find the actual screen extents
        grid_w = self._grid.width
        grid_h = self._grid.height
        
        # Calculate screen positions of grid corners
        # Top corner (0, 0)
        top_x, top_y = world_to_screen(0, 0)
        # Right corner (width, 0)  
        right_x, right_y = world_to_screen(grid_w, 0)
        # Bottom corner (width, height)
        bottom_x, bottom_y = world_to_screen(grid_w, grid_h)
        # Left corner (0, height)
        left_x, left_y = world_to_screen(0, grid_h)
        
        # Find actual bounds
        min_x = min(top_x, right_x, bottom_x, left_x)
        max_x = max(top_x, right_x, bottom_x, left_x)
        min_y = min(top_y, right_y, bottom_y, left_y)
        max_y = max(top_y, right_y, bottom_y, left_y)
        
        # Add padding
        padding = TILE_WIDTH * 2
        
        self._scene.setSceneRect(
            min_x - padding,
            min_y - padding,
            (max_x - min_x) + padding * 2,
            (max_y - min_y) + padding * 2 + TILE_HEIGHT,  # Extra for tile height
        )
        
        # Configure camera bounds
        self._camera.set_bounds_from_grid(self._grid.width, self._grid.height)
        
        # Center camera on the first unlocked zone (center of zone 0)
        center_x = ZONE_WIDTH / 2
        center_y = ZONE_HEIGHT / 2
        self._camera.pan_to_world(center_x, center_y)
        
        logger.info(f"Initialized grid: {self._grid.width}x{self._grid.height} tiles")
    
    # =========================================================================
    # Sprite Management
    # =========================================================================
    
    def add_sprite(self, sprite_id: str, sprite: Sprite) -> None:
        """
        Add a sprite to the view.
        
        Args:
            sprite_id: Unique identifier for the sprite
            sprite: The sprite to add
        """
        if sprite_id in self._sprites:
            self.remove_sprite(sprite_id)
        
        self._sprites[sprite_id] = sprite
        self._scene.addItem(sprite)
    
    def remove_sprite(self, sprite_id: str) -> Sprite | None:
        """
        Remove a sprite from the view.
        
        Args:
            sprite_id: ID of the sprite to remove
            
        Returns:
            The removed sprite, or None if not found
        """
        sprite = self._sprites.pop(sprite_id, None)
        if sprite is not None:
            self._scene.removeItem(sprite)
        return sprite
    
    def get_sprite(self, sprite_id: str) -> Sprite | None:
        """Get a sprite by ID."""
        return self._sprites.get(sprite_id)
    
    def show_production_effect(
        self,
        world_x: float,
        world_y: float,
        product_type: str = "egg",
    ) -> FloatingEffectSprite:
        """
        Show a floating production effect (e.g., egg icon floating up).
        
        Args:
            world_x: World X position (where to spawn effect)
            world_y: World Y position
            product_type: Type of product ("egg", "milk", "truffle")
            
        Returns:
            The created effect sprite
        """
        # Map product types to emojis and colors
        effects = {
            "egg": ("🥚", QColor(255, 250, 220)),
            "milk": ("🥛", QColor(255, 255, 255)),
            "truffle": ("🍄", QColor(180, 140, 100)),
        }
        
        emoji, color = effects.get(product_type, ("✨", QColor(255, 255, 200)))
        
        effect = FloatingEffectSprite(
            world_x=world_x,
            world_y=world_y,
            text=emoji,
            color=color,
            duration_ms=3000,  # 3 seconds
        )
        
        self._floating_effects.append(effect)
        self._scene.addItem(effect)
        
        return effect
    
    def add_building_sprite(
        self,
        building_id: str,
        world_x: float,
        world_y: float,
        footprint_width: int = 2,
        footprint_height: int = 2,
        color: QColor | str = QColor(139, 90, 43),
    ) -> BuildingSprite:
        """
        Add a building sprite.
        
        Args:
            building_id: Unique ID for the building
            world_x: World X position
            world_y: World Y position
            footprint_width: Building width in tiles
            footprint_height: Building height in tiles
            color: Placeholder color
            
        Returns:
            The created building sprite
        """
        sprite = BuildingSprite(
            world_x, world_y,
            footprint_width, footprint_height,
        )
        if isinstance(color, str):
            color = QColor(color)
        sprite.set_placeholder(color, "rect")
        
        self.add_sprite(f"building_{building_id}", sprite)
        return sprite
    
    def add_animal_sprite(
        self,
        animal_id: str,
        world_x: float,
        world_y: float,
        animal_type: str = "chicken",
    ) -> AnimalSprite:
        """
        Add an animal sprite.
        
        Args:
            animal_id: Unique ID for the animal
            world_x: World X position
            world_y: World Y position
            animal_type: Type of animal
            
        Returns:
            The created animal sprite
        """
        sprite = AnimalSprite(world_x, world_y, animal_type)
        self.add_sprite(f"animal_{animal_id}", sprite)
        return sprite
    
    # =========================================================================
    # Animation
    # =========================================================================
    
    def start_animation(self) -> None:
        """Start the animation timer."""
        self._animation_timer.start(FRAME_TIME_MS)
        self._last_tick_time = 0
    
    def stop_animation(self) -> None:
        """Stop the animation timer."""
        self._animation_timer.stop()
    
    def _on_animation_tick(self) -> None:
        """Called each animation frame."""
        # Update all sprites
        for sprite in self._sprites.values():
            sprite.update_animation(FRAME_TIME_MS)
            
            # Update animal wandering
            if isinstance(sprite, AnimalSprite):
                sprite.update_wandering(FRAME_TIME_MS)
        
        # Update floating effects
        finished_effects = []
        for effect in self._floating_effects:
            effect.update_effect(FRAME_TIME_MS)
            if effect.is_finished:
                finished_effects.append(effect)
        
        # Remove finished effects
        for effect in finished_effects:
            self._floating_effects.remove(effect)
            self._scene.removeItem(effect)
        
        # Handle WASD camera panning
        self._handle_keyboard_pan()
        
        # Update camera
        self._camera.update(FRAME_TIME_MS)
    
    def _handle_keyboard_pan(self) -> None:
        """Handle WASD keyboard panning."""
        if not self._keys_pressed:
            return
        
        dx = 0.0
        dy = 0.0
        
        # WASD keys
        if Qt.Key.Key_W in self._keys_pressed or Qt.Key.Key_Up in self._keys_pressed:
            dy -= self._pan_speed
        if Qt.Key.Key_S in self._keys_pressed or Qt.Key.Key_Down in self._keys_pressed:
            dy += self._pan_speed
        if Qt.Key.Key_A in self._keys_pressed or Qt.Key.Key_Left in self._keys_pressed:
            dx -= self._pan_speed
        if Qt.Key.Key_D in self._keys_pressed or Qt.Key.Key_Right in self._keys_pressed:
            dx += self._pan_speed
        
        if dx != 0 or dy != 0:
            self._camera.pan(dx, dy)
    
    # =========================================================================
    # Input Handling
    # =========================================================================
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Middle button: start panning
            self._camera.start_pan(QPointF(event.position()))
            self._is_dragging = True
            self._drag_button = Qt.MouseButton.MiddleButton
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton:
            # Store for drag detection / click
            self._drag_start = QPointF(event.position())
            self._drag_button = Qt.MouseButton.LeftButton
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Right click - also allow panning
            self._camera.start_pan(QPointF(event.position()))
            self._is_dragging = True
            self._drag_button = Qt.MouseButton.RightButton
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move."""
        # Only handle if we have an active drag operation
        if self._is_dragging and self._drag_button is not None:
            # Update pan
            self._camera.update_pan(QPointF(event.position()))
            event.accept()
        elif (self._drag_start is not None and 
              self._drag_button == Qt.MouseButton.LeftButton and
              event.buttons() & Qt.MouseButton.LeftButton):
            # Check if we should start dragging (left button held and moved enough)
            delta = QPointF(event.position()) - self._drag_start
            if abs(delta.x()) > 10 or abs(delta.y()) > 10:
                # Start panning with left button
                self._is_dragging = True
                self._camera.start_pan(self._drag_start)
                self._camera.update_pan(QPointF(event.position()))
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            # Clear drag state if no button is pressed (safety)
            if not event.buttons():
                self._drag_start = None
                self._drag_button = None
                if self._is_dragging:
                    self._camera.end_pan()
                    self._is_dragging = False
                    self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Update zone hover highlight
            self._update_zone_hover(QPointF(event.position()))
            
            # Update placement preview position if active
            if self._placement_preview is not None:
                self._update_placement_preview_position(event.position())
            
            super().mouseMoveEvent(event)
    
    def _update_placement_preview_position(self, screen_pos) -> None:
        """Update placement preview based on mouse position."""
        if self._placement_preview is None or self._grid is None:
            return
        
        # Get grid position under mouse
        tile_pos = self.get_tile_at_screen(int(screen_pos.x()), int(screen_pos.y()))
        
        if tile_pos is None:
            self._placement_preview.hide()
            return
        
        grid_x, grid_y = tile_pos
        
        # Check if all tiles in footprint are valid for placement
        footprint_w = self._placement_preview.footprint_width
        footprint_h = self._placement_preview.footprint_height
        
        valid = self._grid.can_place_building(grid_x, grid_y, footprint_w, footprint_h)
        
        # Update preview
        self._placement_preview.show()
        self._placement_preview.set_position(grid_x, grid_y)
        self._placement_preview.set_valid(valid)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        if self._is_dragging and event.button() == self._drag_button:
            # End panning
            self._camera.end_pan()
            self._is_dragging = False
            self._drag_button = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton and not self._is_dragging:
            # This was a click (not a drag)
            if self._drag_start is not None:
                self._handle_click(QPointF(event.position()))
            self._drag_start = None
            self._drag_button = None
            event.accept()
        else:
            self._drag_start = None
            self._drag_button = None
            super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        # Get zoom direction
        delta = event.angleDelta().y()
        
        if delta > 0:
            self._camera.zoom_in()
        elif delta < 0:
            self._camera.zoom_out()
        
        event.accept()
    
    def showEvent(self, event) -> None:
        """Handle show event - ensure mouse tracking is enabled."""
        super().showEvent(event)
        # Must set mouse tracking on viewport after it's created
        self.viewport().setMouseTracking(True)
    
    def enterEvent(self, event) -> None:
        """Handle mouse entering the widget."""
        super().enterEvent(event)
        # Ensure mouse tracking is on when mouse enters
        self.viewport().setMouseTracking(True)
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press for WASD panning."""
        key = event.key()
        
        # Track WASD and arrow keys
        if key in (Qt.Key.Key_W, Qt.Key.Key_A, Qt.Key.Key_S, Qt.Key.Key_D,
                   Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            self._keys_pressed.add(key)
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle key release."""
        key = event.key()
        
        if key in self._keys_pressed:
            self._keys_pressed.discard(key)
            event.accept()
        else:
            super().keyReleaseEvent(event)
    
    # =========================================================================
    # Zone Hover Highlighting
    # =========================================================================
    
    def _update_zone_hover(self, view_pos: QPointF) -> None:
        """Update zone highlight when hovering over locked zones."""
        if self._grid is None:
            return
        
        # Convert to scene coordinates then to grid
        scene_pos = self.mapToScene(view_pos.toPoint())
        world_pos = screen_to_world(scene_pos.x(), scene_pos.y())
        grid_x, grid_y = int(world_pos[0]), int(world_pos[1])
        
        # Check if position is valid
        if not self._grid.is_valid_position(grid_x, grid_y):
            self._clear_zone_highlight()
            return
        
        zone_index = self._grid.get_zone_index(grid_x, grid_y)
        
        # Only highlight locked zones
        if self._grid.is_zone_unlocked(zone_index):
            self._clear_zone_highlight()
            return
        
        # Only update if zone changed
        if zone_index == self._hovered_zone:
            return
        
        self._hovered_zone = zone_index
        self._draw_zone_highlight(zone_index)
    
    def _clear_zone_highlight(self) -> None:
        """Remove zone highlight from scene."""
        if self._zone_highlight is not None:
            self._scene.removeItem(self._zone_highlight)
            self._zone_highlight = None
        if self._zone_label is not None:
            self._scene.removeItem(self._zone_label)
            self._zone_label = None
        self._hovered_zone = -1
    
    def _draw_zone_highlight(self, zone_index: int) -> None:
        """Draw highlight overlay for a zone."""
        if self._grid is None:
            return
        
        # Clear existing highlight
        if self._zone_highlight is not None:
            self._scene.removeItem(self._zone_highlight)
        if self._zone_label is not None:
            self._scene.removeItem(self._zone_label)
        
        # Calculate zone position
        zone_x = zone_index % self._grid.zones_wide
        zone_y = zone_index // self._grid.zones_wide
        
        # Get tile coordinates of zone corners
        start_tile_x = zone_x * ZONE_WIDTH
        start_tile_y = zone_y * ZONE_HEIGHT
        end_tile_x = start_tile_x + ZONE_WIDTH
        end_tile_y = start_tile_y + ZONE_HEIGHT
        
        # Convert zone corners to screen coordinates (isometric)
        from ..utils.math_utils import world_to_screen
        
        # The four corners of the zone in isometric space
        top_corner = world_to_screen(start_tile_x, start_tile_y)  # Top
        right_corner = world_to_screen(end_tile_x, start_tile_y)  # Right
        bottom_corner = world_to_screen(end_tile_x, end_tile_y)   # Bottom
        left_corner = world_to_screen(start_tile_x, end_tile_y)   # Left
        
        # Create polygon for zone boundary
        polygon = QPolygonF([
            QPointF(top_corner[0], top_corner[1]),
            QPointF(right_corner[0], right_corner[1]),
            QPointF(bottom_corner[0], bottom_corner[1]),
            QPointF(left_corner[0], left_corner[1]),
        ])
        
        # Create highlight item
        highlight = QGraphicsPolygonItem(polygon)
        highlight.setPen(QPen(QColor(255, 200, 50, 200), 3))  # Yellow-gold border
        highlight.setBrush(QBrush(QColor(255, 200, 50, 40)))  # Light yellow fill
        highlight.setZValue(1000)  # Above tiles
        
        self._zone_highlight = highlight
        self._scene.addItem(highlight)
        
        # Create zone label
        center_x = (top_corner[0] + bottom_corner[0]) / 2
        center_y = (top_corner[1] + bottom_corner[1]) / 2
        
        label = QGraphicsSimpleTextItem(f"Plot {zone_index + 1}")
        label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        label.setBrush(QBrush(QColor(255, 220, 100)))  # Gold text
        
        # Center the label
        label_rect = label.boundingRect()
        label.setPos(center_x - label_rect.width() / 2, center_y - label_rect.height() / 2)
        label.setZValue(1001)  # Above highlight
        
        self._zone_label = label
        self._scene.addItem(label)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leaving the view."""
        self._clear_zone_highlight()
        super().leaveEvent(event)
    
    def _handle_click(self, pos: QPointF) -> None:
        """Handle a left click."""
        # Convert to scene coordinates
        scene_pos = self.mapToScene(pos.toPoint())
        
        # Check if clicked on a non-tile sprite (buildings, animals, characters)
        items = self._scene.items(scene_pos)
        for item in items:
            # Skip tile sprites - we want to click through them
            if isinstance(item, TileSprite):
                continue
            if isinstance(item, Sprite):
                self.sprite_clicked.emit(item)
                return
        
        # Convert to grid coordinates
        world_pos = screen_to_world(scene_pos.x(), scene_pos.y())
        grid_x, grid_y = int(world_pos[0]), int(world_pos[1])
        
        # Emit signal
        self.tile_clicked.emit(grid_x, grid_y)
        
        # Call custom handler if set
        if self._click_handler is not None:
            self._click_handler(grid_x, grid_y)
    
    def _handle_right_click(self, pos: QPointF) -> None:
        """Handle a right click."""
        scene_pos = self.mapToScene(pos.toPoint())
        world_pos = screen_to_world(scene_pos.x(), scene_pos.y())
        grid_x, grid_y = int(world_pos[0]), int(world_pos[1])
        
        self.tile_right_clicked.emit(grid_x, grid_y)
    
    def set_click_handler(self, handler: Callable[[int, int], None] | None) -> None:
        """
        Set a custom click handler.
        
        Args:
            handler: Function that takes (grid_x, grid_y)
        """
        self._click_handler = handler
    
    # =========================================================================
    # Utility
    # =========================================================================
    
    def fit_view_to_unlocked(self) -> None:
        """Fit the view to show the unlocked zone nicely."""
        from ..utils.math_utils import world_to_screen
        
        if self._grid is None:
            return
        
        # Center on first unlocked zone
        center_x = ZONE_WIDTH / 2
        center_y = ZONE_HEIGHT / 2
        
        screen_x, screen_y = world_to_screen(center_x, center_y)
        self.centerOn(screen_x, screen_y)
    
    def highlight_tile(self, x: int, y: int, color: QColor | None = None) -> None:
        """
        Highlight a tile (for selection, hover, etc.).
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            color: Highlight color (None to remove highlight)
        """
        if self._grid is None:
            return
        
        tile = self._grid.get_tile(x, y)
        if tile is None or tile.sprite is None:
            return
        
        # TODO: Implement proper highlight effect
        # For now, just change the color slightly
        if color is not None:
            tile.sprite.set_placeholder(color, "diamond")
    
    def get_tile_at_screen(self, screen_x: int, screen_y: int) -> tuple[int, int] | None:
        """
        Get the grid coordinates at a screen position.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            
        Returns:
            Tuple of (grid_x, grid_y) or None if outside grid
        """
        scene_pos = self.mapToScene(screen_x, screen_y)
        world_pos = screen_to_world(scene_pos.x(), scene_pos.y())
        grid_x, grid_y = int(world_pos[0]), int(world_pos[1])
        
        if self._grid and self._grid.is_valid_position(grid_x, grid_y):
            return (grid_x, grid_y)
        return None

    # =========================================================================
    # Grid Visibility
    # =========================================================================
    
    def set_grid_visible(self, visible: bool) -> None:
        """
        Show or hide the tile grid lines.
        
        Args:
            visible: True to show grid, False to hide
        """
        if self._grid is not None:
            self._grid.set_grid_visible(visible)
    
    # =========================================================================
    # Placement Preview
    # =========================================================================
    
    def show_placement_preview(self, footprint_width: int, footprint_height: int) -> None:
        """
        Show the building placement preview.
        
        Args:
            footprint_width: Width of building in tiles
            footprint_height: Height of building in tiles
        """
        # Remove existing preview if any
        self.hide_placement_preview()
        
        # Create new preview
        self._placement_preview = PlacementPreviewSprite(footprint_width, footprint_height)
        self._scene.addItem(self._placement_preview)
        
        # Initially hide until mouse moves over a valid position
        self._placement_preview.hide()
        
        # Also show the grid
        self.set_grid_visible(True)
        
        # Start polling timer for mouse position (16ms = ~60fps)
        self._placement_timer.start(16)
        
        # Force an initial position update
        self._poll_placement_position()
    
    def hide_placement_preview(self) -> None:
        """Hide and remove the placement preview."""
        # Stop polling timer
        self._placement_timer.stop()
        
        if self._placement_preview is not None:
            self._scene.removeItem(self._placement_preview)
            self._placement_preview = None
        
        # Also hide the grid
        self.set_grid_visible(False)
    
    def update_placement_preview(self, grid_x: int, grid_y: int, valid: bool) -> None:
        """
        Update the placement preview position and validity.
        
        Args:
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate
            valid: Whether placement is valid at this position
        """
        if self._placement_preview is not None:
            self._placement_preview.show()
            self._placement_preview.set_position(grid_x, grid_y)
            self._placement_preview.set_valid(valid)
    
    def _poll_placement_position(self) -> None:
        """Poll current mouse position and update placement preview."""
        if self._placement_preview is None:
            return
        
        # Get cursor position relative to this widget
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        
        # Only update if cursor is within the view
        if self.rect().contains(cursor_pos):
            self._update_placement_preview_position(cursor_pos)
        else:
            self._placement_preview.hide()