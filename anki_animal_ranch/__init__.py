"""
Anki Animal Ranch - A farm simulation game addon for Anki.

This addon gamifies studying by letting users run a virtual farm
where time progresses based on cards answered.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Set up logging (console only at import time, file logging when game opens)
from .utils.logger import setup_logging, setup_file_logging, get_logger, get_log_file_path

setup_logging()
logger = get_logger(__name__)

# Version
__version__ = "0.2.4"

# Global reference to the main window
_main_window = None


def show_game_window() -> None:
    """
    Show the main game window.
    
    Creates a new window if one doesn't exist, otherwise shows
    the existing window.
    """
    global _main_window
    
    # Set up file logging now that Anki is ready
    setup_file_logging()
    
    try:
        from aqt import mw  # type: ignore
        from .ui.main_window import MainWindow
        
        if _main_window is None:
            _main_window = MainWindow(mw=mw)
        
        _main_window.show()
        _main_window.raise_()
        _main_window.activateWindow()
        
        logger.info("Game window shown")
    except ImportError:
        # Running outside of Anki - show standalone
        _show_standalone()
    except Exception as e:
        logger.error(f"Failed to show game window: {e}", exc_info=True)


def _show_standalone() -> None:
    """Show the game window in standalone mode (outside Anki)."""
    global _main_window
    
    # Set up file logging for standalone mode
    setup_file_logging()
    
    import sys
    from PyQt6.QtWidgets import QApplication
    from .ui.main_window import MainWindow
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    if _main_window is None:
        _main_window = MainWindow(mw=None)
    
    _main_window.show()
    _main_window.raise_()
    
    # Only run event loop if we created the app
    if not hasattr(app, '_anki_animal_ranch_running'):
        app._anki_animal_ranch_running = True
        sys.exit(app.exec())


def on_card_answered(reviewer, card, ease) -> None:
    """
    Hook called when the user answers a card.
    
    Forwards the event to the game if the window is open.
    """
    if _main_window is not None and _main_window.isVisible():
        _main_window.on_card_answered(ease)


def setup_hooks() -> None:
    """Set up Anki hooks for the addon."""
    try:
        from aqt import gui_hooks  # type: ignore
        
        # Hook into card review
        gui_hooks.reviewer_did_answer_card.append(on_card_answered)
        
        logger.info("Anki hooks registered")
    except ImportError:
        logger.warning("Running outside Anki - hooks not registered")


def add_menu_item() -> None:
    """Add menu item to Anki's Tools menu."""
    try:
        from aqt import mw  # type: ignore
        from aqt.qt import QAction
        
        action = QAction("🐄 Animal Ranch", mw)
        action.triggered.connect(show_game_window)
        mw.form.menuTools.addAction(action)
        
        logger.info("Menu item added")
    except ImportError:
        logger.warning("Running outside Anki - menu not added")
    except Exception as e:
        logger.error(f"Failed to add menu item: {e}", exc_info=True)


# =============================================================================
# Anki Addon Entry Point
# =============================================================================

def init_addon() -> None:
    """Initialize the addon when Anki loads it."""
    setup_hooks()
    add_menu_item()
    logger.info("Anki Animal Ranch addon initialized")


# Run initialization if loaded by Anki
try:
    from aqt import mw  # type: ignore
    if mw is not None:
        init_addon()
except ImportError:
    # Not running in Anki
    pass


# =============================================================================
# Standalone Entry Point
# =============================================================================

def main() -> None:
    """Main entry point for running standalone."""
    log_path = get_log_file_path()
    logger.info("Starting Anki Animal Ranch in standalone mode")
    if log_path:
        logger.info(f"Log file: {log_path}")
    _show_standalone()


if __name__ == "__main__":
    main()
