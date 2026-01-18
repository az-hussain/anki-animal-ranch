"""
User interface components for Anki Animal Ranch.

This package contains all Qt-dependent UI components:
- Main game window
- HUD overlay
- Panels (stats, inventory, building management)
- Dialogs (shop, market, settings)
- Custom widgets
"""

from .main_window import MainWindow

__all__ = [
    "MainWindow",
]
