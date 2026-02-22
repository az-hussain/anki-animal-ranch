"""
ProductRow widget — a single row in the market products tab.

Extracted from market_dialog.py so it can be imported independently
and reused without pulling in the entire dialog.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from ...core.constants import ProductQuality, ProductType
from ...services.pricing import product_unit_price
from ..theme import (
    COLOR_BG_BORDER,
    COLOR_BG_SELECTED,
    COLOR_NEUTRAL,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_QUALITY_ARTISAN,
    COLOR_QUALITY_BASIC,
    COLOR_QUALITY_BG_ARTISAN,
    COLOR_QUALITY_BG_BASIC,
    COLOR_QUALITY_BG_GOOD,
    COLOR_QUALITY_BG_PREMIUM,
    COLOR_QUALITY_GOOD,
    COLOR_QUALITY_PREMIUM,
    COLOR_RETURN,
    COLOR_RETURN_HOVER,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
)


class ProductRow(QFrame):
    """A row displaying a product with quality tier and sell controls."""

    sell_clicked = pyqtSignal(str, int)  # inventory_key (e.g. "egg_premium"), quantity

    def __init__(
        self,
        product_type: ProductType,
        quality: ProductQuality,
        quantity: int,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.product_type = product_type
        self.quality = quality
        self.quantity = quantity

        self.price = product_unit_price(product_type, quality)

        # Inventory key format: "egg_premium"
        self.inventory_key = f"{product_type.value}_{quality.value}"

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the row UI."""
        # Color based on quality
        quality_colors = {
            ProductQuality.ARTISAN: COLOR_QUALITY_BG_ARTISAN,
            ProductQuality.PREMIUM: COLOR_QUALITY_BG_PREMIUM,
            ProductQuality.GOOD: COLOR_QUALITY_BG_GOOD,
            ProductQuality.BASIC: COLOR_QUALITY_BG_BASIC,
        }
        bg_color = quality_colors.get(self.quality, COLOR_QUALITY_BG_BASIC)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 8px;
                padding: 5px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)

        # Product icon
        emoji = self._get_emoji()
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 20px;")
        emoji_label.setFixedWidth(35)
        layout.addWidget(emoji_label)

        # Product name and quality
        quality_stars = self._get_quality_stars()
        name_label = QLabel(f"{self.product_type.value.capitalize()} {quality_stars}")
        name_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        name_label.setFixedWidth(140)
        layout.addWidget(name_label)

        # Quantity owned
        self.quantity_label = QLabel(f"×{self.quantity}")
        self.quantity_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        self.quantity_label.setFixedWidth(50)
        layout.addWidget(self.quantity_label)

        # Price per unit (with quality bonus shown)
        price_color = self._get_price_color()
        price_label = QLabel(f"${self.price}")
        price_label.setStyleSheet(f"color: {price_color}; font-size: 13px; font-weight: bold;")
        price_label.setFixedWidth(50)
        layout.addWidget(price_label)

        # Spacer
        layout.addStretch()

        # Sell controls (only if we have items)
        if self.quantity > 0:
            # Quantity selector with +/- buttons
            self._sell_qty = 1

            # Minus button
            minus_btn = QPushButton("−")
            minus_btn.setFixedSize(28, 28)
            minus_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_NEUTRAL};
                    color: {COLOR_TEXT_WHITE};
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: #6a6a6a; }}
            """)
            minus_btn.clicked.connect(self._decrement)
            layout.addWidget(minus_btn)

            # Quantity display
            self.qty_display = QLabel("1")
            self.qty_display.setStyleSheet(f"""
                background-color: {COLOR_BG_SELECTED};
                color: {COLOR_TEXT_WHITE};
                border: 1px solid {COLOR_NEUTRAL};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            """)
            self.qty_display.setFixedWidth(40)
            self.qty_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.qty_display)

            # Plus button
            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(28, 28)
            plus_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_NEUTRAL};
                    color: {COLOR_TEXT_WHITE};
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: #6a6a6a; }}
            """)
            plus_btn.clicked.connect(self._increment)
            layout.addWidget(plus_btn)

            # Total value
            self.total_label = QLabel(f"= ${self.price}")
            self.total_label.setStyleSheet(
                f"color: {COLOR_TEXT_ACCENT}; font-size: 13px; font-weight: bold;"
            )
            self.total_label.setFixedWidth(60)
            layout.addWidget(self.total_label)

            # Sell button
            sell_btn = QPushButton("Sell")
            sell_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_PRIMARY};
                    color: {COLOR_TEXT_WHITE};
                    border: none;
                    padding: 6px 15px;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 4px;
                }}
                QPushButton:hover {{ background-color: {COLOR_PRIMARY_HOVER}; }}
            """)
            sell_btn.clicked.connect(self._on_sell)
            layout.addWidget(sell_btn)

            # Sell All button
            sell_all_btn = QPushButton("All")
            sell_all_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_RETURN};
                    color: {COLOR_TEXT_WHITE};
                    border: none;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 4px;
                }}
                QPushButton:hover {{ background-color: {COLOR_RETURN_HOVER}; }}
            """)
            sell_all_btn.clicked.connect(self._on_sell_all)
            layout.addWidget(sell_all_btn)
        else:
            empty_label = QLabel("—")
            empty_label.setStyleSheet(f"color: {COLOR_BG_BORDER}; font-size: 13px;")
            layout.addWidget(empty_label)

    def _get_emoji(self) -> str:
        """Get emoji for product type."""
        emojis = {
            ProductType.EGG: "🥚",
            ProductType.MILK: "🥛",
            ProductType.TRUFFLE: "🍄",
        }
        return emojis.get(self.product_type, "📦")

    def _get_quality_stars(self) -> str:
        """Get star representation of quality."""
        stars = {
            ProductQuality.ARTISAN: "⭐⭐⭐⭐",
            ProductQuality.PREMIUM: "⭐⭐⭐",
            ProductQuality.GOOD: "⭐⭐",
            ProductQuality.BASIC: "⭐",
        }
        return stars.get(self.quality, "⭐")

    def _get_price_color(self) -> str:
        """Get color based on quality tier."""
        colors = {
            ProductQuality.ARTISAN: COLOR_QUALITY_ARTISAN,
            ProductQuality.PREMIUM: COLOR_QUALITY_PREMIUM,
            ProductQuality.GOOD: COLOR_QUALITY_GOOD,
            ProductQuality.BASIC: COLOR_QUALITY_BASIC,
        }
        return colors.get(self.quality, COLOR_QUALITY_BASIC)

    def _increment(self) -> None:
        """Increment sell quantity."""
        if self._sell_qty < self.quantity:
            self._sell_qty += 1
            self._update_display()

    def _decrement(self) -> None:
        """Decrement sell quantity."""
        if self._sell_qty > 1:
            self._sell_qty -= 1
            self._update_display()

    def _update_display(self) -> None:
        """Update quantity display and total."""
        self.qty_display.setText(str(self._sell_qty))
        total = self._sell_qty * self.price
        self.total_label.setText(f"= ${total}")

    def _on_sell(self) -> None:
        """Handle sell button click."""
        self.sell_clicked.emit(self.inventory_key, self._sell_qty)

    def _on_sell_all(self) -> None:
        """Handle sell all button click."""
        self.sell_clicked.emit(self.inventory_key, self.quantity)
