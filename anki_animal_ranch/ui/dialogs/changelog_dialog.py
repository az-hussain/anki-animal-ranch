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
        self.setStyleSheet("""
            QDialog {
                background-color: #2c2c2c;
            }
            QScrollArea {
                background-color: #2c2c2c;
                border: none;
            }
            QWidget {
                background-color: #2c2c2c;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🎉 Anki Animal Ranch Updated!")
        header.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #4CAF50;
                background-color: transparent;
            }
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Here's what's new:")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #aaa;
                background-color: transparent;
            }
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
            version_frame.setStyleSheet("""
                QFrame#versionFrame {
                    background-color: #3a3a3a;
                    border-radius: 8px;
                    border: 1px solid #444;
                }
                QFrame#versionFrame QLabel {
                    background: none;
                    border: none;
                }
            """)
            version_layout = QVBoxLayout(version_frame)
            version_layout.setSpacing(8)
            version_layout.setContentsMargins(15, 12, 15, 12)
            
            version_label = QLabel(f"✨ Version {version}")
            version_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #4CAF50;")
            version_layout.addWidget(version_label)
            
            # Changes list
            for change in changes:
                change_label = QLabel(f"  • {change}")
                change_label.setWordWrap(True)
                change_label.setStyleSheet("font-size: 13px; color: #ccc; padding-left: 10px;")
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
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
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
