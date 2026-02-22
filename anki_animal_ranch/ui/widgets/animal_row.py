"""
AnimalRow widget — a single row in the market animals tab.

Extracted from market_dialog.py so it can be imported independently
and reused without pulling in the entire dialog.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from ...core.constants import AnimalType
from ..theme import (
    COLOR_BG_PANEL,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_MUTED,
    danger_button_style,
)

if TYPE_CHECKING:
    from ...models.animal import Animal


class AnimalRow(QFrame):
    """A row displaying an animal with sell controls."""

    sell_clicked = pyqtSignal(str)  # animal_id

    def __init__(
        self,
        animal: Animal,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.animal = animal

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the row UI."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_PANEL};
                border-radius: 8px;
                padding: 5px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Animal icon and name
        emoji = self._get_emoji()
        name = self.animal.display_name
        name_label = QLabel(f"{emoji} {name}")
        name_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        name_label.setFixedWidth(130)
        layout.addWidget(name_label)

        # Stage/maturity info
        stage = self.animal.growth_stage.value.capitalize()
        maturity = f"{self.animal.maturity:.0%}"
        info_label = QLabel(f"{stage} ({maturity})")
        info_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        info_label.setFixedWidth(100)
        layout.addWidget(info_label)

        # Health (affects sale value)
        health_pct = int(self.animal.health * 100)
        health_label = QLabel(f"❤️ {health_pct}%")
        health_label.setStyleSheet("color: #a77; font-size: 12px;")
        health_label.setFixedWidth(70)
        layout.addWidget(health_label)

        # Spacer
        layout.addStretch()

        # Sale value
        value = self.animal.sale_value
        value_label = QLabel(f"${value:,}")
        value_label.setStyleSheet(
            f"color: {COLOR_TEXT_ACCENT}; font-size: 15px; font-weight: bold;"
        )
        value_label.setFixedWidth(80)
        layout.addWidget(value_label)

        # Sell button
        sell_btn = QPushButton("Sell")
        sell_btn.setStyleSheet(danger_button_style(13))
        sell_btn.clicked.connect(self._on_sell)
        layout.addWidget(sell_btn)

    def _get_emoji(self) -> str:
        """Get emoji for animal type."""
        emojis = {
            AnimalType.CHICKEN: "🐔",
            AnimalType.PIG: "🐷",
            AnimalType.COW: "🐄",
        }
        return emojis.get(self.animal.type, "🐾")

    def _on_sell(self) -> None:
        """Handle sell button click."""
        self.sell_clicked.emit(self.animal.id)
