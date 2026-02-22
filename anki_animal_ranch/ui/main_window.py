"""
Main game window.

This is the primary window for the game, containing the
isometric view, HUD, and all game UI components.
"""

from __future__ import annotations

from ..utils.logger import get_logger
from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QWidget,
)

from ..core.constants import (
    DECORATION_FOOTPRINTS,
    DECORATION_INFO,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    VERSION,
    AnimalType,
    BuildingType,
    DecorationType,
    Direction,
    Events,
)
from ..core.event_bus import event_bus
from .panels.side_panel import SidePanel
from .placement_state import PlacementState, VisitState
from ..core.time_system import TimeSystem
from ..data import get_save_manager
from ..models.building import Building
from ..models.farm import Farm
from ..services.shop_service import purchase_animal, purchase_building, purchase_decoration

from ..rendering import IsometricView
from ..rendering.sprite import AnimalSprite, DecorationSprite, PenSprite
from ..systems import GrowthSystem
from .sprite_manager import SpriteManager

if TYPE_CHECKING:
    from aqt.main import AnkiQt

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Main game window for Anki Animal Ranch.
    
    This window contains:
    - Isometric game view (center)
    - HUD overlay (top)
    - Side panels (right)
    - Control buttons
    """
    
    def __init__(self, mw: AnkiQt | None = None, parent: QWidget | None = None):
        """
        Initialize the main game window.
        
        Args:
            mw: The Anki main window (for integration)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.mw = mw
        self.farm: Farm | None = None
        self.time_system: TimeSystem | None = None
        self.growth_system: GrowthSystem | None = None
        
        # Rendering
        self._iso_view: IsometricView | None = None

        # Placement and visit state
        self._placement = PlacementState()
        self._visit = VisitState()
        
        # Sprite lifecycle manager (created in _setup_ui after _iso_view exists)
        self._sprites: SpriteManager | None = None
        
        self._setup_window()
        self._setup_ui()
        self._setup_game()
        
        # Delay changelog check so game is fully visible in background
        # Using a longer delay ensures the window is rendered
        QTimer.singleShot(1000, self._check_for_changelog)
        
        logger.info("MainWindow initialized")
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"Anki Animal Ranch v{VERSION}")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # Allow the window to be resized
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinMaxButtonsHint
        )
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # =================================================================
        # Isometric Game View
        # =================================================================
        self._iso_view = IsometricView()
        self._iso_view.tile_clicked.connect(self._on_tile_clicked)
        self._iso_view.tile_right_clicked.connect(self._on_tile_right_clicked)
        self._iso_view.sprite_clicked.connect(self._on_sprite_clicked)
        
        main_layout.addWidget(self._iso_view, stretch=3)
        self._sprites = SpriteManager(self._iso_view)

        # =================================================================
        # Side Panel
        # =================================================================
        self.side_panel = SidePanel()
        self.side_panel.shop_clicked.connect(self._on_shop_clicked)
        self.side_panel.market_clicked.connect(self._on_market_clicked)
        self.side_panel.visit_friend_clicked.connect(self._on_visit_friend_clicked)
        self.side_panel.return_home_clicked.connect(self._on_return_home_clicked)
        self.side_panel.cancel_placement_clicked.connect(self._cancel_placement_mode)
        self.side_panel.settings_clicked.connect(self._on_settings_clicked)

        main_layout.addWidget(self.side_panel)
    
    def _setup_game(self) -> None:
        """Initialize game state and systems."""
        # Try to load existing save
        save_manager = get_save_manager()
        loaded = save_manager.load()
        
        if loaded is not None:
            self.farm = loaded
            # Initialize TimeSystem with card count from farm stats
            self.time_system = TimeSystem(total_cards=self.farm.statistics.total_cards_answered)
            logger.info(f"Loaded save: {self.farm.name} with ${self.farm.money}, {self.farm.statistics.total_cards_answered} cards")
        else:
            # Create new farm
            self.farm = Farm.create_new(name="My Ranch")
            self.time_system = TimeSystem(total_cards=0)
            logger.info("Created new farm")
        
        # Initialize growth system
        self.growth_system = GrowthSystem(self.farm)
        
        # Subscribe to production events for visual feedback
        event_bus.subscribe(Events.ANIMAL_PRODUCED, self._on_animal_produced)
        event_bus.subscribe(Events.SEASON_CHANGED, self._on_season_changed)
        
        # Initialize the isometric view
        if self._iso_view is not None:
            # Create grid (3x4 zones based on farm's unlocked zones)
            self._iso_view.initialize_grid(
                zones_wide=3,
                zones_tall=4,
                unlocked_zones=self.farm.unlocked_zones if self.farm else 1,
            )
            
            # Set initial season
            if self.time_system:
                self._iso_view.set_season(self.time_system.current_time.season)
            
            # If we loaded a save, recreate building/animal sprites
            if loaded is not None and self._sprites is not None:
                self._sprites.recreate_from_save(self.farm)
            
            # Start animation
            self._iso_view.start_animation()
            
            # Center view on first zone
            self._iso_view.fit_view_to_unlocked()
        
        # Throttle animation when the app loses focus
        app = QApplication.instance()
        if app is not None:
            app.applicationStateChanged.connect(self._on_app_state_changed)

        # Update UI with initial state
        self._update_ui()

        logger.info("Game systems initialized")
    
    def _check_for_changelog(self) -> None:
        """Check if we should show the changelog (after an update)."""
        from ..core.changelog import get_versions_between, get_changelog_for_versions
        
        save_manager = get_save_manager()
        last_seen = save_manager.get_last_seen_version()
        
        # If no last_seen_version, this is an existing user updating from before
        # changelog tracking was added. Assume they were on 0.2.4.
        if last_seen is None:
            last_seen = "0.2.4"
            logger.info(f"No previous version found, assuming {last_seen}")
        
        # Check if there are new versions to show
        new_versions = get_versions_between(last_seen, VERSION)
        
        if not new_versions:
            logger.debug(f"No changelog to show (last seen: {last_seen}, current: {VERSION})")
            return
        
        logger.info(f"Showing changelog for versions: {new_versions}")
        
        # Get changelog content
        changelog = get_changelog_for_versions(new_versions)
        
        if changelog:
            from .dialogs import ChangelogDialog
            dialog = ChangelogDialog(changelog, self)
            dialog.exec()
        
        # Update the last seen version
        save_manager.update_last_seen_version(VERSION)
    
    def _update_ui(self) -> None:
        """Update all HUD elements to reflect current game state."""
        if self.farm is None or self.time_system is None:
            return
        self.side_panel.refresh(self.farm, self.time_system)
    
    # =========================================================================
    # Tile Click Handlers
    # =========================================================================
    
    def _on_tile_clicked(self, grid_x: int, grid_y: int) -> None:
        """Handle tile click - place building/decoration or show zone unlock dialog."""
        logger.info(f"Tile clicked: ({grid_x}, {grid_y})")
        
        # Block interactions in visit mode
        if self._visit.active:
            return
        
        if self._iso_view is None or self._iso_view.grid is None:
            return
        
        # Check if clicked on a locked zone
        if not self._iso_view.grid.is_tile_unlocked(grid_x, grid_y):
            self._show_zone_unlock_dialog(grid_x, grid_y)
            return
        
        # Handle building placement mode
        if self._placement.active and self._placement.building_type is not None:
            self._place_building(grid_x, grid_y)
            return
        
        # Handle decoration placement mode
        if self._placement.active and self._placement.decoration_type is not None:
            self._place_decoration(grid_x, grid_y)
            return
        
        # Normal click on unlocked tile - no action needed
    
    def _on_tile_right_clicked(self, grid_x: int, grid_y: int) -> None:
        """Handle right-click on tile."""
        logger.info(f"Tile right-clicked: ({grid_x}, {grid_y})")
        
        if self._iso_view is None or self._iso_view.grid is None:
            return
        
        tile = self._iso_view.grid.get_tile(grid_x, grid_y)
        if tile:
            info = f"Tile ({grid_x}, {grid_y})\n"
            info += f"Type: {tile.type.name}\n"
            info += f"Walkable: {tile.walkable}\n"
            info += f"Buildable: {tile.buildable}\n"
            info += f"Building: {tile.building_id or 'None'}"
            logger.info(info)
    
    def _on_sprite_clicked(self, sprite) -> None:
        """Handle click on a sprite."""
        logger.info(f"Sprite clicked: {sprite}")
        
        # Block interactions in placement/move mode
        if self._placement.active:
            return
        
        # Block interactions in visit mode (view only)
        if self._visit.active:
            return
        
        # Check if it's a building (PenSprite)
        if isinstance(sprite, PenSprite) and sprite.building_id:
            building_id = sprite.building_id
            if building_id in self.farm.buildings:
                building = self.farm.buildings[building_id]
                self._show_building_details(building)
        
        # Check if it's a decoration
        elif isinstance(sprite, DecorationSprite) and sprite.decoration_id:
            decoration_id = sprite.decoration_id
            if decoration_id in self.farm.decorations:
                decoration = self.farm.decorations[decoration_id]
                self._show_decoration_details(decoration)
        
        # Check if it's an animal - find and open its building
        elif isinstance(sprite, AnimalSprite) and sprite.animal_id:
            animal_id = sprite.animal_id
            # Find the building containing this animal
            for building in self.farm.buildings.values():
                if animal_id in building.animals:
                    self._show_building_details(building)
                    return
    
    def _show_building_details(self, building: Building) -> None:
        """Show the building details dialog."""
        from .dialogs import BuildingDetailsDialog
        
        dialog = BuildingDetailsDialog(building, self.farm, self)
        dialog.building_upgraded.connect(self._on_building_upgraded)
        dialog.building_move_requested.connect(self._on_building_move_requested)
        dialog.exec()
    
    def _show_decoration_details(self, decoration) -> None:
        """Show the decoration details dialog."""
        from .dialogs import DecorationDetailsDialog
        
        dialog = DecorationDetailsDialog(decoration, self.farm, self)
        dialog.decoration_move_requested.connect(self._on_decoration_move_requested)
        dialog.decoration_delete_requested.connect(self._on_decoration_delete_requested)
        dialog.exec()
    
    def _on_decoration_move_requested(self, decoration_id: str) -> None:
        """Handle decoration move request - enter move mode."""
        if self.farm is None:
            return
        
        decoration = self.farm.decorations.get(decoration_id)
        if decoration is None:
            return
        
        # Store the decoration we're moving
        self._placement.move_decoration_id = decoration_id
        self._placement.active = True
        self._placement.decoration_type = decoration.type
        self._placement.direction = decoration.direction
        
        # Get footprint and info
        footprint = DECORATION_FOOTPRINTS.get(decoration.type, (1, 1))
        info = DECORATION_INFO.get(decoration.type, {})
        can_rotate = info.get("can_rotate", False)
        
        # Update UI with same format as placing
        facing_label = "→ Right" if self._placement.direction == Direction.EAST else "← Left (Flipped)"
        if can_rotate:
            label_text = (
                f"📍 Moving: {info.get('name', decoration.type.value)}\n"
                f"Facing: {facing_label}\n"
                f"Press R to flip • ESC to cancel"
            )
        else:
            label_text = (
                f"📍 Moving: {info.get('name', decoration.type.value)}\n"
                f"Click to place • ESC to cancel"
            )
        self.side_panel.set_placement_mode(True, label_text)
        
        # Show placement preview with grid
        if self._iso_view is not None:
            self._iso_view.show_placement_preview(footprint[0], footprint[1])
        
        logger.info(f"Started move mode for decoration {decoration_id}")
    
    def _on_decoration_delete_requested(self, decoration_id: str) -> None:
        """Handle decoration delete request."""
        if self.farm is None or self._iso_view is None:
            return
        
        # Remove from farm
        if decoration_id in self.farm.decorations:
            del self.farm.decorations[decoration_id]
            logger.info(f"Deleted decoration {decoration_id}")
        
        # Remove sprite
        if self._sprites:
            self._sprites.remove_decoration_sprite(decoration_id)
        
        # Save and update
        self._update_ui()
        self.save_game()
    
    def _on_building_upgraded(self, building_id: str) -> None:
        """Handle building upgrade."""
        logger.info(f"Building upgraded: {building_id}")
        self._update_ui()
        self.save_game()
    
    def _on_building_move_requested(self, building_id: str) -> None:
        """Handle building move request - enter move mode."""
        if self.farm is None:
            return
        
        building = self.farm.buildings.get(building_id)
        if building is None:
            return
        
        # Enter move mode
        self._placement.move_building_id = building_id
        self._placement.active = True
        self._placement.building_type = building.type
        
        # Update UI
        from ..core.constants import BUILDING_FOOTPRINTS
        footprint = BUILDING_FOOTPRINTS.get(building.type, (2, 2))
        
        self.side_panel.set_placement_mode(
            True,
            f"📍 Moving: {building.display_name}\n"
            f"Click on the farm to place ({footprint[0]}x{footprint[1]} tiles)\n"
            f"Press ESC or click Cancel to cancel",
        )
        
        # Show placement preview with grid
        if self._iso_view is not None:
            self._iso_view.show_placement_preview(footprint[0], footprint[1])
        
        logger.info(f"Started move mode for building {building_id}")
    
    def _show_zone_unlock_dialog(self, grid_x: int, grid_y: int) -> None:
        """Show dialog to unlock a zone."""
        from .dialogs import ZoneLockedDialog, ZoneUnlockDialog
        
        if self.farm is None or self._iso_view is None or self._iso_view.grid is None:
            return
        
        zone_index = self._iso_view.grid.get_zone_index(grid_x, grid_y)
        next_zone = self.farm.unlocked_zones  # The next zone to unlock (0-indexed internally)
        
        # Check if this is the next zone to unlock (must unlock in order)
        if zone_index != next_zone:
            dialog = ZoneLockedDialog(zone_index, next_zone, self)
            dialog.exec()
            return
        
        # Show custom unlock dialog
        dialog = ZoneUnlockDialog(zone_index, self.farm, self)
        dialog.zone_unlocked.connect(self._on_zone_unlocked)
        dialog.exec()
    
    def _on_zone_unlocked(self, zone_index: int) -> None:
        """Handle zone unlock."""
        if self._iso_view is None or self._iso_view.grid is None:
            return
        
        # Sync grid unlocked zones
        self._iso_view.grid.unlocked_zones = self.farm.unlocked_zones
        logger.info(f"Unlocked zone {zone_index + 1}!")
        self._update_ui()
        self.save_game()
    
    # =========================================================================
    # Building Placement
    # =========================================================================
    
    def _start_placement_mode(self, building_type: BuildingType) -> None:
        """Start building placement mode."""
        self._placement.active = True
        self._placement.building_type = building_type
        
        # Update UI
        from ..core.constants import BUILDING_FOOTPRINTS
        footprint = BUILDING_FOOTPRINTS.get(building_type, (2, 2))
        
        self.side_panel.set_placement_mode(
            True,
            f"📍 Placing: {building_type.value.replace('_', ' ').title()}\n"
            f"Click on the farm to place ({footprint[0]}x{footprint[1]} tiles)\n"
            f"Press ESC or click Cancel to cancel",
        )
        
        # Show placement preview with grid
        if self._iso_view is not None:
            self._iso_view.show_placement_preview(footprint[0], footprint[1])
        
        logger.info(f"Started placement mode for {building_type.value}")
    
    def _cancel_placement_mode(self) -> None:
        """Cancel building/decoration placement mode."""
        self._placement.reset()
        
        self.side_panel.set_placement_mode(False)
        
        # Hide placement preview and grid
        if self._iso_view is not None:
            self._iso_view.hide_placement_preview()
        
        logger.info("Cancelled placement mode")
    
    def _place_building(self, grid_x: int, grid_y: int) -> None:
        """Place a building at the specified location."""
        if self.farm is None or self._iso_view is None or self._iso_view.grid is None:
            return
        
        if self._placement.building_type is None:
            return
        
        building_type = self._placement.building_type
        
        from ..core.constants import BUILDING_FOOTPRINTS
        footprint = BUILDING_FOOTPRINTS.get(building_type, (2, 2))
        width, height = footprint
        
        # Check if we're in move mode
        is_move_mode = self._placement.move_building_id is not None
        
        # For move mode, we need to temporarily clear the old building's tiles
        # so we can check if the new position is valid
        old_position = None
        if is_move_mode:
            building = self.farm.buildings.get(self._placement.move_building_id)
            if building:
                old_position = building.position
                # Temporarily clear old tiles
                self._iso_view.grid.clear_building(self._placement.move_building_id)
        
        # Check if we can place here
        if not self._iso_view.grid.can_place_building(grid_x, grid_y, width, height):
            logger.warning(f"Cannot place building at ({grid_x}, {grid_y})")
            # Restore old tiles if in move mode
            if is_move_mode and old_position:
                self._iso_view.grid.mark_building(
                    self._placement.move_building_id,
                    old_position[0], old_position[1],
                    width, height
                )
            return
        
        if is_move_mode:
            # === MOVE EXISTING BUILDING ===
            building = self.farm.buildings.get(self._placement.move_building_id)
            if building is None:
                return

            building.position = (grid_x, grid_y)
            self._iso_view.grid.mark_building(building.id, grid_x, grid_y, width, height)
            if self._sprites:
                self._sprites.move_building_sprite(building, grid_x, grid_y, width, height)
            logger.info(f"Moved {building.display_name} to ({grid_x}, {grid_y})")
            self._placement.move_building_id = None
        else:
            # === CREATE NEW BUILDING ===
            building = purchase_building(self.farm, building_type, (grid_x, grid_y))
            if building is None:
                return

            self._iso_view.grid.mark_building(building.id, grid_x, grid_y, width, height)
            if self._sprites:
                self._sprites.add_building_sprite(building, width, height)
            logger.info(f"Placed {building_type.value} at ({grid_x}, {grid_y})")
        
        # Exit placement mode
        self._cancel_placement_mode()
        
        # Update UI
        self._update_ui()
        
        # Auto-save after building placement/move
        self.save_game()
    
    # =========================================================================
    # Decoration Placement
    # =========================================================================
    
    def _start_decoration_placement_mode(self, decoration_type: DecorationType) -> None:
        """Start decoration placement mode."""
        self._placement.active = True
        self._placement.decoration_type = decoration_type
        self._placement.building_type = None  # Clear building type
        self._placement.direction = Direction.EAST  # Reset direction (EAST = default, WEST = flipped)
        
        # Get footprint
        footprint = DECORATION_FOOTPRINTS.get(decoration_type, (1, 1))
        info = DECORATION_INFO.get(decoration_type, {})
        can_rotate = info.get("can_rotate", False)
        
        # Terse format with direction info
        facing_label = "→ Right" if self._placement.direction == Direction.EAST else "← Left (Flipped)"
        if can_rotate:
            label_text = (
                f"📍 Placing: {info.get('name', decoration_type.value)}\n"
                f"Facing: {facing_label}\n"
                f"Press R to flip • ESC to cancel"
            )
        else:
            label_text = (
                f"📍 Placing: {info.get('name', decoration_type.value)}\n"
                f"Click to place • ESC to cancel"
            )
        self.side_panel.set_placement_mode(True, label_text)
        
        # Show placement preview with grid
        if self._iso_view is not None:
            self._iso_view.show_placement_preview(footprint[0], footprint[1])
        
        logger.info(f"Started decoration placement mode for {decoration_type.value}")
    
    def _rotate_placement(self) -> None:
        """Rotate the current placement by 90 degrees."""
        if not self._placement.active:
            return
        
        if self._placement.decoration_type is not None:
            info = DECORATION_INFO.get(self._placement.decoration_type, {})
            if not info.get("can_rotate", False):
                return
            
            # Toggle between EAST (default) and WEST (flipped)
            if self._placement.direction == Direction.EAST:
                self._placement.direction = Direction.WEST
            else:
                self._placement.direction = Direction.EAST
            
            # Update preview text
            footprint = DECORATION_FOOTPRINTS.get(self._placement.decoration_type, (1, 1))
            facing_label = "→ Right" if self._placement.direction == Direction.EAST else "← Left (Flipped)"
            
            self.side_panel.set_placement_mode(
                True,
                f"📍 Placing: {info.get('name', self._placement.decoration_type.value)}\n"
                f"Facing: {facing_label}\n"
                f"Press R to flip • ESC to cancel",
            )
            
            logger.debug(f"Flipped to {self._placement.direction.name}")
    
    def _place_decoration(self, grid_x: int, grid_y: int) -> None:
        """Place a decoration at the specified location."""
        if self.farm is None or self._iso_view is None or self._iso_view.grid is None:
            return
        
        if self._placement.decoration_type is None:
            return
        
        decoration_type = self._placement.decoration_type
        footprint = DECORATION_FOOTPRINTS.get(decoration_type, (1, 1))
        
        # Adjust footprint for rotation
        if self._placement.direction in (Direction.EAST, Direction.WEST):
            width, height = footprint[1], footprint[0]
        else:
            width, height = footprint
        
        # Check if we're in move mode
        is_move_mode = self._placement.move_decoration_id is not None
        
        # For move mode, clear old tiles first
        if is_move_mode:
            decoration = self.farm.decorations.get(self._placement.move_decoration_id)
            if decoration:
                self._iso_view.grid.clear_building(self._placement.move_decoration_id)
        
        # Check if we can place here
        if not self._iso_view.grid.can_place_building(grid_x, grid_y, width, height):
            logger.warning(f"Cannot place decoration at ({grid_x}, {grid_y})")
            # Restore old tiles if in move mode
            if is_move_mode:
                decoration = self.farm.decorations.get(self._placement.move_decoration_id)
                if decoration:
                    old_w, old_h = decoration.rotated_footprint
                    self._iso_view.grid.mark_building(
                        self._placement.move_decoration_id,
                        decoration.position[0], decoration.position[1],
                        old_w, old_h
                    )
            return
        
        if is_move_mode:
            # === MOVE EXISTING DECORATION ===
            decoration = self.farm.decorations.get(self._placement.move_decoration_id)
            if decoration is None:
                return

            decoration.position = (grid_x, grid_y)
            decoration.direction = self._placement.direction
            self._iso_view.grid.mark_building(decoration.id, grid_x, grid_y, width, height)
            if self._sprites:
                self._sprites.move_decoration_sprite(decoration, grid_x, grid_y)
            logger.info(f"Moved {decoration.display_name} to ({grid_x}, {grid_y})")
            self._placement.move_decoration_id = None
        else:
            # === CREATE NEW DECORATION ===
            decoration = purchase_decoration(
                self.farm, decoration_type, (grid_x, grid_y), self._placement.direction
            )
            if decoration is None:
                return

            self._iso_view.grid.mark_building(decoration.id, grid_x, grid_y, width, height)
            if self._sprites:
                self._sprites.add_decoration_sprite(decoration, width, height)
            logger.info(f"Placed {decoration_type.value} at ({grid_x}, {grid_y})")
        
        # Exit placement mode
        self._cancel_placement_mode()
        
        # Update UI
        self._update_ui()
        
        # Auto-save
        self.save_game()
    
    def _add_animal_to_building(self, animal_type: AnimalType, building_id: str) -> None:
        """Add an animal to a specific building."""
        if self.farm is None or self._iso_view is None:
            return

        animal = purchase_animal(self.farm, animal_type, building_id)
        if animal is None:
            return

        building = self.farm.buildings.get(building_id)
        fallback = tuple(building.center_position) if building else None
        if self._sprites:
            self._sprites.add_animal_sprite(animal, building_id, fallback_pos=fallback)
        logger.info(f"Added {animal_type.value} to building {building_id}")
        
        # Update UI
        self._update_ui()
        
        # Auto-save after animal purchase
        self.save_game()
    
    # =========================================================================
    # Button Handlers
    # =========================================================================
    
    def _on_shop_clicked(self) -> None:
        """Handle shop button click."""
        if self.farm is None:
            return
        
        from .dialogs.shop_dialog import ShopDialog
        
        dialog = ShopDialog(self.farm, self)
        dialog.building_purchased.connect(self._on_building_purchased)
        dialog.animal_purchased.connect(self._on_animal_purchased)
        dialog.decoration_purchased.connect(self._on_decoration_purchased)
        dialog.exec()
        
        # Update UI after shop closes
        self._update_ui()
    
    def _on_building_purchased(self, building_type: BuildingType) -> None:
        """Handle building purchase from shop."""
        logger.info(f"Building purchased: {building_type.value}")
        self._start_placement_mode(building_type)
    
    def _on_animal_purchased(self, animal_type: AnimalType, building_id: str) -> None:
        """Handle animal purchase from shop."""
        logger.info(f"Animal purchased: {animal_type.value} for {building_id}")
        self._add_animal_to_building(animal_type, building_id)
    
    def _on_decoration_purchased(self, decoration_type: DecorationType) -> None:
        """Handle decoration purchase from shop."""
        logger.info(f"Decoration purchased: {decoration_type.value}")
        self._start_decoration_placement_mode(decoration_type)
    
    def _on_market_clicked(self) -> None:
        """Handle market button click."""
        if self.farm is None:
            return
        
        from .dialogs.market_dialog import MarketDialog
        
        dialog = MarketDialog(self.farm, self)
        dialog.products_sold.connect(self._on_products_sold)
        dialog.animal_sold.connect(self._on_animal_sold)
        dialog.exec()
        
        # Update UI after market closes
        self._update_ui()
    
    def _on_products_sold(self, product_type: str, quantity: int, total_value: int) -> None:
        """Handle products sold event."""
        if product_type == "all":
            logger.info(f"💰 Sold all products for ${total_value}!")
        else:
            logger.info(f"💰 Sold {quantity} {product_type} for ${total_value}!")
        
        # Update UI
        self._update_ui()
        
        # Auto-save after product sale
        self.save_game()
    
    def _on_animal_sold(self, animal_id: str, sale_value: int) -> None:
        """Handle animal sold event - remove sprite from view."""
        logger.info(f"💰 Sold animal {animal_id} for ${sale_value}!")
        
        # Remove animal sprite
        if self._sprites:
            self._sprites.remove_animal_sprite(animal_id)
        
        # Update UI
        self._update_ui()
        
        # Auto-save after animal sale
        self.save_game()
    
    def _on_visit_friend_clicked(self) -> None:
        """Handle visit friend button click."""
        from .dialogs import AccountCreationDialog, VisitFriendDialog
        from ..data.account_manager import get_account_manager
        
        # Don't allow if already visiting
        if self._visit.active:
            return
        
        account_manager = get_account_manager()
        
        # Check if user has account
        if not account_manager.has_account:
            # Show account creation dialog
            dialog = AccountCreationDialog(self.farm, self)
            dialog.account_created.connect(self._on_account_created)
            result = dialog.exec()
            
            if result != dialog.DialogCode.Accepted:
                return
        
        # Show visit friend dialog
        dialog = VisitFriendDialog(self)
        dialog.visit_requested.connect(self._on_visit_friend_requested)
        dialog.exec()
    
    def _on_account_created(self, username: str) -> None:
        """Handle account creation."""
        logger.info(f"Account created: {username}")
        # Sync farm immediately
        self._sync_farm_to_cloud()
    
    def _on_visit_friend_requested(self, username: str, farm_data: dict) -> None:
        """Handle request to visit a friend's farm."""
        logger.info(f"Visiting farm: {username}")
        
        # Store home farm and current unlocked zones
        self._visit.home_farm = self.farm
        self._visit.home_unlocked_zones = self._iso_view.grid.unlocked_zones
        self._visit.active = True
        self._visit.username = username
        
        # Load friend's farm
        try:
            friend_farm = Farm.from_dict(farm_data)
            self.farm = friend_farm
            
            # Update grid to show friend's unlocked zones
            self._iso_view.grid.unlocked_zones = friend_farm.unlocked_zones
            
            # Clear all building markers from grid (important for placement checks)
            self._iso_view.grid.clear_all_buildings()
            if self._sprites:
                self._sprites.clear_all()
                self._sprites.recreate_from_save(friend_farm)
            
            # Update UI for visit mode
            self._enter_visit_mode(username)
            
            logger.info(f"Now visiting {username}'s farm with {friend_farm.unlocked_zones} unlocked zones")
        except Exception as e:
            logger.error(f"Failed to load friend's farm: {e}")
            self._visit.reset()
    
    def _enter_visit_mode(self, username: str) -> None:
        """Enter visit mode UI."""
        # Update title
        self.setWindowTitle(f"Visiting {username}'s Farm - Anki Animal Ranch")
        
        # Hide normal buttons, show return home
        self.side_panel.set_visit_mode(True)
    
    def _on_return_home_clicked(self) -> None:
        """Return to home farm from visit."""
        if not self._visit.active or self._visit.home_farm is None:
            return
        
        logger.info("Returning home from visit")
        
        # Restore home farm
        self.farm = self._visit.home_farm

        # Restore home farm's unlocked zones
        if self._visit.home_unlocked_zones is not None:
            self._iso_view.grid.unlocked_zones = self._visit.home_unlocked_zones

        self._visit.reset()
        
        # Clear all building markers from grid (important for placement checks)
        self._iso_view.grid.clear_all_buildings()
        if self._sprites:
            self._sprites.clear_all()
            self._sprites.recreate_from_save(self.farm)
        
        # Exit visit mode UI
        self._exit_visit_mode()
    
    def _exit_visit_mode(self) -> None:
        """Exit visit mode UI."""
        # Restore title
        self.setWindowTitle(f"Anki Animal Ranch v{VERSION}")
        
        # Show normal buttons
        self.side_panel.set_visit_mode(False)
        
        # Update UI
        self._update_ui()
    
    def _sync_farm_to_cloud(self) -> None:
        """Sync current farm to cloud (if account exists)."""
        from ..data.account_manager import get_account_manager
        from ..network import sync_farm, is_online_available
        
        # Don't sync while visiting
        if self._visit.active:
            return
        
        account_manager = get_account_manager()
        
        if not account_manager.has_account:
            return
        
        if not is_online_available():
            logger.debug("Offline - skipping cloud sync")
            return
        
        if self.farm is None:
            return
        
        # Sync in background (fire and forget)
        try:
            result = sync_farm(
                account_manager.username,
                account_manager.pkey,
                self.farm.to_dict()
            )
            if result.success:
                logger.debug("Farm synced to cloud")
            else:
                logger.warning(f"Cloud sync failed: {result.error}")
        except Exception as e:
            logger.warning(f"Cloud sync error: {e}")
    
    def _on_settings_clicked(self) -> None:
        """Handle settings button click."""
        from .dialogs import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.farm_reset.connect(self._reset_farm)
        dialog.exec()

    def _reset_farm(self) -> None:
        """Reset the farm to a blank state."""
        farm_name = self.farm.name if self.farm else "My Ranch"

        self.farm = Farm.create_new(name=farm_name)
        self.time_system = TimeSystem(total_cards=0)
        self.growth_system = GrowthSystem(self.farm)

        if self._iso_view and self._iso_view.grid:
            self._iso_view.grid.unlocked_zones = 1
            self._iso_view.grid.clear_all_buildings()

        if self._sprites:
            self._sprites.clear_all()

        self.save_game()
        self._update_ui()

        logger.info("Farm reset to blank state")
    
    def _on_animal_produced(self, **kwargs) -> None:
        """Handle animal production event for visual feedback."""
        animal_id = kwargs.get("animal_id")
        product_type = kwargs.get("product_type")
        quantity = kwargs.get("quantity", 1)
        
        logger.debug(f"Production event: {product_type} x{quantity} from {animal_id}")
        
        # Show floating effect at animal's position
        if animal_id and self._sprites and self._iso_view:
            sprite = self._sprites.get_animal_sprite(animal_id)
            if sprite:
                product_name = product_type.value if hasattr(product_type, 'value') else str(product_type)
                self._iso_view.show_production_effect(
                    world_x=sprite.world_x,
                    world_y=sprite.world_y,
                    product_type=product_name,
                )
        
        # Update UI immediately
        self._update_ui()
    
    def _on_season_changed(self, **kwargs) -> None:
        """Handle season change event to update visuals."""
        new_season = kwargs.get("new_season")
        if new_season and self._iso_view:
            logger.info(f"Season changed to {new_season.value}")
            self._iso_view.set_season(new_season)
    
    def simulate_card_answer(self, ease: int = 3) -> None:
        """
        Simulate answering an Anki card (for testing outside Anki).
        
        Args:
            ease: Simulated ease button (1-4)
        """
        self.on_card_answered(ease)
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def on_card_answered(self, ease: int) -> None:
        """
        Called when the user answers an Anki card.
        
        Args:
            ease: The ease button pressed (1-4)
        """
        if self.time_system is None or self.farm is None:
            return
        
        # Get time before to calculate hours passed
        old_hour = self.time_system.current_time.hour
        old_day = self.time_system.current_time.day
        
        # Advance time
        self.time_system.on_card_answered(ease)
        
        # Calculate hours passed (including across days)
        new_hour = self.time_system.current_time.hour
        new_day = self.time_system.current_time.day
        
        hours_passed = (new_day - old_day) * 24 + (new_hour - old_hour)
        if hours_passed < 0:
            hours_passed += 24  # Day wrap
        
        # Update growth system with time passed
        if self.growth_system is not None and hours_passed > 0:
            events = self.growth_system.update(hours_passed)
            logger.debug(f"Growth system returned {len(events)} events: {[e['type'] for e in events]}")
            
            # Log significant events
            for event in events:
                if event["type"] == "product_produced":
                    logger.info(
                        f"🥚 {event['animal_type'].capitalize()} produced "
                        f"{event['quantity']} {event['product_type']}!"
                    )
                elif event["type"] == "growth_stage_changed":
                    logger.info(
                        f"🌱 {event['animal_type'].capitalize()} grew to {event['new_stage']}!"
                    )
                    animal_id = event.get("animal_id")
                    if animal_id and self._sprites:
                        self._sprites.update_animal_growth_stage(animal_id, event["new_stage"])
        
        # Auto-save every 25 cards (TimeSystem tracks the count)
        if self.time_system.total_cards_answered % 25 == 0:
            self.save_game()
            logger.info(f"💾 Auto-saved after {self.time_system.total_cards_answered} cards")
        
        # Update UI
        self._update_ui()
        
        logger.debug(f"Card answered with ease {ease}, {hours_passed}h passed")
    
    def start_game(self) -> None:
        """Resume animation (called when the window becomes visible)."""
        if self._iso_view:
            self._iso_view.start_animation()
        logger.info("Game started")

    def pause_game(self) -> None:
        """Pause animation (called when the window is hidden)."""
        if self._iso_view:
            self._iso_view.stop_animation()
        logger.info("Game paused")
    
    def save_game(self) -> None:
        """Save the current game state."""
        if self.farm is None:
            return
        
        # Don't save while visiting friend's farm
        if self._visit.active:
            return
        
        # Sync card count from time_system to farm stats before saving
        if self.time_system is not None:
            self.farm.statistics.total_cards_answered = self.time_system.total_cards_answered
        
        save_manager = get_save_manager()
        if save_manager.save(self.farm, app_version=VERSION):
            logger.info(f"💾 Game saved! (${self.farm.money}, {len(self.farm.animals)} animals)")
            # Also sync to cloud
            self._sync_farm_to_cloud()
        else:
            logger.error("Failed to save game")
    
    def load_game(self) -> None:
        """Load a saved game state."""
        save_manager = get_save_manager()
        loaded = save_manager.load()
        
        if loaded is None:
            logger.warning("No save file found")
            return
        
        self.farm = loaded
        # Initialize TimeSystem with card count from farm stats
        self.time_system = TimeSystem(total_cards=self.farm.statistics.total_cards_answered)
        
        # Update growth system with new farm
        self.growth_system = GrowthSystem(self.farm)
        
        # Recreate sprites for loaded entities
        self._recreate_sprites_from_save()
        
        # Update UI
        self._update_ui()
        
        logger.info(f"📂 Game loaded! (${self.farm.money}, {len(self.farm.animals)} animals)")
    
    # =========================================================================
    # Event Handlers
    # =========================================================================
    
    def showEvent(self, event) -> None:
        """Handle window show event."""
        super().showEvent(event)
        self.start_game()
        
        # Center view on first zone after window is shown
        if self._iso_view is not None:
            self._iso_view.fit_view_to_unlocked()
    
    def hideEvent(self, event) -> None:
        """Handle window hide event."""
        super().hideEvent(event)
        self.pause_game()

    def changeEvent(self, event: QEvent) -> None:
        """Pause animation when minimized, resume when restored."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                self.pause_game()
            elif self._iso_view and not self._iso_view._animation_timer.isActive():
                self.start_game()

    def _on_app_state_changed(self, state: Qt.ApplicationState) -> None:
        """Throttle to 5 FPS when another app has focus, restore to 30 FPS when focused."""
        if self._iso_view is None:
            return
        if state == Qt.ApplicationState.ApplicationActive:
            self._iso_view.set_animation_fps(30)
            logger.debug("App focused — 30 FPS")
        else:
            self._iso_view.set_animation_fps(5)
            logger.debug("App unfocused — 5 FPS")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            if self._placement.active:
                self._cancel_placement_mode()
                event.accept()
                return
        elif event.key() == Qt.Key.Key_R:
            if self._placement.active:
                self._rotate_placement()
                event.accept()
                return
        super().keyPressEvent(event)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        self.pause_game()
        self.save_game()
        logger.info("MainWindow closed")
        super().closeEvent(event)
