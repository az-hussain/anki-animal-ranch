"""
Main game window.

This is the primary window for the game, containing the
isometric view, HUD, and all game UI components.
"""

from __future__ import annotations

from ..utils.logger import get_logger
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QColor, QKeyEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.constants import (
    ANIMAL_PURCHASE_PRICES,
    BUILDING_PURCHASE_COSTS,
    DECORATION_COSTS,
    DECORATION_FOOTPRINTS,
    DECORATION_INFO,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    FRAME_TIME_MS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    PRODUCT_BASE_PRICES,
    PRODUCT_QUALITY_MULTIPLIERS,
    VERSION,
    AnimalType,
    BuildingType,
    DecorationType,
    Direction,
    FeedType,
    ProductQuality,
    ProductType,
)
from ..core.constants import Events
from ..core.event_bus import event_bus
from ..core.time_system import TimeSystem
from ..data import get_save_manager
from ..models.animal import Animal
from ..models.building import Building
from ..models.decoration import Decoration
from ..models.farm import Farm
from ..rendering import IsometricView
from ..rendering.sprite import AnimalSprite, DecorationSprite, PenSprite
from ..systems import GrowthSystem

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
        
        # Game loop timer
        self._game_timer: QTimer | None = None
        self._is_running = False
        
        # Building placement mode
        self._placement_mode = False
        self._placement_building_type: BuildingType | None = None
        self._placement_preview_sprite = None
        self._move_building_id: str | None = None  # Building ID when in move mode
        
        # Decoration placement mode
        self._placement_decoration_type: DecorationType | None = None
        self._placement_direction: Direction = Direction.EAST
        self._move_decoration_id: str | None = None
        
        # Friend visit mode
        self._visiting_friend: bool = False
        self._visiting_username: str | None = None
        self._home_farm: Farm | None = None  # Store home farm when visiting
        self._home_unlocked_zones: int | None = None  # Store home zones when visiting
        
        # Track sprites by entity ID
        self._building_sprites: dict[str, PenSprite] = {}
        self._animal_sprites: dict[str, AnimalSprite] = {}
        self._decoration_sprites: dict[str, DecorationSprite] = {}
        
        self._setup_window()
        self._setup_ui()
        self._setup_game()
        
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
        
        # =================================================================
        # Side Panel
        # =================================================================
        side_panel = QFrame()
        side_panel.setFixedWidth(280)
        side_panel.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border-left: 2px solid #444;
            }
        """)
        
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(10, 10, 10, 10)
        side_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("🐄 Farm Status")
        title_label.setStyleSheet("""
            QLabel {
                color: #f0c040;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        side_layout.addWidget(title_label)
        
        # Stats display
        self.money_label = QLabel("💰 Money: $1,500")
        self.time_label = QLabel("🕐 Spring Day 1, 06:00")
        self.animals_label = QLabel("🐔 Animals: 0")
        self.zones_label = QLabel("🌾 Plots: 1/12")
        
        for label in [self.money_label, self.time_label, self.animals_label, self.zones_label]:
            label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 14px;
                    padding: 5px;
                    background-color: #3a3a3a;
                    border-radius: 4px;
                }
            """)
            side_layout.addWidget(label)
        
        # Inventory section
        inventory_title = QLabel("📦 Inventory")
        inventory_title.setStyleSheet("""
            QLabel {
                color: #f0c040;
                font-size: 16px;
                font-weight: bold;
                padding: 8px 5px 4px 5px;
                margin-top: 5px;
            }
        """)
        side_layout.addWidget(inventory_title)
        
        # Inventory display (eggs, milk, truffles)
        self.inventory_label = QLabel("🥚 Eggs: 0\n🥛 Milk: 0\n🍄 Truffles: 0")
        self.inventory_label.setStyleSheet("""
            QLabel {
                color: #bbb;
                font-size: 13px;
                padding: 8px;
                background-color: #353535;
                border-radius: 4px;
                border: 1px solid #444;
            }
        """)
        self.inventory_label.setWordWrap(True)
        self.inventory_label.setMinimumWidth(180)
        side_layout.addWidget(self.inventory_label)
        
        # Feed section
        feed_title = QLabel("🌾 Feed Supply")
        feed_title.setStyleSheet("""
            QLabel {
                color: #f0c040;
                font-size: 16px;
                font-weight: bold;
                padding: 8px 5px 4px 5px;
                margin-top: 5px;
            }
        """)
        side_layout.addWidget(feed_title)
        
        # Feed status display
        self.feed_label = QLabel("No animals yet")
        self.feed_label.setStyleSheet("""
            QLabel {
                color: #bbb;
                font-size: 12px;
                padding: 8px;
                background-color: #353535;
                border-radius: 4px;
                border: 1px solid #444;
            }
        """)
        self.feed_label.setWordWrap(True)
        self.feed_label.setMinimumWidth(180)
        side_layout.addWidget(self.feed_label)
        
        # Spacer
        side_layout.addSpacing(10)
        
        # Placement mode indicator
        self.placement_label = QLabel("")
        self.placement_label.setStyleSheet("""
            QLabel {
                color: #f0c040;
                font-size: 13px;
                padding: 8px;
                background-color: #4a4a2a;
                border-radius: 4px;
                border: 1px solid #6a6a3a;
            }
        """)
        self.placement_label.setWordWrap(True)
        self.placement_label.hide()
        side_layout.addWidget(self.placement_label)
        
        # Action buttons
        button_style = """
            QPushButton {
                background-color: #5a8f4a;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #6ba85a;
            }
            QPushButton:pressed {
                background-color: #4a7f3a;
            }
        """
        
        # Shop button (replaced by Cancel when in placement mode)
        self.shop_btn = QPushButton("🏪 Shop")
        self.shop_btn.setStyleSheet(button_style)
        self.shop_btn.clicked.connect(self._on_shop_clicked)
        side_layout.addWidget(self.shop_btn)
        
        # Cancel placement button (replaces Shop when in placement mode)
        self.cancel_btn = QPushButton("❌ Cancel Placement")
        self.cancel_btn.setStyleSheet(button_style.replace("#5a8f4a", "#8f4a4a").replace("#6ba85a", "#a85a5a").replace("#4a7f3a", "#7f3a3a"))
        self.cancel_btn.clicked.connect(self._cancel_placement_mode)
        self.cancel_btn.hide()
        side_layout.addWidget(self.cancel_btn)
        
        self.market_btn = QPushButton("📦 Market")
        self.market_btn.setStyleSheet(button_style)
        self.market_btn.clicked.connect(self._on_market_clicked)
        side_layout.addWidget(self.market_btn)
        
        # Visit Friend button
        self.visit_btn = QPushButton("👥 Visit Friend")
        self.visit_btn.setStyleSheet(button_style.replace("#5a8f4a", "#4a6a8f").replace("#6ba85a", "#5a7aa5").replace("#4a7f3a", "#3a5a7f"))
        self.visit_btn.clicked.connect(self._on_visit_friend_clicked)
        side_layout.addWidget(self.visit_btn)
        
        # Return Home button (shown when visiting)
        self.return_home_btn = QPushButton("🏠 Return Home")
        self.return_home_btn.setStyleSheet(button_style.replace("#5a8f4a", "#8f6a4a").replace("#6ba85a", "#a87a5a").replace("#4a7f3a", "#7f5a3a"))
        self.return_home_btn.clicked.connect(self._on_return_home_clicked)
        self.return_home_btn.hide()
        side_layout.addWidget(self.return_home_btn)
        
        # Spacer
        side_layout.addStretch()
        
        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setStyleSheet(button_style.replace("#5a8f4a", "#666").replace("#6ba85a", "#777").replace("#4a7f3a", "#555"))
        settings_btn.clicked.connect(self._on_settings_clicked)
        side_layout.addWidget(settings_btn)
        
        main_layout.addWidget(side_panel)
    
    def _setup_game(self) -> None:
        """Initialize game state and systems."""
        # Try to load existing save
        save_manager = get_save_manager()
        loaded = save_manager.load()
        
        if loaded is not None:
            self.farm, self.time_system = loaded
            logger.info(f"Loaded save: {self.farm.name} with ${self.farm.money}")
        else:
            # Create new farm
            self.farm = Farm.create_new(name="My Ranch")
            self.time_system = TimeSystem()
            logger.info("Created new farm")
        
        # Initialize growth system
        self.growth_system = GrowthSystem(self.farm)
        
        # Subscribe to production events for visual feedback
        event_bus.subscribe(Events.ANIMAL_PRODUCED, self._on_animal_produced)
        
        # Initialize the isometric view
        if self._iso_view is not None:
            # Create grid (3x4 zones based on farm's unlocked zones)
            self._iso_view.initialize_grid(
                zones_wide=3,
                zones_tall=4,
                unlocked_zones=self.farm.unlocked_zones if self.farm else 1,
            )
            
            # If we loaded a save, recreate building/animal sprites
            if loaded is not None:
                self._recreate_sprites_from_save()
            
            # Start animation
            self._iso_view.start_animation()
            
            # Center view on first zone
            self._iso_view.fit_view_to_unlocked()
        
        # Set up game loop timer
        self._game_timer = QTimer(self)
        self._game_timer.timeout.connect(self._game_tick)
        
        # Update UI with initial state
        self._update_ui()
        
        logger.info("Game systems initialized")
    
    def _game_tick(self) -> None:
        """Main game loop tick (called every frame)."""
        if not self._is_running or self.farm is None:
            return
        
        # Update UI
        self._update_ui()
    
    def _update_ui(self) -> None:
        """Update UI elements to reflect current game state."""
        if self.farm is None or self.time_system is None:
            return
        
        # Update labels
        self.money_label.setText(f"💰 Money: ${self.farm.money:,}")
        self.time_label.setText(f"🕐 {self.time_system.current_time.format_full()}")
        self.animals_label.setText(f"🐔 Animals: {len(self.farm.animals)}")
        
        # Update zones info
        from ..core.constants import MAX_FARM_ZONES
        zones_text = f"🌾 Plots: {self.farm.unlocked_zones}/{MAX_FARM_ZONES}"
        if self.farm.unlocked_zones < MAX_FARM_ZONES:
            next_cost = self.farm.next_zone_cost
            zones_text += f" (next: ${next_cost:,})"
        self.zones_label.setText(zones_text)
        
        # Update inventory display (simple totals - quality shown in Market)
        inventory = self.farm.player.inventory
        total_value = 0
        
        # Count products by type (summing all qualities)
        product_totals: dict[ProductType, int] = {pt: 0 for pt in ProductType}
        
        for key, count in inventory.items():
            if count <= 0:
                continue
            # Parse key format: "egg_basic", "milk_premium", etc.
            parts = key.split("_")
            if len(parts) >= 2:
                try:
                    product_type = ProductType(parts[0])
                    quality = ProductQuality(parts[1])
                    product_totals[product_type] += count
                    # Calculate value with quality multiplier
                    base_price = PRODUCT_BASE_PRICES.get(product_type, 10)
                    quality_mult = PRODUCT_QUALITY_MULTIPLIERS.get(quality, 1.0)
                    total_value += int(count * base_price * quality_mult)
                except (ValueError, KeyError):
                    # Legacy format without quality - treat as basic
                    try:
                        product_type = ProductType(key)
                        product_totals[product_type] += count
                        total_value += count * PRODUCT_BASE_PRICES.get(product_type, 10)
                    except ValueError:
                        pass
            else:
                # Legacy format without quality
                try:
                    product_type = ProductType(key)
                    product_totals[product_type] += count
                    total_value += count * PRODUCT_BASE_PRICES.get(product_type, 10)
                except ValueError:
                    pass
        
        # Build simple inventory text (just totals)
        eggs = product_totals.get(ProductType.EGG, 0)
        milk = product_totals.get(ProductType.MILK, 0)
        truffles = product_totals.get(ProductType.TRUFFLE, 0)
        
        inventory_text = f"🥚 Eggs: {eggs}\n🥛 Milk: {milk}\n🍄 Truffles: {truffles}"
        if total_value > 0:
            inventory_text += f"\n\n💵 Value: ${total_value:,}"
        
        self.inventory_label.setText(inventory_text)
        
        # Update feed status
        self._update_feed_display()
    def _update_feed_display(self) -> None:
        """Update the feed status display."""
        if self.farm is None:
            return
        
        feed_status = self.farm.get_feed_status()
        
        # Check if we have any animals
        total_animals = len(self.farm.animals)
        if total_animals == 0:
            self.feed_label.setText("No animals yet")
            self.feed_label.setStyleSheet("""
                QLabel {
                    color: #888;
                    font-size: 12px;
                    padding: 8px;
                    background-color: #353535;
                    border-radius: 4px;
                    border: 1px solid #444;
                }
            """)
            return
        
        # Build feed status text
        feed_lines = []
        has_warning = False
        
        feed_emojis = {
            FeedType.CHICKEN_FEED: "🐔",
            FeedType.PIG_FEED: "🐷",
            FeedType.COW_FEED: "🐄",
        }
        
        for feed_type, status in feed_status.items():
            animal_count = status.get("animal_count", 0)
            if animal_count == 0:
                continue
            
            amount = status.get("amount", 0)
            days = status.get("days_remaining", float('inf'))
            emoji = feed_emojis.get(feed_type, "🌾")
            
            if days == float('inf') or days > 30:
                days_text = "30+ days"
                status_emoji = "✅"
            elif days < 10:
                days_text = f"{days:.0f} days"
                status_emoji = "⚠️"
                has_warning = True
            else:
                days_text = f"{days:.0f} days"
                status_emoji = "✅"
            
            feed_lines.append(f"{emoji} {amount} ({days_text}) {status_emoji}")
        
        if feed_lines:
            feed_text = "\n".join(feed_lines)
        else:
            feed_text = "No feed needed"
        
        # Update style based on warning status
        if has_warning:
            self.feed_label.setStyleSheet("""
                QLabel {
                    color: #fa8;
                    font-size: 12px;
                    padding: 8px;
                    background-color: #4a3a2a;
                    border-radius: 4px;
                    border: 1px solid #6a4a2a;
                }
            """)
        else:
            self.feed_label.setStyleSheet("""
                QLabel {
                    color: #8a8;
                    font-size: 12px;
                    padding: 8px;
                    background-color: #353535;
                    border-radius: 4px;
                    border: 1px solid #444;
                }
            """)
        
        self.feed_label.setText(feed_text)
    
    # =========================================================================
    # Tile Click Handlers
    # =========================================================================
    
    def _on_tile_clicked(self, grid_x: int, grid_y: int) -> None:
        """Handle tile click - place building/decoration or show zone unlock dialog."""
        logger.info(f"Tile clicked: ({grid_x}, {grid_y})")
        
        # Block interactions in visit mode
        if self._visiting_friend:
            return
        
        if self._iso_view is None or self._iso_view.grid is None:
            return
        
        # Check if clicked on a locked zone
        if not self._iso_view.grid.is_tile_unlocked(grid_x, grid_y):
            self._show_zone_unlock_dialog(grid_x, grid_y)
            return
        
        # Handle building placement mode
        if self._placement_mode and self._placement_building_type is not None:
            self._place_building(grid_x, grid_y)
            return
        
        # Handle decoration placement mode
        if self._placement_mode and self._placement_decoration_type is not None:
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
        
        # Block interactions in visit mode (view only)
        if self._visiting_friend:
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
        self._move_decoration_id = decoration_id
        self._placement_mode = True
        self._placement_decoration_type = decoration.type
        self._placement_direction = decoration.direction
        
        # Get footprint and info
        footprint = DECORATION_FOOTPRINTS.get(decoration.type, (1, 1))
        info = DECORATION_INFO.get(decoration.type, {})
        can_rotate = info.get("can_rotate", False)
        
        # Update UI with same format as placing
        facing_label = "→ Right" if self._placement_direction == Direction.EAST else "← Left (Flipped)"
        if can_rotate:
            self.placement_label.setText(
                f"📍 Moving: {info.get('name', decoration.type.value)}\n"
                f"Facing: {facing_label}\n"
                f"Press R to flip • ESC to cancel"
            )
        else:
            self.placement_label.setText(
                f"📍 Moving: {info.get('name', decoration.type.value)}\n"
                f"Click to place • ESC to cancel"
            )
        self.placement_label.show()
        self.shop_btn.hide()
        self.market_btn.hide()
        self.cancel_btn.show()
        
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
        if decoration_id in self._decoration_sprites:
            sprite = self._decoration_sprites.pop(decoration_id)
            self._iso_view.scene().removeItem(sprite)
        
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
        self._move_building_id = building_id
        self._placement_mode = True
        self._placement_building_type = building.type
        
        # Update UI
        from ..core.constants import BUILDING_FOOTPRINTS
        footprint = BUILDING_FOOTPRINTS.get(building.type, (2, 2))
        
        self.placement_label.setText(
            f"📍 Moving: {building.display_name}\n"
            f"Click on the farm to place ({footprint[0]}x{footprint[1]} tiles)\n"
            f"Press ESC or click Cancel to cancel"
        )
        self.placement_label.show()
        self.shop_btn.hide()
        self.market_btn.hide()
        self.cancel_btn.show()
        
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
        self._placement_mode = True
        self._placement_building_type = building_type
        
        # Update UI
        from ..core.constants import BUILDING_FOOTPRINTS
        footprint = BUILDING_FOOTPRINTS.get(building_type, (2, 2))
        
        self.placement_label.setText(
            f"📍 Placing: {building_type.value.replace('_', ' ').title()}\n"
            f"Click on the farm to place ({footprint[0]}x{footprint[1]} tiles)\n"
            f"Press ESC or click Cancel to cancel"
        )
        self.placement_label.show()
        self.shop_btn.hide()
        self.market_btn.hide()
        self.cancel_btn.show()
        
        # Show placement preview with grid
        if self._iso_view is not None:
            self._iso_view.show_placement_preview(footprint[0], footprint[1])
        
        logger.info(f"Started placement mode for {building_type.value}")
    
    def _cancel_placement_mode(self) -> None:
        """Cancel building/decoration placement mode."""
        self._placement_mode = False
        self._placement_building_type = None
        self._placement_decoration_type = None
        self._placement_direction = Direction.EAST
        self._move_building_id = None
        self._move_decoration_id = None
        
        self.placement_label.hide()
        self.cancel_btn.hide()
        self.shop_btn.show()
        self.market_btn.show()
        
        # Hide placement preview and grid
        if self._iso_view is not None:
            self._iso_view.hide_placement_preview()
        
        logger.info("Cancelled placement mode")
    
    def _place_building(self, grid_x: int, grid_y: int) -> None:
        """Place a building at the specified location."""
        if self.farm is None or self._iso_view is None or self._iso_view.grid is None:
            return
        
        if self._placement_building_type is None:
            return
        
        building_type = self._placement_building_type
        
        from ..core.constants import BUILDING_FOOTPRINTS
        footprint = BUILDING_FOOTPRINTS.get(building_type, (2, 2))
        width, height = footprint
        
        # Check if we're in move mode
        is_move_mode = self._move_building_id is not None
        
        # For move mode, we need to temporarily clear the old building's tiles
        # so we can check if the new position is valid
        old_position = None
        if is_move_mode:
            building = self.farm.buildings.get(self._move_building_id)
            if building:
                old_position = building.position
                # Temporarily clear old tiles
                self._iso_view.grid.clear_building(self._move_building_id)
        
        # Check if we can place here
        if not self._iso_view.grid.can_place_building(grid_x, grid_y, width, height):
            logger.warning(f"Cannot place building at ({grid_x}, {grid_y})")
            # Restore old tiles if in move mode
            if is_move_mode and old_position:
                self._iso_view.grid.mark_building(
                    self._move_building_id,
                    old_position[0], old_position[1],
                    width, height
                )
            return
        
        if is_move_mode:
            # === MOVE EXISTING BUILDING ===
            building = self.farm.buildings.get(self._move_building_id)
            if building is None:
                return
            
            # Update building position
            building.position = (grid_x, grid_y)
            
            # Mark new tiles as occupied
            self._iso_view.grid.mark_building(building.id, grid_x, grid_y, width, height)
            
            # Update sprite position
            pen_sprite = self._building_sprites.get(building.id)
            if pen_sprite:
                pen_sprite.set_world_pos(float(grid_x), float(grid_y))
                
                # Also need to move animal sprites inside this building
                for animal_id in building.animals:
                    animal_sprite = self._animal_sprites.get(animal_id)
                    if animal_sprite:
                        # Update the sprite's pen bounds
                        animal_sprite.set_pen_bounds(
                            grid_x, grid_y,
                            grid_x + width, grid_y + height
                        )
            
            logger.info(f"Moved {building.display_name} to ({grid_x}, {grid_y})")
            
            # Clear move mode
            self._move_building_id = None
        else:
            # === CREATE NEW BUILDING ===
            # Get cost and check affordability
            cost = BUILDING_PURCHASE_COSTS.get(building_type, 500)
            if not self.farm.spend_money(cost, f"Purchase {building_type.value}"):
                logger.warning(f"Cannot afford {building_type.value}")
                return
            
            # Create building model
            building = Building(
                type=building_type,
                position=(grid_x, grid_y),
            )
            self.farm.add_building(building)
            
            # Mark tiles as occupied
            self._iso_view.grid.mark_building(building.id, grid_x, grid_y, width, height)
            
            # Create pen sprite
            pen_sprite = PenSprite(
                world_x=float(grid_x),
                world_y=float(grid_y),
                pen_width=width,
                pen_height=height,
            )
            pen_sprite.building_id = building.id  # Set building ID for click detection
            self._iso_view.add_sprite(f"building_{building.id}", pen_sprite)
            self._building_sprites[building.id] = pen_sprite
            
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
        self._placement_mode = True
        self._placement_decoration_type = decoration_type
        self._placement_building_type = None  # Clear building type
        self._placement_direction = Direction.EAST  # Reset direction (EAST = default, WEST = flipped)
        
        # Get footprint
        footprint = DECORATION_FOOTPRINTS.get(decoration_type, (1, 1))
        info = DECORATION_INFO.get(decoration_type, {})
        can_rotate = info.get("can_rotate", False)
        
        # Terse format with direction info
        facing_label = "→ Right" if self._placement_direction == Direction.EAST else "← Left (Flipped)"
        if can_rotate:
            self.placement_label.setText(
                f"📍 Placing: {info.get('name', decoration_type.value)}\n"
                f"Facing: {facing_label}\n"
                f"Press R to flip • ESC to cancel"
            )
        else:
            self.placement_label.setText(
                f"📍 Placing: {info.get('name', decoration_type.value)}\n"
                f"Click to place • ESC to cancel"
            )
        self.placement_label.show()
        self.shop_btn.hide()
        self.market_btn.hide()
        self.cancel_btn.show()
        
        # Show placement preview with grid
        if self._iso_view is not None:
            self._iso_view.show_placement_preview(footprint[0], footprint[1])
        
        logger.info(f"Started decoration placement mode for {decoration_type.value}")
    
    def _rotate_placement(self) -> None:
        """Rotate the current placement by 90 degrees."""
        if not self._placement_mode:
            return
        
        if self._placement_decoration_type is not None:
            info = DECORATION_INFO.get(self._placement_decoration_type, {})
            if not info.get("can_rotate", False):
                return
            
            # Toggle between EAST (default) and WEST (flipped)
            if self._placement_direction == Direction.EAST:
                self._placement_direction = Direction.WEST
            else:
                self._placement_direction = Direction.EAST
            
            # Update preview text
            footprint = DECORATION_FOOTPRINTS.get(self._placement_decoration_type, (1, 1))
            facing_label = "→ Right" if self._placement_direction == Direction.EAST else "← Left (Flipped)"
            
            self.placement_label.setText(
                f"📍 Placing: {info.get('name', self._placement_decoration_type.value)}\n"
                f"Facing: {facing_label}\n"
                f"Press R to flip • ESC to cancel"
            )
            
            logger.debug(f"Flipped to {self._placement_direction.name}")
    
    def _place_decoration(self, grid_x: int, grid_y: int) -> None:
        """Place a decoration at the specified location."""
        if self.farm is None or self._iso_view is None or self._iso_view.grid is None:
            return
        
        if self._placement_decoration_type is None:
            return
        
        decoration_type = self._placement_decoration_type
        footprint = DECORATION_FOOTPRINTS.get(decoration_type, (1, 1))
        
        # Adjust footprint for rotation
        if self._placement_direction in (Direction.EAST, Direction.WEST):
            width, height = footprint[1], footprint[0]
        else:
            width, height = footprint
        
        # Check if we're in move mode
        is_move_mode = self._move_decoration_id is not None
        
        # For move mode, clear old tiles first
        if is_move_mode:
            decoration = self.farm.decorations.get(self._move_decoration_id)
            if decoration:
                self._iso_view.grid.clear_building(self._move_decoration_id)
        
        # Check if we can place here
        if not self._iso_view.grid.can_place_building(grid_x, grid_y, width, height):
            logger.warning(f"Cannot place decoration at ({grid_x}, {grid_y})")
            # Restore old tiles if in move mode
            if is_move_mode:
                decoration = self.farm.decorations.get(self._move_decoration_id)
                if decoration:
                    old_w, old_h = decoration.rotated_footprint
                    self._iso_view.grid.mark_building(
                        self._move_decoration_id,
                        decoration.position[0], decoration.position[1],
                        old_w, old_h
                    )
            return
        
        if is_move_mode:
            # === MOVE EXISTING DECORATION ===
            decoration = self.farm.decorations.get(self._move_decoration_id)
            if decoration is None:
                return
            
            # Update position and direction
            decoration.position = (grid_x, grid_y)
            decoration.direction = self._placement_direction
            
            # Mark new tiles
            self._iso_view.grid.mark_building(decoration.id, grid_x, grid_y, width, height)
            
            # Update sprite
            deco_sprite = self._decoration_sprites.get(decoration.id)
            if deco_sprite:
                deco_sprite.set_world_pos(float(grid_x), float(grid_y))
                deco_sprite.set_direction(self._placement_direction)
            
            logger.info(f"Moved {decoration.display_name} to ({grid_x}, {grid_y})")
            self._move_decoration_id = None
        else:
            # === CREATE NEW DECORATION ===
            cost = DECORATION_COSTS.get(decoration_type, 100)
            if not self.farm.spend_money(cost, f"Purchase {decoration_type.value}"):
                logger.warning(f"Cannot afford {decoration_type.value}")
                return
            
            # Create decoration model
            decoration = Decoration(
                type=decoration_type,
                position=(grid_x, grid_y),
                direction=self._placement_direction,
            )
            self.farm.add_decoration(decoration)
            
            # Mark tiles as occupied
            self._iso_view.grid.mark_building(decoration.id, grid_x, grid_y, width, height)
            
            # Create sprite
            deco_sprite = DecorationSprite(
                world_x=float(grid_x),
                world_y=float(grid_y),
                decoration_type=decoration_type,
                direction=self._placement_direction,
                footprint_width=width,
                footprint_height=height,
            )
            deco_sprite.decoration_id = decoration.id
            self._iso_view.add_sprite(f"decoration_{decoration.id}", deco_sprite)
            self._decoration_sprites[decoration.id] = deco_sprite
            
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
        
        building = self.farm.buildings.get(building_id)
        if not building:
            logger.warning(f"Building {building_id} not found")
            return
        
        # Check building can accept this animal
        if not building.can_add_animal(animal_type):
            logger.warning(f"Building cannot accept {animal_type.value}")
            return
        
        # Check affordability
        cost = ANIMAL_PURCHASE_PRICES.get(animal_type, 100)
        if not self.farm.spend_money(cost, f"Purchase {animal_type.value}"):
            logger.warning(f"Cannot afford {animal_type.value}")
            return
        
        # Create animal model
        animal = Animal(type=animal_type, building_id=building_id)
        self.farm.add_animal(animal)
        building.add_animal(animal.id)
        
        # Get pen sprite for bounds
        pen_sprite = self._building_sprites.get(building_id)
        if pen_sprite:
            bounds = pen_sprite.get_animal_bounds()
            
            # Random position within pen
            import random
            start_x = random.uniform(bounds[0], bounds[2])
            start_y = random.uniform(bounds[1], bounds[3])
        else:
            # Fallback to building center
            start_x, start_y = building.center_position
        
        # Create animal sprite with wandering
        animal_sprite = AnimalSprite(
            world_x=start_x,
            world_y=start_y,
            animal_type=animal_type.value,
            animal_id=animal.id,
        )
        
        # Set growth stage from animal model
        animal_sprite.growth_stage = animal.growth_stage.value
        
        # Set pen bounds for wandering
        if pen_sprite:
            bounds = pen_sprite.get_animal_bounds()
            animal_sprite.set_pen_bounds(bounds[0], bounds[1], bounds[2], bounds[3])
        
        self._iso_view.add_sprite(f"animal_{animal.id}", animal_sprite)
        self._animal_sprites[animal.id] = animal_sprite
        
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
        if animal_id in self._animal_sprites:
            sprite = self._animal_sprites.pop(animal_id)
            if self._iso_view:
                self._iso_view.remove_sprite(f"animal_{animal_id}")
        
        # Update UI
        self._update_ui()
        
        # Auto-save after animal sale
        self.save_game()
    
    def _on_visit_friend_clicked(self) -> None:
        """Handle visit friend button click."""
        from .dialogs import AccountCreationDialog, VisitFriendDialog
        from ..data.account_manager import get_account_manager
        
        # Don't allow if already visiting
        if self._visiting_friend:
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
        self._home_farm = self.farm
        self._home_unlocked_zones = self._iso_view.grid.unlocked_zones
        self._visiting_friend = True
        self._visiting_username = username
        
        # Load friend's farm
        try:
            friend_farm = Farm.from_dict(farm_data)
            self.farm = friend_farm
            
            # Update grid to show friend's unlocked zones
            self._iso_view.grid.unlocked_zones = friend_farm.unlocked_zones
            
            # Clear existing sprites
            self._clear_all_sprites()
            
            # Recreate sprites for friend's farm
            self._recreate_sprites_from_save()
            
            # Update UI for visit mode
            self._enter_visit_mode(username)
            
            logger.info(f"Now visiting {username}'s farm with {friend_farm.unlocked_zones} unlocked zones")
        except Exception as e:
            logger.error(f"Failed to load friend's farm: {e}")
            self._home_farm = None
            self._visiting_friend = False
            self._visiting_username = None
    
    def _enter_visit_mode(self, username: str) -> None:
        """Enter visit mode UI."""
        # Update title
        self.setWindowTitle(f"Visiting {username}'s Farm - Anki Animal Ranch")
        
        # Update header
        if hasattr(self, 'header_label'):
            self.header_label.setText(f"👥 Visiting: {username}")
        
        # Hide normal buttons, show return home
        self.shop_btn.hide()
        self.market_btn.hide()
        self.visit_btn.hide()
        self.return_home_btn.show()
        
        # Update money display to show "Viewing"
        if hasattr(self, 'money_label'):
            self.money_label.setText("👀 View Only")
    
    def _on_return_home_clicked(self) -> None:
        """Return to home farm from visit."""
        if not self._visiting_friend or self._home_farm is None:
            return
        
        logger.info("Returning home from visit")
        
        # Restore home farm
        self.farm = self._home_farm
        self._home_farm = None
        self._visiting_friend = False
        self._visiting_username = None
        
        # Restore home farm's unlocked zones
        if hasattr(self, '_home_unlocked_zones'):
            self._iso_view.grid.unlocked_zones = self._home_unlocked_zones
            self._home_unlocked_zones = None
        
        # Clear and recreate sprites
        self._clear_all_sprites()
        self._recreate_sprites_from_save()
        
        # Exit visit mode UI
        self._exit_visit_mode()
    
    def _exit_visit_mode(self) -> None:
        """Exit visit mode UI."""
        # Restore title
        self.setWindowTitle(f"Anki Animal Ranch v{VERSION}")
        
        # Restore header
        if hasattr(self, 'header_label'):
            self.header_label.setText("🌾 Anki Animal Ranch")
        
        # Show normal buttons
        self.shop_btn.show()
        self.market_btn.show()
        self.visit_btn.show()
        self.return_home_btn.hide()
        
        # Update UI
        self._update_ui()
    
    def _clear_all_sprites(self) -> None:
        """Clear all entity sprites from the view."""
        if self._iso_view is None:
            return
        
        # Remove building sprites
        for building_id, sprite in list(self._building_sprites.items()):
            self._iso_view.remove_sprite(f"building_{building_id}")
        self._building_sprites.clear()
        
        # Remove animal sprites
        for animal_id, sprite in list(self._animal_sprites.items()):
            self._iso_view.remove_sprite(f"animal_{animal_id}")
        self._animal_sprites.clear()
        
        # Remove decoration sprites
        for deco_id, sprite in list(self._decoration_sprites.items()):
            self._iso_view.remove_sprite(f"decoration_{deco_id}")
        self._decoration_sprites.clear()
    
    def _sync_farm_to_cloud(self) -> None:
        """Sync current farm to cloud (if account exists)."""
        from ..data.account_manager import get_account_manager
        from ..network import sync_farm, is_online_available
        
        # Don't sync while visiting
        if self._visiting_friend:
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
        logger.info("Settings clicked")
        # TODO: Open settings dialog
    
    def _on_animal_produced(self, **kwargs) -> None:
        """Handle animal production event for visual feedback."""
        animal_id = kwargs.get("animal_id")
        product_type = kwargs.get("product_type")
        quantity = kwargs.get("quantity", 1)
        
        logger.debug(f"Production event: {product_type} x{quantity} from {animal_id}")
        
        # Get animal sprite and show production effect
        if animal_id and animal_id in self._animal_sprites and self._iso_view:
            sprite = self._animal_sprites[animal_id]
            
            # Show floating effect at animal's position
            product_name = product_type.value if hasattr(product_type, 'value') else str(product_type)
            self._iso_view.show_production_effect(
                world_x=sprite.world_x,
                world_y=sprite.world_y,
                product_type=product_name,
            )
        
        # Update UI immediately
        self._update_ui()
    
    def simulate_card_answer(self, ease: int = 3) -> None:
        """
        Simulate answering an Anki card (for testing outside Anki).
        
        Args:
            ease: Simulated ease button (1-4)
        """
        self.on_card_answered(ease)
    
    def _on_study_clicked(self) -> None:
        """Handle study button click - simulates passing 1 hour of game time."""
        if self.time_system is None or self.farm is None:
            return
        
        # Advance 1 hour of game time
        self.time_system.advance_time(hours=1)
        
        # Update growth system
        if self.growth_system is not None:
            events = self.growth_system.update(hours_passed=1.0)
            
            # Show feedback for events
            for event in events:
                if event["type"] == "product_produced":
                    logger.info(
                        f"🥚 {event['animal_type'].capitalize()} produced "
                        f"{event['quantity']} {event['product_type']}!"
                    )
                elif event["type"] == "growth_stage_changed":
                    logger.info(
                        f"🌱 {event['animal_type'].capitalize()} grew from "
                        f"{event['old_stage']} to {event['new_stage']}!"
                    )
                    # Update the sprite's growth stage
                    animal_id = event.get("animal_id")
                    logger.info(f"  Looking for sprite: animal_id={animal_id}, in_dict={animal_id in self._animal_sprites}")
                    if animal_id and animal_id in self._animal_sprites:
                        logger.info(f"  Found sprite, setting growth_stage to {event['new_stage']}")
                        self._animal_sprites[animal_id].growth_stage = event["new_stage"]
                    else:
                        logger.warning(f"  Sprite not found for animal_id={animal_id}")
        
        # Log animal status summary
        if self.farm.animals:
            for animal in list(self.farm.animals.values())[:3]:  # Show first 3
                logger.debug(
                    f"  {animal.type.value}: {animal.maturity:.0%} mature, "
                    f"stage={animal.growth_stage.value}, "
                    f"can_produce={animal.is_mature}"
                )
        
        # Update statistics
        self.farm.statistics.total_cards_answered += 1
        
        # Auto-save every 25 "cards"
        if self.farm.statistics.total_cards_answered % 25 == 0:
            self.save_game()
            logger.info(f"💾 Auto-saved after {self.farm.statistics.total_cards_answered} study clicks")
        
        # Update UI
        self._update_ui()
        
        logger.info(f"⏰ Advanced 1 hour: {self.time_system.current_time.format_full()}")
    
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
        
        # Track cards answered
        self.farm.statistics.total_cards_answered += 1
        
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
                        f"🌱 {event['animal_type'].capitalize()} grew to "
                        f"{event['new_stage']}!"
                    )
                    # Update the sprite's growth stage
                    animal_id = event.get("animal_id")
                    logger.info(f"  Looking for sprite: animal_id={animal_id}, in_dict={animal_id in self._animal_sprites}")
                    if animal_id and animal_id in self._animal_sprites:
                        logger.info(f"  Found sprite, setting growth_stage to {event['new_stage']}")
                        self._animal_sprites[animal_id].growth_stage = event["new_stage"]
                    else:
                        logger.warning(f"  Sprite not found for animal_id={animal_id}")
        
        # Update statistics
        self.farm.statistics.total_cards_answered += 1
        
        # Auto-save every 25 cards
        if self.farm.statistics.total_cards_answered % 25 == 0:
            self.save_game()
            logger.info(f"💾 Auto-saved after {self.farm.statistics.total_cards_answered} cards")
        
        # Update UI
        self._update_ui()
        
        logger.debug(f"Card answered with ease {ease}, {hours_passed}h passed")
    
    def start_game(self) -> None:
        """Start the game loop."""
        if self._is_running:
            return
        
        self._is_running = True
        if self._game_timer:
            self._game_timer.start(FRAME_TIME_MS)
        
        logger.info("Game started")
    
    def pause_game(self) -> None:
        """Pause the game loop."""
        self._is_running = False
        if self._game_timer:
            self._game_timer.stop()
        
        logger.info("Game paused")
    
    def save_game(self) -> None:
        """Save the current game state."""
        if self.farm is None or self.time_system is None:
            return
        
        # Don't save while visiting friend's farm
        if self._visiting_friend:
            return
        
        save_manager = get_save_manager()
        if save_manager.save(self.farm, self.time_system):
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
        
        self.farm, self.time_system = loaded
        
        # Update growth system with new farm
        self.growth_system = GrowthSystem(self.farm)
        
        # Recreate sprites for loaded entities
        self._recreate_sprites_from_save()
        
        # Update UI
        self._update_ui()
        
        logger.info(f"📂 Game loaded! (${self.farm.money}, {len(self.farm.animals)} animals)")
    
    def _recreate_sprites_from_save(self) -> None:
        """Recreate sprites for all buildings and animals from loaded save."""
        if self._iso_view is None or self.farm is None:
            return
        
        from ..core.constants import BUILDING_FOOTPRINTS
        
        # Clear existing building and animal sprites
        for sprite_id in list(self._building_sprites.keys()):
            self._iso_view.remove_sprite(f"building_{sprite_id}")
        for sprite_id in list(self._animal_sprites.keys()):
            self._iso_view.remove_sprite(f"animal_{sprite_id}")
        
        self._building_sprites.clear()
        self._animal_sprites.clear()
        
        # Recreate building sprites
        for building_id, building in self.farm.buildings.items():
            footprint = BUILDING_FOOTPRINTS.get(building.type, (2, 2))
            width, height = footprint
            
            pen_sprite = PenSprite(
                world_x=float(building.position[0]),
                world_y=float(building.position[1]),
                pen_width=width,
                pen_height=height,
            )
            pen_sprite.building_id = building_id  # Set building ID for click detection
            self._iso_view.add_sprite(f"building_{building_id}", pen_sprite)
            self._building_sprites[building_id] = pen_sprite
            
            # Mark tiles as occupied
            if self._iso_view.grid:
                self._iso_view.grid.mark_building(
                    building_id,
                    building.position[0],
                    building.position[1],
                    width,
                    height,
                )
        
        # Recreate animal sprites
        import random
        for animal_id, animal in self.farm.animals.items():
            # Get pen bounds from building
            pen_sprite = self._building_sprites.get(animal.building_id)
            if pen_sprite:
                bounds = pen_sprite.get_animal_bounds()
                start_x = random.uniform(bounds[0], bounds[2])
                start_y = random.uniform(bounds[1], bounds[3])
            else:
                start_x, start_y = animal.position
            
            animal_sprite = AnimalSprite(
                world_x=start_x,
                world_y=start_y,
                animal_type=animal.type.value,
                animal_id=animal.id,
            )
            
            # Set growth stage from animal model
            animal_sprite.growth_stage = animal.growth_stage.value
            
            # Set pen bounds for wandering
            if pen_sprite:
                bounds = pen_sprite.get_animal_bounds()
                animal_sprite.set_pen_bounds(bounds[0], bounds[1], bounds[2], bounds[3])
            
            self._iso_view.add_sprite(f"animal_{animal_id}", animal_sprite)
            self._animal_sprites[animal_id] = animal_sprite
        
        # Clear and recreate decoration sprites
        for sprite_id in list(self._decoration_sprites.keys()):
            self._iso_view.remove_sprite(f"decoration_{sprite_id}")
        self._decoration_sprites.clear()
        
        # Recreate decoration sprites
        for decoration_id, decoration in self.farm.decorations.items():
            footprint = decoration.rotated_footprint
            width, height = footprint
            
            deco_sprite = DecorationSprite(
                world_x=float(decoration.position[0]),
                world_y=float(decoration.position[1]),
                decoration_type=decoration.type,
                direction=decoration.direction,
                footprint_width=width,
                footprint_height=height,
            )
            deco_sprite.decoration_id = decoration_id
            self._iso_view.add_sprite(f"decoration_{decoration_id}", deco_sprite)
            self._decoration_sprites[decoration_id] = deco_sprite
            
            # Mark tiles as occupied
            if self._iso_view.grid:
                self._iso_view.grid.mark_building(
                    decoration_id,
                    decoration.position[0],
                    decoration.position[1],
                    width,
                    height,
                )
        
        logger.info(f"Recreated {len(self._building_sprites)} buildings, {len(self._animal_sprites)} animals, {len(self._decoration_sprites)} decorations")
    
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
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            if self._placement_mode:
                self._cancel_placement_mode()
                event.accept()
                return
        elif event.key() == Qt.Key.Key_R:
            if self._placement_mode:
                self._rotate_placement()
                event.accept()
                return
        super().keyPressEvent(event)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        self.pause_game()
        self.save_game()
        
        # Clean up
        if self._game_timer:
            self._game_timer.stop()
        
        if self._iso_view:
            self._iso_view.stop_animation()
        
        logger.info("MainWindow closed")
        super().closeEvent(event)
