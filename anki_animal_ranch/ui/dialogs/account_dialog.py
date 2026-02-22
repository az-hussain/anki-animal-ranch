"""
Account creation dialog for Anki Animal Ranch.

First-time setup dialog for creating an online account.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...data.account_manager import AccountManager, get_account_manager
from ...network import check_username_available, create_account, is_online_available
from ...utils.logger import get_logger
from ..theme import (
    COLOR_BG_BORDER,
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BG_SELECTED,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_TEXT_DIMMED,
    COLOR_TEXT_MUTED,
)

if TYPE_CHECKING:
    from ...models.farm import Farm

logger = get_logger(__name__)


class AccountCreationDialog(QDialog):
    """
    Dialog for creating a new online account.
    
    Shows on first "Visit Friend" click if no account exists.
    
    Signals:
        account_created: Emitted when account is successfully created
    """
    
    account_created = pyqtSignal(str)  # username
    
    def __init__(
        self,
        farm: Farm,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.farm = farm
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("🌐 Create Online Account")
        self.setMinimumSize(450, 300)
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
                font-size: 16px;
            }}
            QLineEdit:focus {{
                border-color: {COLOR_PRIMARY};
            }}
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: white;
                border: none;
                padding: 12px 25px;
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
            QPushButton#cancelBtn {{
                background-color: {COLOR_BG_SELECTED};
            }}
            QPushButton#cancelBtn:hover {{
                background-color: #5a5a5a;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Create Your Online Account")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_PRIMARY};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Info text
        info = QLabel(
            "Choose a username to enable online features like visiting friends' farms.\n\n"
            "⚠️ Your username cannot be changed after creation!"
        )
        info.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_MUTED};")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        layout.addSpacing(10)
        
        # Username input
        username_label = QLabel("Username:")
        username_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username (3-20 chars, lowercase)")
        self.username_input.setMaxLength(20)
        self.username_input.textChanged.connect(self._on_username_changed)
        layout.addWidget(self.username_input)
        
        # Validation hint
        self.hint_label = QLabel("Lowercase letters, numbers, and underscores only")
        self.hint_label.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_DIMMED};")
        layout.addWidget(self.hint_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create Account")
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self._on_create_clicked)
        btn_layout.addWidget(self.create_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_username_changed(self, text: str) -> None:
        """Handle username input change."""
        # Normalize to lowercase
        normalized = text.lower()
        if text != normalized:
            self.username_input.setText(normalized)
            return
        
        # Validate
        account_manager = get_account_manager()
        valid, error = account_manager.validate_username(text)
        
        if not text:
            self.hint_label.setText("Lowercase letters, numbers, and underscores only")
            self.hint_label.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_DIMMED};")
            self.create_btn.setEnabled(False)
        elif valid:
            self.hint_label.setText("✓ Username looks good!")
            self.hint_label.setStyleSheet(f"font-size: 11px; color: {COLOR_PRIMARY};")
            self.create_btn.setEnabled(True)
        else:
            self.hint_label.setText(f"✗ {error}")
            self.hint_label.setStyleSheet("font-size: 11px; color: #c44;")
            self.create_btn.setEnabled(False)
    
    def _on_create_clicked(self) -> None:
        """Handle create button click."""
        username = self.username_input.text().strip().lower()
        
        if not username:
            return
        
        # Disable UI while processing
        self.create_btn.setEnabled(False)
        self.create_btn.setText("Checking...")
        
        # Check if online features available
        if not is_online_available():
            QMessageBox.warning(
                self,
                "Offline",
                "Online features are not available.\n\n"
                "Please check your internet connection and try again."
            )
            self.create_btn.setEnabled(True)
            self.create_btn.setText("Create Account")
            return
        
        # Check username availability
        result = check_username_available(username)
        
        if not result.success:
            QMessageBox.warning(
                self,
                "Username Taken",
                f"The username '{username}' is already taken.\n\n"
                "Please choose a different username."
            )
            self.create_btn.setEnabled(True)
            self.create_btn.setText("Create Account")
            return
        
        # Create local account
        account_manager = get_account_manager()
        success, error, pkey = account_manager.create_account(username)
        
        if not success:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create account: {error}"
            )
            self.create_btn.setEnabled(True)
            self.create_btn.setText("Create Account")
            return
        
        # Register with Supabase
        farm_data = self.farm.to_dict()
        result = create_account(username, pkey, farm_data)
        
        if not result.success:
            # Rollback local account? For now just warn
            QMessageBox.warning(
                self,
                "Partial Success",
                f"Account created locally but failed to sync:\n{result.error}\n\n"
                "Your farm will sync on next save."
            )
        else:
            QMessageBox.information(
                self,
                "Success!",
                f"Account '{username}' created successfully!\n\n"
                "You can now visit friends' farms and they can visit yours."
            )
        
        self.account_created.emit(username)
        self.accept()
