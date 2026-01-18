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
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2c2c2c;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        frame = QFrame()
        frame.setObjectName("headerFrame")
        frame.setStyleSheet("""
            #headerFrame {
                background-color: #4a3a3a;
                border: 2px solid #8f5a5a;
                border-radius: 8px;
            }
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
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        header_layout.addWidget(title)
        
        layout.addWidget(frame)
        
        # Info
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_frame.setStyleSheet("""
            #infoFrame {
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 6px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 12, 15, 12)
        info_layout.setSpacing(8)
        
        next_label = QLabel(f"➡️ Next plot to unlock: Plot {self.next_zone + 1}")
        next_label.setStyleSheet("font-size: 14px; color: #8f8; background: transparent; border: none;")
        info_layout.addWidget(next_label)
        
        this_label = QLabel(f"📍 You clicked: Plot {self.clicked_zone + 1}")
        this_label.setStyleSheet("font-size: 14px; color: #aaa; background: transparent; border: none;")
        info_layout.addWidget(this_label)
        
        layout.addWidget(info_frame)
        
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #5a5a8f;
                color: white;
                border: none;
                padding: 12px 40px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #6a6a9f;
            }
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
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2c2c2c;
            }
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
        frame.setStyleSheet("""
            #headerFrame {
                background-color: #3a4a5a;
                border: 2px solid #5a8faf;
                border-radius: 8px;
            }
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
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        return frame
    
    def _create_info_section(self) -> QFrame:
        """Create the info section."""
        frame = QFrame()
        frame.setObjectName("infoFrame")
        frame.setStyleSheet("""
            #infoFrame {
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Cost
        cost_color = "#f0c040" if self.can_afford else "#f66"
        cost_label = QLabel(f"💰 Cost: ${self.cost:,}")
        cost_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {cost_color}; background: transparent; border: none;")
        layout.addWidget(cost_label)
        
        # Your money
        money_label = QLabel(f"💵 Your money: ${self.farm.money:,}")
        money_label.setStyleSheet("font-size: 14px; color: #aaa; background: transparent; border: none;")
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
        progress.setStyleSheet("font-size: 12px; color: #888; background: transparent; border: none; margin-top: 5px;")
        layout.addWidget(progress)
        
        return frame
    
    def _create_buttons(self) -> QHBoxLayout:
        """Create the button row."""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Unlock button
        unlock_btn = QPushButton(f"🔓 Unlock Plot")
        unlock_btn.setEnabled(self.can_afford)
        unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#5a8f4a" if self.can_afford else "#444"};
                color: {"white" if self.can_afford else "#888"};
                border: none;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {"#6ba85a" if self.can_afford else "#444"};
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
