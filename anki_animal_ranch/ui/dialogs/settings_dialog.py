"""
Settings dialog for Anki Animal Ranch.

Provides game settings, currently including the Reset Farm action.
"""

from __future__ import annotations

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

from ..theme import (
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BG_BORDER,
    COLOR_DANGER_FRAME_BG,
    COLOR_TEXT_WHITE,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
    danger_button_style,
    neutral_button_style,
)


class SettingsDialog(QDialog):
    """
    Settings dialog with a Reset Farm option.

    Signals:
        farm_reset: Emitted when the user confirms the farm reset.
    """

    farm_reset = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
                color: {COLOR_TEXT_WHITE};
            }}
            QLabel {{
                color: {COLOR_TEXT_WHITE};
            }}
        """)

        self._confirmed = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_WHITE};")
        layout.addWidget(title)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {COLOR_BG_BORDER};")
        layout.addWidget(divider)

        # Reset Farm section
        reset_frame = QFrame()
        reset_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_DANGER_FRAME_BG};
                border: 1px solid #6a3a3a;
                border-radius: 6px;
            }}
        """)
        reset_layout = QVBoxLayout(reset_frame)
        reset_layout.setContentsMargins(16, 16, 16, 16)
        reset_layout.setSpacing(8)

        reset_title = QLabel("Reset Farm")
        reset_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_WHITE}; border: none;")
        reset_layout.addWidget(reset_title)

        reset_desc = QLabel("Permanently delete your farm and start fresh with $1,500.")
        reset_desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED}; border: none;")
        reset_desc.setWordWrap(True)
        reset_layout.addWidget(reset_desc)

        # Confirmation area (hidden initially)
        self._confirm_widget = QWidget()
        self._confirm_widget.setStyleSheet("border: none;")
        confirm_layout = QVBoxLayout(self._confirm_widget)
        confirm_layout.setContentsMargins(0, 8, 0, 0)
        confirm_layout.setSpacing(8)

        confirm_label = QLabel("This will permanently delete your farm. This cannot be undone.")
        confirm_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: #e06060; border: none;")
        confirm_label.setWordWrap(True)
        confirm_layout.addWidget(confirm_label)

        confirm_buttons = QHBoxLayout()
        confirm_buttons.setSpacing(8)

        self._confirm_yes_btn = QPushButton("Yes, Reset Farm")
        self._confirm_yes_btn.setStyleSheet(danger_button_style(12))
        self._confirm_yes_btn.clicked.connect(self._do_reset)

        self._confirm_no_btn = QPushButton("Cancel")
        self._confirm_no_btn.setStyleSheet(neutral_button_style(12))
        self._confirm_no_btn.clicked.connect(self._cancel_confirm)

        confirm_buttons.addWidget(self._confirm_yes_btn)
        confirm_buttons.addWidget(self._confirm_no_btn)
        confirm_layout.addLayout(confirm_buttons)

        self._confirm_widget.setVisible(False)
        reset_layout.addWidget(self._confirm_widget)

        # Reset button
        self._reset_btn = QPushButton("Reset Farm")
        self._reset_btn.setStyleSheet(danger_button_style(12))
        self._reset_btn.clicked.connect(self._show_confirm)
        reset_layout.addWidget(self._reset_btn)

        layout.addWidget(reset_frame)
        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(neutral_button_style())
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def _show_confirm(self) -> None:
        """Show the inline confirmation."""
        self._reset_btn.setVisible(False)
        self._confirm_widget.setVisible(True)
        self.adjustSize()

    def _cancel_confirm(self) -> None:
        """Hide the confirmation and restore the reset button."""
        self._confirm_widget.setVisible(False)
        self._reset_btn.setVisible(True)
        self.adjustSize()

    def _do_reset(self) -> None:
        """Emit farm_reset and close the dialog."""
        self.farm_reset.emit()
        self.accept()
