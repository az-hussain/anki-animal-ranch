"""
Changelog Dialog - Shows what's new after updates.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
)

from ..theme import (
    COLOR_BG_BORDER,
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_PRESSED,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
    primary_button_style,
)


class ChangelogDialog(QDialog):
    """Dialog showing changelog entries for recent updates."""
    
    def __init__(self, changelog: dict[str, list[str]], parent=None):
        """
        Initialize the changelog dialog.
        
        Args:
            changelog: Dict of version -> list of changes
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("What's New")
        self.setMinimumSize(500, 400)
        self.resize(550, 450)
        
        self._setup_ui(changelog)
    
    def _setup_ui(self, changelog: dict[str, list[str]]) -> None:
        """Set up the dialog UI."""
        # Dark theme matching other game dialogs
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
            }}
            QScrollArea {{
                background-color: {COLOR_BG_DARK};
                border: none;
            }}
            QWidget {{
                background-color: {COLOR_BG_DARK};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🎉 Anki Animal Ranch Updated!")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: bold;
                color: {COLOR_PRIMARY};
                background-color: transparent;
            }}
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Here's what's new:")
        subtitle.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLOR_TEXT_MUTED};
                background-color: transparent;
            }}
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Scroll area for changelog content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(5, 10, 5, 10)
        
        # Add changelog entries (sorted by version, newest first)
        sorted_versions = sorted(changelog.keys(), key=self._parse_version, reverse=True)
        
        for version in sorted_versions:
            changes = changelog[version]
            
            # Version section container
            version_frame = QFrame()
            version_frame.setObjectName("versionFrame")
            version_frame.setStyleSheet(f"""
                QFrame#versionFrame {{
                    background-color: {COLOR_BG_PANEL};
                    border-radius: 8px;
                    border: 1px solid {COLOR_BG_BORDER};
                }}
                QFrame#versionFrame QLabel {{
                    background: none;
                    border: none;
                }}
            """)
            version_layout = QVBoxLayout(version_frame)
            version_layout.setSpacing(8)
            version_layout.setContentsMargins(15, 12, 15, 12)
            
            version_label = QLabel(f"✨ Version {version}")
            version_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLOR_PRIMARY};")
            version_layout.addWidget(version_label)
            
            # Changes list
            for change in changes:
                change_label = QLabel(f"  • {change}")
                change_label.setWordWrap(True)
                change_label.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_LIGHT}; padding-left: 10px;")
                version_layout.addWidget(change_label)
            
            content_layout.addWidget(version_frame)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, 1)
        
        # OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("Got it!")
        ok_btn.setMinimumWidth(140)
        ok_btn.setStyleSheet(primary_button_style())
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    @staticmethod
    def _parse_version(version_str: str) -> tuple[int, int, int]:
        """Parse version string for sorting."""
        try:
            parts = version_str.split(".")
            return (
                int(parts[0]) if len(parts) > 0 else 0,
                int(parts[1]) if len(parts) > 1 else 0,
                int(parts[2]) if len(parts) > 2 else 0,
            )
        except (ValueError, IndexError):
            return (0, 0, 0)
