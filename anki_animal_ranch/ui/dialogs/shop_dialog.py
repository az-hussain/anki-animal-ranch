"""
Shop dialog for buying buildings and animals.

Provides a clean UI for purchasing:
- Animal housing (coops, pigsties, barns)
- Animals (chickens, pigs, cows)
"""

from __future__ import annotations

from ...utils.logger import get_logger
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.constants import (
    ANIMAL_FEED_MAP,
    ANIMAL_PURCHASE_PRICES,
    BUILDING_CAPACITIES,
    BUILDING_FOOTPRINTS,
    BUILDING_PURCHASE_COSTS,
    DECORATION_COSTS,
    DECORATION_FOOTPRINTS,
    DECORATION_INFO,
    FEED_BUNDLE_SIZES,
    FEED_CONSUMPTION_PER_DAY,
    FEED_PRICES,
    AnimalType,
    BuildingType,
    DecorationType,
    FeedType,
)

if TYPE_CHECKING:
    from ...models.farm import Farm

logger = get_logger(__name__)


# Building info for display
BUILDING_INFO = {
    BuildingType.COOP: {
        "name": "Chicken Coop",
        "emoji": "🐔",
        "description": "Houses chickens. They produce eggs!",
        "animal_type": AnimalType.CHICKEN,
    },
    BuildingType.PIGSTY: {
        "name": "Pig Sty",
        "emoji": "🐷",
        "description": "Houses pigs. They find truffles!",
        "animal_type": AnimalType.PIG,
    },
    BuildingType.BARN: {
        "name": "Cow Barn",
        "emoji": "🐄",
        "description": "Houses cows. They produce milk!",
        "animal_type": AnimalType.COW,
    },
}

# Animal info for display
ANIMAL_INFO = {
    AnimalType.CHICKEN: {
        "name": "Chicken",
        "emoji": "🐔",
        "description": "Produces eggs daily when mature.",
        "product": "🥚 Eggs",
    },
    AnimalType.PIG: {
        "name": "Pig",
        "emoji": "🐷",
        "description": "Finds valuable truffles!",
        "product": "🍄 Truffles",
    },
    AnimalType.COW: {
        "name": "Cow",
        "emoji": "🐄",
        "description": "Produces milk daily when mature.",
        "product": "🥛 Milk",
    },
}

# Feed info for display
FEED_INFO = {
    FeedType.CHICKEN_FEED: {
        "name": "Chicken Feed",
        "emoji": "🌾",
        "description": "Nutritious grain mix for chickens.",
        "animal_emoji": "🐔",
    },
    FeedType.PIG_FEED: {
        "name": "Pig Feed",
        "emoji": "🥕",
        "description": "Hearty vegetable blend for pigs.",
        "animal_emoji": "🐷",
    },
    FeedType.COW_FEED: {
        "name": "Cow Feed",
        "emoji": "🌿",
        "description": "Premium hay and grain for cows.",
        "animal_emoji": "🐄",
    },
}


class ShopItemWidget(QFrame):
    """Widget displaying a single purchasable item."""
    
    clicked = pyqtSignal()
    
    def __init__(
        self,
        name: str,
        emoji: str,
        description: str,
        price: int,
        extra_info: str = "",
        enabled: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.name = name
        self.price = price
        self._enabled = enabled
        
        self._setup_ui(name, emoji, description, price, extra_info, enabled)
    
    def _setup_ui(
        self,
        name: str,
        emoji: str,
        description: str,
        price: int,
        extra_info: str,
        enabled: bool,
    ) -> None:
        """Set up the item widget UI."""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        
        # Style
        bg_color = "#3a4a3a" if enabled else "#2a2a2a"
        border_color = "#5a8f4a" if enabled else "#444"
        text_color = "#fff" if enabled else "#666"
        
        self.setStyleSheet(f"""
            ShopItemWidget {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 8px;
            }}
            ShopItemWidget:hover {{
                background-color: {"#4a5a4a" if enabled else bg_color};
                border-color: {"#6ba85a" if enabled else border_color};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Emoji
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet(f"font-size: 32px; color: {text_color};")
        layout.addWidget(emoji_label)
        
        # Info column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(name)
        name_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color};")
        info_layout.addWidget(name_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"font-size: 11px; color: {'#aaa' if enabled else '#555'};")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        if extra_info:
            extra_label = QLabel(extra_info)
            extra_label.setStyleSheet(f"font-size: 10px; color: {'#8a8' if enabled else '#454'};")
            info_layout.addWidget(extra_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Price
        price_label = QLabel(f"${price:,}")
        price_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {"#f0c040" if enabled else "#665"};
        """)
        layout.addWidget(price_label)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
    
    def mousePressEvent(self, event) -> None:
        if self._enabled:
            self.clicked.emit()
        super().mousePressEvent(event)


class ShopDialog(QDialog):
    """
    Shop dialog for purchasing buildings and animals.
    
    Signals:
        building_purchased: Emitted when a building is bought (BuildingType)
        animal_purchased: Emitted when an animal is bought (AnimalType, building_id)
        decoration_purchased: Emitted when a decoration is bought (DecorationType)
    """
    
    building_purchased = pyqtSignal(object)  # BuildingType
    animal_purchased = pyqtSignal(object, str)  # AnimalType, building_id
    decoration_purchased = pyqtSignal(object)  # DecorationType
    
    def __init__(
        self,
        farm: Farm,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.farm = farm
        self._selected_building_id: str | None = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("🏪 Farm Shop")
        self.setMinimumSize(500, 400)
        self.resize(550, 500)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2c2c2c;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #333;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #ccc;
                padding: 10px 20px;
                border: 1px solid #444;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #4a5a4a;
                color: #fff;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Money display
        self.money_label = QLabel(f"💰 Your Money: ${self.farm.money:,}")
        self.money_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #f0c040;
            padding: 10px;
            background-color: #3a3a3a;
            border-radius: 6px;
        """)
        layout.addWidget(self.money_label)
        
        # Tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Buildings tab
        buildings_tab = self._create_buildings_tab()
        tabs.addTab(buildings_tab, "🏠 Buildings")
        
        # Animals tab
        animals_tab = self._create_animals_tab()
        tabs.addTab(animals_tab, "🐔 Animals")
        
        # Feed tab
        feed_tab = self._create_feed_tab()
        tabs.addTab(feed_tab, "🌾 Feed")
        
        # Decorations tab
        decorations_tab = self._create_decorations_tab()
        tabs.addTab(decorations_tab, "🎨 Decor")
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 12px 30px;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def _create_buildings_tab(self) -> QWidget:
        """Create the buildings purchase tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Instructions
        instructions = QLabel("Purchase buildings to house your animals. Click to buy, then place on your farm!")
        instructions.setStyleSheet("color: #aaa; font-size: 12px; padding: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Scroll area for items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        
        # Add building items
        for building_type in [BuildingType.COOP, BuildingType.PIGSTY, BuildingType.BARN]:
            info = BUILDING_INFO.get(building_type, {})
            price = BUILDING_PURCHASE_COSTS.get(building_type, 500)
            footprint = BUILDING_FOOTPRINTS.get(building_type, (2, 2))
            capacity = BUILDING_CAPACITIES.get(building_type, [5])[0]
            
            can_afford = self.farm.money >= price
            
            item = ShopItemWidget(
                name=info.get("name", building_type.value),
                emoji=info.get("emoji", "🏠"),
                description=info.get("description", ""),
                price=price,
                extra_info=f"Size: {footprint[0]}x{footprint[1]} tiles • Capacity: {capacity} animals",
                enabled=can_afford,
            )
            item.clicked.connect(lambda bt=building_type: self._on_building_clicked(bt))
            scroll_layout.addWidget(item)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_animals_tab(self) -> QWidget:
        """Create the animals purchase tab with animal-first selection."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Check if user has any animal housing
        housing_buildings = [
            b for b in self.farm.buildings.values()
            if b.type in (BuildingType.COOP, BuildingType.PIGSTY, BuildingType.BARN)
        ]
        
        if not housing_buildings:
            # No buildings message
            no_buildings = QLabel(
                "🏠 You need to build animal housing first!\n\n"
                "Go to the Buildings tab and purchase a Coop, Pig Sty, or Barn "
                "before you can buy animals."
            )
            no_buildings.setStyleSheet("""
                color: #f88;
                font-size: 14px;
                padding: 30px;
                background-color: #3a2a2a;
                border-radius: 8px;
            """)
            no_buildings.setWordWrap(True)
            no_buildings.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_buildings)
            layout.addStretch()
            return widget
        
        # Animal type selector
        animal_label = QLabel("1. Select animal type to buy:")
        animal_label.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold;")
        layout.addWidget(animal_label)
        
        # Animal type buttons
        self.animal_type_buttons: dict[AnimalType, QPushButton] = {}
        animal_row = QHBoxLayout()
        
        for animal_type in [AnimalType.CHICKEN, AnimalType.PIG, AnimalType.COW]:
            info = ANIMAL_INFO.get(animal_type, {})
            price = ANIMAL_PURCHASE_PRICES.get(animal_type, 100)
            
            # Check if there are any buildings for this animal type
            matching_buildings = [b for b in housing_buildings if b.allowed_animal_type == animal_type]
            has_housing = len(matching_buildings) > 0
            available_space = any(not b.is_full for b in matching_buildings)
            
            btn = QPushButton(f"{info.get('emoji', '🐔')}\n{info.get('name', animal_type.value)}\n${price}")
            btn.setCheckable(True)
            btn.setMinimumSize(80, 70)
            
            if not has_housing:
                tooltip = f"No {info.get('name', '')} housing built"
                enabled = False
            elif not available_space:
                tooltip = "All buildings full"
                enabled = False
            else:
                tooltip = f"Buy a {info.get('name', '')} for ${price}"
                enabled = True
            
            btn.setToolTip(tooltip)
            btn.setEnabled(enabled)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#3a3a3a" if enabled else "#2a2a2a"};
                    color: {"#ccc" if enabled else "#666"};
                    border: 2px solid #444;
                    padding: 8px;
                border-radius: 8px;
                    font-size: 12px;
                }}
                QPushButton:checked {{
                    background-color: #4a5a4a;
                    border-color: #6ba85a;
                    color: #fff;
                }}
                QPushButton:hover {{
                    background-color: {"#4a4a4a" if enabled else "#2a2a2a"};
                }}
            """)
            btn.clicked.connect(lambda checked, at=animal_type: self._on_animal_type_selected(at))
            animal_row.addWidget(btn)
            self.animal_type_buttons[animal_type] = btn
        
        animal_row.addStretch()
        layout.addLayout(animal_row)
        
        # Building selector label
        building_label = QLabel("2. Select which pen to add to:")
        building_label.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(building_label)
        
        # Scroll area for buildings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.buildings_scroll_content = QWidget()
        self.buildings_layout = QVBoxLayout(self.buildings_scroll_content)
        self.buildings_layout.setSpacing(8)
        
        # Placeholder
        placeholder = QLabel("👆 Select an animal type above")
        placeholder.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buildings_layout.addWidget(placeholder)
        
        scroll.setWidget(self.buildings_scroll_content)
        layout.addWidget(scroll)
        
        # Store for later updates
        self.building_buttons: dict[str, QPushButton] = {}
        self._selected_animal_type: AnimalType | None = None
        
        return widget
    
    def _on_animal_type_selected(self, animal_type: AnimalType) -> None:
        """Handle animal type selection."""
        # Update button states
        for at, btn in self.animal_type_buttons.items():
            btn.setChecked(at == animal_type)
        
        self._selected_animal_type = animal_type
        self._update_buildings_list()
    
    def _on_building_clicked(self, building_type: BuildingType) -> None:
        """Handle building purchase click."""
        price = BUILDING_PURCHASE_COSTS.get(building_type, 500)
        
        if self.farm.money < price:
            logger.warning(f"Cannot afford {building_type.value}")
            return
        
        logger.info(f"Purchased building: {building_type.value}")
        self.building_purchased.emit(building_type)
        self.close()
    
    def _update_buildings_list(self) -> None:
        """Update the buildings list based on selected animal type."""
        # Clear existing items
        while self.buildings_layout.count():
            item = self.buildings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.building_buttons.clear()
        
        if not self._selected_animal_type:
            placeholder = QLabel("👆 Select an animal type above")
            placeholder.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.buildings_layout.addWidget(placeholder)
            return
        
        # Get buildings that can house this animal type
        matching_buildings = [
            b for b in self.farm.buildings.values()
            if b.allowed_animal_type == self._selected_animal_type
        ]
        
        if not matching_buildings:
            no_buildings = QLabel(
                f"No housing for this animal type.\n"
                f"Build a {BUILDING_INFO.get(self._get_building_type_for_animal(self._selected_animal_type), {}).get('name', 'pen')} first!"
            )
            no_buildings.setStyleSheet("color: #f88; font-size: 13px; padding: 20px;")
            no_buildings.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.buildings_layout.addWidget(no_buildings)
            return
        
        # Animal info for price
        animal_info = ANIMAL_INFO.get(self._selected_animal_type, {})
        price = ANIMAL_PURCHASE_PRICES.get(self._selected_animal_type, 100)
        can_afford = self.farm.money >= price
        
        # Add building items
        for building in matching_buildings:
            binfo = BUILDING_INFO.get(building.type, {})
            capacity_text = f"{building.current_occupancy}/{building.capacity}"
            is_full = building.is_full
            enabled = can_afford and not is_full
            
            # Create building row widget
            row = QFrame()
            row.setStyleSheet(f"""
                QFrame {{
                    background-color: {"#3a4a3a" if enabled else "#2a2a2a"};
                    border: 2px solid {"#5a8f4a" if enabled else "#444"};
                    border-radius: 8px;
                    padding: 4px;
                }}
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)
            
            # Building info
            info_layout = QVBoxLayout()
            name_label = QLabel(f"{binfo.get('emoji', '🏠')} {building.display_name}")
            name_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {'#fff' if enabled else '#666'};")
            info_layout.addWidget(name_label)
            
            capacity_label = QLabel(f"Capacity: {capacity_text}")
            status_color = "#8a8" if not is_full else "#a66"
            capacity_label.setStyleSheet(f"font-size: 12px; color: {status_color if enabled else '#555'};")
            info_layout.addWidget(capacity_label)
            
            row_layout.addLayout(info_layout, stretch=1)
            
            # Status / Buy button
            if is_full:
                status_label = QLabel("FULL")
                status_label.setStyleSheet("color: #a66; font-weight: bold; font-size: 12px;")
                row_layout.addWidget(status_label)
            elif not can_afford:
                status_label = QLabel("Can't afford")
                status_label.setStyleSheet("color: #a86; font-size: 11px;")
                row_layout.addWidget(status_label)
            else:
                buy_btn = QPushButton(f"Buy ${price}")
                buy_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #5a8f4a;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #6ba85a;
                    }
                """)
                buy_btn.clicked.connect(lambda checked, bid=building.id: self._on_buy_animal(bid))
                row_layout.addWidget(buy_btn)
                self.building_buttons[building.id] = buy_btn
            
            self.buildings_layout.addWidget(row)
        
        self.buildings_layout.addStretch()
    
    def _get_building_type_for_animal(self, animal_type: AnimalType) -> BuildingType | None:
        """Get the building type that houses this animal type."""
        mapping = {
            AnimalType.CHICKEN: BuildingType.COOP,
            AnimalType.PIG: BuildingType.PIGSTY,
            AnimalType.COW: BuildingType.BARN,
        }
        return mapping.get(animal_type)
    
    def _on_buy_animal(self, building_id: str) -> None:
        """Handle buying an animal for a specific building."""
        if not self._selected_animal_type:
            return
        
        price = ANIMAL_PURCHASE_PRICES.get(self._selected_animal_type, 100)
        
        if self.farm.money < price:
            logger.warning(f"Cannot afford {self._selected_animal_type.value}")
            return
        
        logger.info(f"Purchased animal: {self._selected_animal_type.value} for building {building_id}")
        self.animal_purchased.emit(self._selected_animal_type, building_id)
        
        # Refresh the dialog
        self.money_label.setText(f"💰 Your Money: ${self.farm.money:,}")
        self._update_animal_type_buttons()
        self._update_buildings_list()
    
    def _update_animal_type_buttons(self) -> None:
        """Update animal type buttons based on available housing."""
        housing_buildings = [
            b for b in self.farm.buildings.values()
            if b.type in (BuildingType.COOP, BuildingType.PIGSTY, BuildingType.BARN)
        ]
        
        for animal_type, btn in self.animal_type_buttons.items():
            info = ANIMAL_INFO.get(animal_type, {})
            
            # Check if there are any buildings for this animal type
            matching_buildings = [b for b in housing_buildings if b.allowed_animal_type == animal_type]
            has_housing = len(matching_buildings) > 0
            available_space = any(not b.is_full for b in matching_buildings)
            
            enabled = has_housing and available_space
            btn.setEnabled(enabled)
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#3a3a3a" if enabled else "#2a2a2a"};
                    color: {"#ccc" if enabled else "#666"};
                    border: 2px solid #444;
                    padding: 8px;
                    border-radius: 8px;
                    font-size: 12px;
                }}
                QPushButton:checked {{
                    background-color: #4a5a4a;
                    border-color: #6ba85a;
                    color: #fff;
                }}
                QPushButton:hover {{
                    background-color: {"#4a4a4a" if enabled else "#2a2a2a"};
                }}
            """)
    
    def _create_feed_tab(self) -> QWidget:
        """Create the feed purchase tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Instructions
        instructions = QLabel(
            "Keep your animals fed to maintain their health! "
            "Healthy animals produce higher quality products. "
            "Feed is consumed automatically each game day."
        )
        instructions.setStyleSheet("color: #aaa; font-size: 12px; padding: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Scroll area for feed items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        
        # Add feed items for each type
        for feed_type in FeedType:
            feed_widget = self._create_feed_item(feed_type)
            scroll_layout.addWidget(feed_widget)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_feed_item(self, feed_type: FeedType) -> QFrame:
        """Create a widget for purchasing a specific feed type."""
        info = FEED_INFO.get(feed_type, {})
        base_price = FEED_PRICES.get(feed_type, 50)
        consumption = FEED_CONSUMPTION_PER_DAY.get(feed_type, 1)
        
        # Get current stock and animal count
        current_stock = self.farm.get_feed_amount(feed_type)
        
        # Find matching animal type
        matching_animal = None
        for animal_type, ft in ANIMAL_FEED_MAP.items():
            if ft == feed_type:
                matching_animal = animal_type
                break
        
        animal_count = sum(
            1 for a in self.farm.animals.values()
            if a.type == matching_animal
        ) if matching_animal else 0
        
        daily_consumption = consumption * animal_count
        days_remaining = current_stock / daily_consumption if daily_consumption > 0 else float('inf')
        
        # Create frame
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #3a4a3a;
                border: 2px solid #5a8f4a;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        main_layout = QVBoxLayout(frame)
        main_layout.setSpacing(8)
        
        # Header row
        header_layout = QHBoxLayout()
        
        emoji_label = QLabel(f"{info.get('emoji', '🌾')} {info.get('animal_emoji', '')}")
        emoji_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(emoji_label)
        
        name_label = QLabel(info.get("name", feed_type.value))
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Stock status
        if days_remaining == float('inf'):
            if animal_count == 0:
                stock_text = f"Stock: {current_stock} (no animals)"
                stock_color = "#888"
            else:
                stock_text = f"Stock: {current_stock}"
                stock_color = "#8a8"
        elif days_remaining < 10:
            stock_text = f"Stock: {current_stock} ({days_remaining:.0f} days left ⚠️)"
            stock_color = "#fa8"
        else:
            stock_text = f"Stock: {current_stock} ({days_remaining:.0f} days left)"
            stock_color = "#8a8"
        
        stock_label = QLabel(stock_text)
        stock_label.setStyleSheet(f"font-size: 12px; color: {stock_color};")
        header_layout.addWidget(stock_label)
        
        main_layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(info.get("description", ""))
        desc_label.setStyleSheet("font-size: 11px; color: #aaa;")
        main_layout.addWidget(desc_label)
        
        # Purchase buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        price_info = QLabel(f"${base_price}/100 units")
        price_info.setStyleSheet("font-size: 11px; color: #f0c040;")
        buttons_layout.addWidget(price_info)
        
        buttons_layout.addStretch()
        
        # Add buy buttons for each bundle size
        for bundle_size in FEED_BUNDLE_SIZES:
            total_cost = (base_price * bundle_size) // 100
            can_afford = self.farm.money >= total_cost
            
            btn = QPushButton(f"+{bundle_size} (${total_cost})")
            btn.setEnabled(can_afford)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#5a8f4a" if can_afford else "#444"};
                    color: {"white" if can_afford else "#666"};
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {"#6ba85a" if can_afford else "#444"};
                }}
            """)
            btn.clicked.connect(
                lambda checked, ft=feed_type, bs=bundle_size: self._on_buy_feed(ft, bs)
            )
            buttons_layout.addWidget(btn)
        
        main_layout.addLayout(buttons_layout)
        
        return frame
    
    def _on_buy_feed(self, feed_type: FeedType, bundle_size: int) -> None:
        """Handle feed purchase."""
        if self.farm.buy_feed(feed_type, bundle_size):
            logger.info(f"Purchased {bundle_size} {feed_type.value}")
            self.money_label.setText(f"💰 Your Money: ${self.farm.money:,}")
            # Refresh the feed tab to update stock displays
            # Find and update the parent tab widget
            self._refresh_feed_tab()
        else:
            logger.warning(f"Cannot afford {bundle_size} {feed_type.value}")
    
    def _refresh_feed_tab(self) -> None:
        """Refresh the feed tab content."""
        # Find the tab widget and replace the feed tab
        for child in self.children():
            if isinstance(child, QTabWidget):
                # Find the feed tab index
                for i in range(child.count()):
                    if "Feed" in child.tabText(i):
                        # Remove old tab and add new one
                        child.removeTab(i)
                        feed_tab = self._create_feed_tab()
                        child.insertTab(i, feed_tab, "🌾 Feed")
                        child.setCurrentIndex(i)
                        break
                break
    
    def refresh(self) -> None:
        """Refresh the dialog with current farm state."""
        self.money_label.setText(f"💰 Your Money: ${self.farm.money:,}")
    
    # =========================================================================
    # Decorations Tab
    # =========================================================================
    
    def _create_decorations_tab(self) -> QWidget:
        """Create the decorations purchase tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Instructions
        instructions = QLabel(
            "Decorate your farm! These items are purely cosmetic but add charm. "
            "Press R to rotate during placement."
        )
        instructions.setStyleSheet("color: #aaa; font-size: 12px; padding: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        
        # Group decorations by category
        categories = {
            "🌿 Nature & Plants": [
                DecorationType.HAY_BALE,
                DecorationType.FLOWER_BED,
                DecorationType.TREE,
                DecorationType.SCARECROW,
                DecorationType.PUMPKIN_PATCH,
            ],
            "🏚️ Farm Structures": [
                DecorationType.WINDMILL,
                DecorationType.WATER_WELL,
                DecorationType.DECORATIVE_SILO,
                DecorationType.WOODEN_CART,
            ],
            "💧 Water Features": [
                DecorationType.POND,
                DecorationType.FOUNTAIN,
                DecorationType.WATER_TROUGH,
            ],
            "🪑 Outdoor Living": [
                DecorationType.BENCH,
                DecorationType.PICNIC_TABLE,
                DecorationType.LAMP_POST,
            ],
            "🎪 Fun Extras": [
                DecorationType.GARDEN_GNOME,
                DecorationType.MAILBOX,
                DecorationType.SIGNPOST,
            ],
        }
        
        for category_name, decoration_types in categories.items():
            # Category header
            category_label = QLabel(category_name)
            category_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #aaa; "
                "margin-top: 10px; margin-bottom: 5px;"
            )
            scroll_layout.addWidget(category_label)
            
            # Grid for this category
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(8)
            
            for i, deco_type in enumerate(decoration_types):
                deco_widget = self._create_decoration_item(deco_type)
                row, col = divmod(i, 2)  # 2 columns
                grid.addWidget(deco_widget, row, col)
            
            scroll_layout.addWidget(grid_widget)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_decoration_item(self, decoration_type: DecorationType) -> QFrame:
        """Create a widget for purchasing a specific decoration."""
        info = DECORATION_INFO.get(decoration_type, {})
        cost = DECORATION_COSTS.get(decoration_type, 100)
        footprint = DECORATION_FOOTPRINTS.get(decoration_type, (1, 1))
        can_rotate = info.get("can_rotate", False)
        
        can_afford = self.farm.money >= cost
        
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #3a4a3a;
                border: 2px solid {"#5a8f4a" if can_afford else "#444"};
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Header: emoji + name
        header_layout = QHBoxLayout()
        
        emoji_label = QLabel(info.get("emoji", "🏠"))
        emoji_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(emoji_label)
        
        name_label = QLabel(info.get("name", decoration_type.value))
        name_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #fff;")
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Details row
        details_text = f"${cost:,} • {footprint[0]}x{footprint[1]}"
        if can_rotate:
            details_text += " • 🔄"
        
        details_label = QLabel(details_text)
        details_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(details_label)
        
        # Buy button
        buy_btn = QPushButton("Buy")
        buy_btn.setEnabled(can_afford)
        buy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#5a8f4a" if can_afford else "#444"};
                color: {"white" if can_afford else "#666"};
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {"#6ba85a" if can_afford else "#444"};
            }}
        """)
        buy_btn.clicked.connect(
            lambda checked, dt=decoration_type: self._on_decoration_clicked(dt)
        )
        layout.addWidget(buy_btn)
        
        return frame
    
    def _on_decoration_clicked(self, decoration_type: DecorationType) -> None:
        """Handle decoration purchase click."""
        cost = DECORATION_COSTS.get(decoration_type, 100)
        
        if self.farm.money < cost:
            logger.warning(f"Cannot afford {decoration_type.value}")
            return
        
        logger.info(f"Decoration purchased: {decoration_type.value}")
        self.decoration_purchased.emit(decoration_type)
        self.close()
