"""
SidePanel — the HUD panel shown to the right of the farm view.

Contains all status labels (money, time, animals, zones, inventory, feed)
and action buttons (Shop, Market, Visit Friend, Return Home, etc.).

Exposes pyqtSignals for button clicks so MainWindow can stay decoupled,
and a refresh() method that takes the current Farm + TimeSystem to update
all displayed values in one call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from ...core.constants import (
    MAX_FARM_ZONES,
    FeedType,
    ProductType,
)
from ...models.player import parse_inventory
from ...services.pricing import product_unit_price
from ..theme import (
    COLOR_BG_BORDER,
    COLOR_BG_DARK,
    COLOR_PLACEMENT_BG,
    COLOR_PLACEMENT_BORDER,
    COLOR_TEXT_ACCENT,
    COLOR_WARNING,
    COLOR_WARNING_BG,
    COLOR_WARNING_BORDER,
    danger_button_style,
    inventory_label_style,
    money_label_style,
    neutral_button_style,
    primary_button_style,
    return_button_style,
    section_title_style,
    social_button_style,
    stat_label_style,
)

if TYPE_CHECKING:
    from ...models.farm import Farm
    from ...core.time_system import TimeSystem


class SidePanel(QFrame):
    """
    HUD panel displayed to the right of the isometric view.

    Signals:
        shop_clicked: User clicked the Shop button.
        market_clicked: User clicked the Market button.
        visit_friend_clicked: User clicked Visit Friend.
        return_home_clicked: User clicked Return Home.
        cancel_placement_clicked: User clicked Cancel Placement.
        settings_clicked: User clicked Settings.
    """

    shop_clicked = pyqtSignal()
    market_clicked = pyqtSignal()
    visit_friend_clicked = pyqtSignal()
    return_home_clicked = pyqtSignal()
    cancel_placement_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent: QFrame | None = None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_DARK};
                border-left: 2px solid {COLOR_BG_BORDER};
            }}
        """)

        self._in_placement_mode = False
        self._in_visit_mode = False

        self._setup_ui()

    # =========================================================================
    # Setup
    # =========================================================================

    def _setup_ui(self) -> None:
        """Create all child widgets and layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("🐄 Farm Status")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_ACCENT};
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }}
        """)
        layout.addWidget(title_label)

        # Stats labels
        self._money_label = QLabel("💰 Money: $1,500")
        self._time_label = QLabel("🕐 Spring Day 1, 06:00")
        self._animals_label = QLabel("🐔 Animals: 0")
        self._zones_label = QLabel("🌾 Plots: 1/12")

        for label in [self._money_label, self._time_label, self._animals_label, self._zones_label]:
            label.setStyleSheet(stat_label_style())
            layout.addWidget(label)

        # Inventory section
        inv_title = QLabel("📦 Inventory")
        inv_title.setStyleSheet(section_title_style())
        layout.addWidget(inv_title)

        self._inventory_label = QLabel("🥚 Eggs: 0\n🥛 Milk: 0\n🍄 Truffles: 0")
        self._inventory_label.setStyleSheet(inventory_label_style())
        self._inventory_label.setWordWrap(True)
        self._inventory_label.setMinimumWidth(180)
        layout.addWidget(self._inventory_label)

        # Feed section
        feed_title = QLabel("🌾 Feed Supply")
        feed_title.setStyleSheet(section_title_style())
        layout.addWidget(feed_title)

        self._feed_label = QLabel("No animals yet")
        self._feed_label.setStyleSheet(inventory_label_style())
        self._feed_label.setWordWrap(True)
        self._feed_label.setMinimumWidth(180)
        layout.addWidget(self._feed_label)

        layout.addSpacing(10)

        # Placement mode indicator (hidden by default)
        self._placement_label = QLabel("")
        self._placement_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_ACCENT};
                font-size: 13px;
                padding: 8px;
                background-color: {COLOR_PLACEMENT_BG};
                border-radius: 4px;
                border: 1px solid {COLOR_PLACEMENT_BORDER};
            }}
        """)
        self._placement_label.setWordWrap(True)
        self._placement_label.hide()
        layout.addWidget(self._placement_label)

        # Action buttons
        self._shop_btn = QPushButton("🏪 Shop")
        self._shop_btn.setStyleSheet(primary_button_style())
        self._shop_btn.clicked.connect(self.shop_clicked)
        layout.addWidget(self._shop_btn)

        self._cancel_btn = QPushButton("❌ Cancel Placement")
        self._cancel_btn.setStyleSheet(danger_button_style())
        self._cancel_btn.clicked.connect(self.cancel_placement_clicked)
        self._cancel_btn.hide()
        layout.addWidget(self._cancel_btn)

        self._market_btn = QPushButton("📦 Market")
        self._market_btn.setStyleSheet(primary_button_style())
        self._market_btn.clicked.connect(self.market_clicked)
        layout.addWidget(self._market_btn)

        self._visit_btn = QPushButton("👥 Visit Friend")
        self._visit_btn.setStyleSheet(social_button_style())
        self._visit_btn.clicked.connect(self.visit_friend_clicked)
        layout.addWidget(self._visit_btn)

        self._return_home_btn = QPushButton("🏠 Return Home")
        self._return_home_btn.setStyleSheet(return_button_style())
        self._return_home_btn.clicked.connect(self.return_home_clicked)
        self._return_home_btn.hide()
        layout.addWidget(self._return_home_btn)

        layout.addStretch()

        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setStyleSheet(neutral_button_style())
        settings_btn.clicked.connect(self.settings_clicked)
        layout.addWidget(settings_btn)

    # =========================================================================
    # Data Refresh
    # =========================================================================

    def refresh(self, farm: Farm, time_system: TimeSystem) -> None:
        """
        Update all HUD labels from current farm and time state.

        Call this whenever the farm state changes (card answered, purchase, etc.).
        """
        # Stats row
        self._money_label.setText(f"💰 Money: ${farm.money:,}")
        self._time_label.setText(f"🕐 {time_system.current_time.format_full()}")
        self._animals_label.setText(f"🐔 Animals: {len(farm.animals)}")

        zones_text = f"🌾 Plots: {farm.unlocked_zones}/{MAX_FARM_ZONES}"
        if farm.unlocked_zones < MAX_FARM_ZONES:
            zones_text += f" (next: ${farm.next_zone_cost:,})"
        self._zones_label.setText(zones_text)

        # Inventory
        product_totals: dict[ProductType, int] = {pt: 0 for pt in ProductType}
        total_value = 0
        for product_type, quality, count in parse_inventory(farm.player.inventory):
            product_totals[product_type] += count
            total_value += count * product_unit_price(product_type, quality)

        eggs = product_totals.get(ProductType.EGG, 0)
        milk = product_totals.get(ProductType.MILK, 0)
        truffles = product_totals.get(ProductType.TRUFFLE, 0)
        inv_text = f"🥚 Eggs: {eggs}\n🥛 Milk: {milk}\n🍄 Truffles: {truffles}"
        if total_value > 0:
            inv_text += f"\n\n💵 Value: ${total_value:,}"
        self._inventory_label.setText(inv_text)

        # Feed
        self._refresh_feed(farm)

    def _refresh_feed(self, farm: Farm) -> None:
        """Update the feed status label."""
        total_animals = len(farm.animals)
        if total_animals == 0:
            self._feed_label.setText("No animals yet")
            self._feed_label.setStyleSheet(inventory_label_style())
            return

        feed_status = farm.get_feed_status()
        feed_emojis = {
            FeedType.CHICKEN_FEED: "🐔",
            FeedType.PIG_FEED: "🐷",
            FeedType.COW_FEED: "🐄",
        }

        feed_lines = []
        has_warning = False

        for feed_type, status in feed_status.items():
            animal_count = status.get("animal_count", 0)
            if animal_count == 0:
                continue

            amount = status.get("amount", 0)
            days = status.get("days_remaining", float("inf"))
            emoji = feed_emojis.get(feed_type, "🌾")

            if days == float("inf") or days > 30:
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

        feed_text = "\n".join(feed_lines) if feed_lines else "No feed needed"

        if has_warning:
            self._feed_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLOR_WARNING};
                    font-size: 12px;
                    padding: 8px;
                    background-color: {COLOR_WARNING_BG};
                    border-radius: 4px;
                    border: 1px solid {COLOR_WARNING_BORDER};
                }}
            """)
        else:
            self._feed_label.setStyleSheet(inventory_label_style())

        self._feed_label.setText(feed_text)

    # =========================================================================
    # Mode control
    # =========================================================================

    def set_placement_mode(self, active: bool, label_text: str = "") -> None:
        """
        Switch placement mode UI on or off.

        When active, shows the placement instruction label and Cancel button,
        and hides Shop/Market buttons. When inactive, restores normal button layout
        (respecting visit mode state).
        """
        self._in_placement_mode = active

        if active:
            self._placement_label.setText(label_text)
            self._placement_label.show()
            self._cancel_btn.show()
            self._shop_btn.hide()
            self._market_btn.hide()
            self._visit_btn.hide()
        else:
            self._placement_label.hide()
            self._cancel_btn.hide()
            if not self._in_visit_mode:
                self._shop_btn.show()
                self._market_btn.show()
                self._visit_btn.show()

    def set_visit_mode(self, active: bool) -> None:
        """
        Switch visit-friend mode UI on or off.

        When active, shows Return Home and hides Shop/Market/Visit buttons.
        When inactive, restores normal button layout (unless placement mode is on).
        """
        self._in_visit_mode = active

        if active:
            self._return_home_btn.show()
            self._shop_btn.hide()
            self._market_btn.hide()
            self._visit_btn.hide()
        else:
            self._return_home_btn.hide()
            if not self._in_placement_mode:
                self._shop_btn.show()
                self._market_btn.show()
                self._visit_btn.show()
