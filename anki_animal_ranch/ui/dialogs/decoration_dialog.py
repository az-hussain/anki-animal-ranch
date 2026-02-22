"""
Decoration Details Dialog - View and manage a decoration.

Shows decoration info and provides move/delete options.
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

from ...core.constants import DECORATION_INFO, DecorationType
from ...utils.logger import get_logger
from ..theme import (
    COLOR_BG_DARK,
    COLOR_PRIMARY,
    COLOR_PRIMARY_FRAME_BG,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
    danger_button_style,
    move_button_style,
    neutral_button_style,
)

if TYPE_CHECKING:
    from ...models.decoration import Decoration
    from ...models.farm import Farm

logger = get_logger(__name__)


class DecorationDetailsDialog(QDialog):
    """
    Dialog showing decoration details with move/delete options.
    
    Signals:
        decoration_move_requested: Emitted when move button is clicked
        decoration_delete_requested: Emitted when delete button is clicked
    """
    
    decoration_move_requested = pyqtSignal(str)  # decoration_id
    decoration_delete_requested = pyqtSignal(str)  # decoration_id
    
    def __init__(
        self,
        decoration: Decoration,
        farm: Farm,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.decoration = decoration
        self.farm = farm
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        info = DECORATION_INFO.get(self.decoration.type, {"name": "Decoration", "emoji": "🏠"})
        
        self.setWindowTitle(f"{info.get('emoji', '🏠')} {info.get('name', 'Decoration')}")
        self.setMinimumSize(380, 200)
        self.resize(420, 220)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Header
        header = self._create_header(info)
        layout.addWidget(header)
        
        # Spacer
        layout.addStretch()
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Move button
        move_btn = QPushButton("📍 Move")
        move_btn.setStyleSheet(move_button_style())
        move_btn.clicked.connect(self._on_move_clicked)
        buttons_layout.addWidget(move_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑️ Remove")
        delete_btn.setStyleSheet(danger_button_style())
        delete_btn.clicked.connect(self._on_delete_clicked)
        buttons_layout.addWidget(delete_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(neutral_button_style())
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_header(self, info: dict) -> QFrame:
        """Create the header section."""
        frame = QFrame()
        frame.setObjectName("headerFrame")
        frame.setStyleSheet(f"""
            #headerFrame {{
                background-color: {COLOR_PRIMARY_FRAME_BG};
                border: 2px solid {COLOR_PRIMARY};
                border-radius: 8px;
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Emoji
        emoji_label = QLabel(info.get("emoji", "🏠"))
        emoji_label.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        emoji_label.setFixedWidth(60)
        layout.addWidget(emoji_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(info.get("name", "Decoration"))
        name_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_WHITE}; background: transparent; border: none;")
        info_layout.addWidget(name_label)
        
        desc_label = QLabel(info.get("description", "A decorative item"))
        desc_label.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED}; background: transparent; border: none;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        return frame
    
    def _on_move_clicked(self) -> None:
        """Handle move button click."""
        logger.info(f"Move requested for decoration {self.decoration.id}")
        self.decoration_move_requested.emit(self.decoration.id)
        self.close()
    
    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        logger.info(f"Delete requested for decoration {self.decoration.id}")
        self.decoration_delete_requested.emit(self.decoration.id)
        self.close()
