"""
Visit friend dialog for Anki Animal Ranch.

Allows user to enter a friend's username or select from friends list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...data.account_manager import get_account_manager
from ...network import fetch_farm, is_online_available
from ...utils.logger import get_logger
from ..theme import (
    COLOR_BG_BORDER,
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BG_SELECTED,
    COLOR_NEUTRAL,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_TEXT_DIMMED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
)

logger = get_logger(__name__)


class FriendButton(QFrame):
    """A clickable friend entry."""
    
    clicked = pyqtSignal(str)  # username
    remove_clicked = pyqtSignal(str)  # username
    
    def __init__(self, username: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.username = username
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_PANEL};
                border-radius: 6px;
                padding: 5px;
            }}
            QFrame:hover {{
                background-color: {COLOR_BG_SELECTED};
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(10)
        
        # Friend icon
        icon = QLabel("👤")
        icon.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(icon)
        
        # Username
        name_label = QLabel(self.username)
        name_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background: transparent;")
        layout.addWidget(name_label, stretch=1)
        
        # Remove button (small X)
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXT_DIMMED};
                border: none;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: #c44;
            }}
        """)
        remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.username))
        layout.addWidget(remove_btn)
    
    def mousePressEvent(self, event) -> None:
        """Handle click on the frame."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.username)


class VisitFriendDialog(QDialog):
    """
    Dialog for visiting a friend's farm.
    
    Shows friends list and allows searching by username.
    
    Signals:
        visit_requested: Emitted when user wants to visit a farm (username, farm_data)
    """
    
    visit_requested = pyqtSignal(str, dict)  # username, farm_data
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("👥 Visit Friend's Farm")
        self.setMinimumSize(450, 500)
        self.setModal(True)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
            }}
            QLabel {{
                color: #eee;
            }}
            QLineEdit {{
                background-color: {COLOR_BG_PANEL};
                color: white;
                border: 2px solid {COLOR_BG_BORDER};
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {COLOR_PRIMARY};
            }}
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {COLOR_BG_BORDER};
                color: {COLOR_TEXT_DIMMED};
            }}
            QPushButton#closeBtn {{
                background-color: {COLOR_BG_SELECTED};
            }}
            QPushButton#closeBtn:hover {{
                background-color: #5a5a5a;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Visit a Friend's Farm")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_PRIMARY};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Search section
        search_label = QLabel("Enter username to visit:")
        search_label.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_MUTED};")
        layout.addWidget(search_label)
        
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("friend_username")
        self.username_input.returnPressed.connect(self._on_visit_clicked)
        search_layout.addWidget(self.username_input, stretch=1)
        
        self.visit_btn = QPushButton("Visit")
        self.visit_btn.clicked.connect(self._on_visit_clicked)
        search_layout.addWidget(self.visit_btn)
        
        layout.addLayout(search_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_DIMMED};")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Friends list section
        friends_header = QLabel("📋 Your Friends")
        friends_header.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(friends_header)
        
        # Scrollable friends list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        
        self.friends_container = QWidget()
        self.friends_layout = QVBoxLayout(self.friends_container)
        self.friends_layout.setContentsMargins(0, 0, 0, 0)
        self.friends_layout.setSpacing(8)
        self.friends_layout.addStretch()
        
        scroll.setWidget(self.friends_container)
        layout.addWidget(scroll, stretch=1)
        
        # Populate friends
        self._populate_friends()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
    
    def _populate_friends(self) -> None:
        """Populate the friends list."""
        # Clear existing
        while self.friends_layout.count() > 1:  # Keep the stretch
            item = self.friends_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        account_manager = get_account_manager()
        friends = account_manager.friends
        
        if not friends:
            empty_label = QLabel("No friends yet!\nVisit someone's farm to add them.")
            empty_label.setStyleSheet(f"color: {COLOR_NEUTRAL}; font-size: 13px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.friends_layout.insertWidget(0, empty_label)
        else:
            for username in friends:
                btn = FriendButton(username)
                btn.clicked.connect(self._on_friend_clicked)
                btn.remove_clicked.connect(self._on_remove_friend)
                self.friends_layout.insertWidget(self.friends_layout.count() - 1, btn)
    
    def _on_friend_clicked(self, username: str) -> None:
        """Handle click on a friend."""
        self.username_input.setText(username)
        self._on_visit_clicked()
    
    def _on_remove_friend(self, username: str) -> None:
        """Handle remove friend click."""
        account_manager = get_account_manager()
        account_manager.remove_friend(username)
        self._populate_friends()
    
    def _on_visit_clicked(self) -> None:
        """Handle visit button click."""
        username = self.username_input.text().strip().lower()
        
        if not username:
            self.status_label.setText("Please enter a username")
            self.status_label.setStyleSheet("font-size: 12px; color: #c44;")
            return
        
        # Check if trying to visit self
        account_manager = get_account_manager()
        if account_manager.username and username == account_manager.username:
            self.status_label.setText("That's your own farm!")
            self.status_label.setStyleSheet("font-size: 12px; color: #c44;")
            return
        
        # Check online
        if not is_online_available():
            self.status_label.setText("Offline - cannot visit farms")
            self.status_label.setStyleSheet("font-size: 12px; color: #c44;")
            return
        
        # Disable UI
        self.visit_btn.setEnabled(False)
        self.visit_btn.setText("Loading...")
        self.status_label.setText(f"Fetching {username}'s farm...")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_DIMMED};")
        
        # Fetch farm
        result = fetch_farm(username)
        
        if not result.success:
            self.status_label.setText(f"Error: {result.error}")
            self.status_label.setStyleSheet("font-size: 12px; color: #c44;")
            self.visit_btn.setEnabled(True)
            self.visit_btn.setText("Visit")
            return
        
        # Success! Add to friends list
        account_manager.add_friend(username)
        self._populate_friends()
        
        # Emit visit signal with farm data
        farm_data = result.data.get("farm_json", {})
        self.visit_requested.emit(username, farm_data)
        self.accept()
