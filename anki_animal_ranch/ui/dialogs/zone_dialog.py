"""
Zone Unlock Dialog - Purchase new farm zones.

Styled to match the app's other dialogs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.constants import MAX_FARM_ZONES, ZONE_UNLOCK_COSTS
from ...utils.logger import get_logger
from ..theme import (
    COLOR_BG_BORDER,
    COLOR_BG_DARK,
    COLOR_BG_ITEM,
    COLOR_DANGER,
    COLOR_DANGER_FRAME_BG,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SOCIAL,
    COLOR_SOCIAL_FRAME_BG,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_DIMMED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
    COLOR_UPGRADE,
    COLOR_UPGRADE_HOVER,
    neutral_button_style,
)

if TYPE_CHECKING:
    from ...models.farm import Farm

logger = get_logger(__name__)


class ZoneLockedDialog(QDialog):
    """
    Dialog shown when clicking a plot that can't be unlocked yet.
    """
    
    def __init__(
        self,
        clicked_zone: int,
        next_zone: int,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.clicked_zone = clicked_zone
        self.next_zone = next_zone
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("🔒 Plot Locked")
        self.setMinimumSize(400, 300)
        self.resize(400, 300)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        frame = QFrame()
        frame.setObjectName("headerFrame")
        frame.setStyleSheet(f"""
            #headerFrame {{
                background-color: {COLOR_DANGER_FRAME_BG};
                border: 2px solid {COLOR_DANGER};
                border-radius: 8px;
            }}
        """)
        
        header_layout = QVBoxLayout(frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Lock emoji
        emoji_label = QLabel("🔒")
        emoji_label.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(emoji_label)
        
        # Title
        title = QLabel("Plots Must Be Unlocked In Order")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_TEXT_WHITE}; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        header_layout.addWidget(title)
        
        layout.addWidget(frame)
        
        # Info
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_frame.setStyleSheet(f"""
            #infoFrame {{
                background-color: {COLOR_BG_ITEM};
                border: 1px solid {COLOR_BG_BORDER};
                border-radius: 6px;
            }}
        """)
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 12, 15, 12)
        info_layout.setSpacing(8)
        
        next_label = QLabel(f"➡️ Next plot to unlock: Plot {self.next_zone + 1}")
        next_label.setStyleSheet("font-size: 14px; color: #8f8; background: transparent; border: none;")
        info_layout.addWidget(next_label)
        
        this_label = QLabel(f"📍 You clicked: Plot {self.clicked_zone + 1}")
        this_label.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MUTED}; background: transparent; border: none;")
        info_layout.addWidget(this_label)
        
        layout.addWidget(info_frame)
        
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_UPGRADE};
                color: white;
                border: none;
                padding: 12px 40px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_UPGRADE_HOVER};
            }}
        """)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class ZoneUnlockDialog(QDialog):
    """
    Dialog for unlocking a new farm zone.
    
    Signals:
        zone_unlocked: Emitted when zone is successfully unlocked (zone_index)
    """
    
    zone_unlocked = pyqtSignal(int)
    
    def __init__(
        self,
        zone_index: int,
        farm: Farm,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.zone_index = zone_index
        self.farm = farm
        self.cost = ZONE_UNLOCK_COSTS[zone_index] if zone_index < len(ZONE_UNLOCK_COSTS) else 0
        self.can_afford = farm.money >= self.cost
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle(f"🌾 Unlock Plot {self.zone_index + 1}")
        self.setMinimumSize(420, 380)
        self.resize(420, 400)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Info section
        info_section = self._create_info_section()
        layout.addWidget(info_section)
        
        # Buttons
        buttons = self._create_buttons()
        layout.addLayout(buttons)
    
    def _create_header(self) -> QFrame:
        """Create the header section."""
        frame = QFrame()
        frame.setObjectName("headerFrame")
        frame.setStyleSheet(f"""
            #headerFrame {{
                background-color: {COLOR_SOCIAL_FRAME_BG};
                border: 2px solid {COLOR_SOCIAL};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Emoji
        emoji_label = QLabel("🗺️")
        emoji_label.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(emoji_label)
        
        # Title
        title = QLabel(f"Unlock Plot {self.zone_index + 1}?")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_WHITE}; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        return frame
    
    def _create_info_section(self) -> QFrame:
        """Create the info section."""
        frame = QFrame()
        frame.setObjectName("infoFrame")
        frame.setStyleSheet(f"""
            #infoFrame {{
                background-color: {COLOR_BG_ITEM};
                border: 1px solid {COLOR_BG_BORDER};
                border-radius: 6px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Cost
        cost_color = COLOR_TEXT_ACCENT if self.can_afford else "#f66"
        cost_label = QLabel(f"💰 Cost: ${self.cost:,}")
        cost_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {cost_color}; background: transparent; border: none;")
        layout.addWidget(cost_label)
        
        # Your money
        money_label = QLabel(f"💵 Your money: ${self.farm.money:,}")
        money_label.setStyleSheet(f"font-size: 14px; color: {COLOR_TEXT_MUTED}; background: transparent; border: none;")
        layout.addWidget(money_label)
        
        # After purchase
        if self.can_afford:
            remaining = self.farm.money - self.cost
            after_label = QLabel(f"📊 After purchase: ${remaining:,}")
            after_label.setStyleSheet("font-size: 13px; color: #8a8; background: transparent; border: none;")
            layout.addWidget(after_label)
            
            # Benefit
            benefit = QLabel("✨ This will expand your buildable farm area!")
            benefit.setStyleSheet("font-size: 13px; color: #8af; background: transparent; border: none; margin-top: 5px;")
            benefit.setWordWrap(True)
            layout.addWidget(benefit)
        else:
            # Not enough money
            needed = self.cost - self.farm.money
            needed_label = QLabel(f"⚠️ You need ${needed:,} more")
            needed_label.setStyleSheet("font-size: 13px; color: #f88; background: transparent; border: none;")
            layout.addWidget(needed_label)
        
        # Plot progress
        progress = QLabel(f"🌾 Plot {self.zone_index + 1} of {MAX_FARM_ZONES}")
        progress.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_DIMMED}; background: transparent; border: none; margin-top: 5px;")
        layout.addWidget(progress)
        
        return frame
    
    def _create_buttons(self) -> QHBoxLayout:
        """Create the button row."""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(neutral_button_style())
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Unlock button
        unlock_btn = QPushButton(f"🔓 Unlock Plot")
        unlock_btn.setEnabled(self.can_afford)
        unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY if self.can_afford else COLOR_BG_BORDER};
                color: {"white" if self.can_afford else COLOR_TEXT_DIMMED};
                border: none;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_HOVER if self.can_afford else COLOR_BG_BORDER};
            }}
        """)
        unlock_btn.clicked.connect(self._on_unlock_clicked)
        layout.addWidget(unlock_btn)
        
        return layout
    
    def _on_unlock_clicked(self) -> None:
        """Handle unlock button click."""
        if self.farm.unlock_zone():
            logger.info(f"Unlocked zone {self.zone_index + 1}")
            self.zone_unlocked.emit(self.zone_index)
            self.accept()
        else:
            logger.warning("Failed to unlock zone")
