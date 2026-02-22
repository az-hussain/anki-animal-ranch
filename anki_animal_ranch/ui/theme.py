"""
UI Theme — single source of truth for all colors and reusable button styles.

Every color constant and style helper lives here. Never hardcode hex values
in dialog or widget files — import from this module instead.
"""

from __future__ import annotations

# =============================================================================
# Colors
# =============================================================================

# Backgrounds
COLOR_BG_DARK = "#2c2c2c"      # Dialog/window background
COLOR_BG_PANEL = "#3a3a3a"     # Panels, list rows
COLOR_BG_ITEM = "#353535"      # Secondary item areas
COLOR_BG_BORDER = "#444"       # Default border color
COLOR_BG_SELECTED = "#4a4a4a"  # Selected / hover neutral

# Primary (green) — shop buy, confirm, place
COLOR_PRIMARY = "#5a8f4a"
COLOR_PRIMARY_HOVER = "#6ba85a"
COLOR_PRIMARY_PRESSED = "#4a7f3a"
COLOR_PRIMARY_FRAME_BG = "#3a4a3a"  # Frame background with green border

# Danger (red) — sell, remove, delete
COLOR_DANGER = "#8f4a4a"
COLOR_DANGER_HOVER = "#a85a5a"
COLOR_DANGER_PRESSED = "#7f3a3a"
COLOR_DANGER_FRAME_BG = "#4a3a3a"  # Frame background with danger border

# Social (blue) — visit friend
COLOR_SOCIAL = "#4a6a8f"
COLOR_SOCIAL_HOVER = "#5a7aa5"
COLOR_SOCIAL_PRESSED = "#3a5a7f"
COLOR_SOCIAL_FRAME_BG = "#3a4a5a"  # Frame background with social border

# Move (blue variant) — move building/decoration
COLOR_MOVE = "#4a7a9f"
COLOR_MOVE_HOVER = "#5a8abf"

# Return (orange-brown) — return home
COLOR_RETURN = "#8f6a4a"
COLOR_RETURN_HOVER = "#a87a5a"
COLOR_RETURN_PRESSED = "#7f5a3a"

# Neutral (gray) — settings, cancel, close
COLOR_NEUTRAL = "#666"
COLOR_NEUTRAL_HOVER = "#777"
COLOR_NEUTRAL_PRESSED = "#555"

# Upgrade (blue-purple) — building upgrades
COLOR_UPGRADE = "#5a5a8f"
COLOR_UPGRADE_HOVER = "#6a6a9f"
COLOR_UPGRADE_FRAME_BG = "#3a3a4a"  # Frame background with upgrade border

# Text
COLOR_TEXT_WHITE = "#fff"
COLOR_TEXT_LIGHT = "#ccc"
COLOR_TEXT_MUTED = "#aaa"
COLOR_TEXT_DIMMED = "#888"
COLOR_TEXT_ACCENT = "#f0c040"      # Gold — money, headings

# Quality tier colors
COLOR_QUALITY_ARTISAN = "#d4af37"  # Gold
COLOR_QUALITY_PREMIUM = "#7dd"     # Cyan
COLOR_QUALITY_GOOD = "#7d7"        # Green
COLOR_QUALITY_BASIC = "#aaa"       # Gray

# Quality tier background tints (for rows)
COLOR_QUALITY_BG_ARTISAN = "#4a4a5a"  # Purple tint
COLOR_QUALITY_BG_PREMIUM = "#4a5a4a"  # Green tint
COLOR_QUALITY_BG_GOOD = "#4a4a4a"     # Neutral
COLOR_QUALITY_BG_BASIC = "#3a3a3a"    # Dark

# Placement mode indicator (olive/dark yellow)
COLOR_PLACEMENT_BG = "#4a4a2a"
COLOR_PLACEMENT_BORDER = "#6a6a3a"

# Warning (low feed, etc.)
COLOR_WARNING = "#fa8"
COLOR_WARNING_BG = "#4a3a2a"
COLOR_WARNING_BORDER = "#6a4a2a"

# =============================================================================
# Style Helpers
# =============================================================================

def primary_button_style(font_size: int = 14) -> str:
    """Green 'confirm / buy' button style."""
    return f"""
        QPushButton {{
            background-color: {COLOR_PRIMARY};
            color: {COLOR_TEXT_WHITE};
            border: none;
            padding: 12px;
            font-size: {font_size}px;
            font-weight: bold;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRIMARY_PRESSED};
        }}
    """


def danger_button_style(font_size: int = 14) -> str:
    """Red 'sell / remove' button style."""
    return f"""
        QPushButton {{
            background-color: {COLOR_DANGER};
            color: {COLOR_TEXT_WHITE};
            border: none;
            padding: 12px;
            font-size: {font_size}px;
            font-weight: bold;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_DANGER_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_DANGER_PRESSED};
        }}
    """


def neutral_button_style(font_size: int = 14) -> str:
    """Gray 'close / cancel' button style."""
    return f"""
        QPushButton {{
            background-color: {COLOR_NEUTRAL};
            color: {COLOR_TEXT_WHITE};
            border: none;
            padding: 12px;
            font-size: {font_size}px;
            font-weight: bold;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_NEUTRAL_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_NEUTRAL_PRESSED};
        }}
    """


def social_button_style(font_size: int = 14) -> str:
    """Blue 'visit friend' button style."""
    return f"""
        QPushButton {{
            background-color: {COLOR_SOCIAL};
            color: {COLOR_TEXT_WHITE};
            border: none;
            padding: 12px;
            font-size: {font_size}px;
            font-weight: bold;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_SOCIAL_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_SOCIAL_PRESSED};
        }}
    """


def return_button_style(font_size: int = 14) -> str:
    """Orange-brown 'return home' button style."""
    return f"""
        QPushButton {{
            background-color: {COLOR_RETURN};
            color: {COLOR_TEXT_WHITE};
            border: none;
            padding: 12px;
            font-size: {font_size}px;
            font-weight: bold;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_RETURN_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_RETURN_PRESSED};
        }}
    """


def move_button_style(font_size: int = 14) -> str:
    """Blue 'move' button style (buildings/decorations)."""
    return f"""
        QPushButton {{
            background-color: {COLOR_MOVE};
            color: {COLOR_TEXT_WHITE};
            border: none;
            padding: 10px 25px;
            font-size: {font_size}px;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_MOVE_HOVER};
        }}
    """


def upgrade_button_style(enabled: bool = True, font_size: int = 13) -> str:
    """Blue-purple upgrade button style."""
    bg = COLOR_UPGRADE if enabled else COLOR_BG_BORDER
    text = COLOR_TEXT_WHITE if enabled else "#888"
    hover = COLOR_UPGRADE_HOVER if enabled else COLOR_BG_BORDER
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {text};
            border: none;
            padding: 10px 20px;
            font-size: {font_size}px;
            font-weight: bold;
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
    """


def quality_color(quality: str) -> str:
    """Return the text color for a quality tier string value."""
    return {
        "artisan": COLOR_QUALITY_ARTISAN,
        "premium": COLOR_QUALITY_PREMIUM,
        "good": COLOR_QUALITY_GOOD,
        "basic": COLOR_QUALITY_BASIC,
    }.get(quality, COLOR_QUALITY_BASIC)


def quality_bg_color(quality: str) -> str:
    """Return the background tint color for a quality tier string value."""
    return {
        "artisan": COLOR_QUALITY_BG_ARTISAN,
        "premium": COLOR_QUALITY_BG_PREMIUM,
        "good": COLOR_QUALITY_BG_GOOD,
        "basic": COLOR_QUALITY_BG_BASIC,
    }.get(quality, COLOR_QUALITY_BG_BASIC)


def dialog_style() -> str:
    """Base QDialog background style."""
    return f"QDialog {{ background-color: {COLOR_BG_DARK}; }}"


def tab_widget_style() -> str:
    """Standard tab widget style."""
    return f"""
        QTabWidget::pane {{
            border: 1px solid {COLOR_BG_BORDER};
            background-color: {COLOR_BG_PANEL};
        }}
        QTabBar::tab {{
            background-color: {COLOR_BG_PANEL};
            color: {COLOR_TEXT_MUTED};
            padding: 10px 20px;
            border: 1px solid {COLOR_BG_BORDER};
            border-bottom: none;
        }}
        QTabBar::tab:selected {{
            background-color: {COLOR_PRIMARY_FRAME_BG};
            color: {COLOR_TEXT_WHITE};
        }}
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
    """


def money_label_style() -> str:
    """Style for the money / balance display label."""
    return f"""
        font-size: 18px;
        font-weight: bold;
        color: {COLOR_TEXT_ACCENT};
        padding: 10px;
        background-color: {COLOR_BG_PANEL};
        border-radius: 6px;
    """


def stat_label_style() -> str:
    """Style for HUD stat labels."""
    return f"""
        QLabel {{
            color: {COLOR_TEXT_WHITE};
            font-size: 14px;
            padding: 5px;
            background-color: {COLOR_BG_PANEL};
            border-radius: 4px;
        }}
    """


def inventory_label_style() -> str:
    """Style for inventory/feed display labels."""
    return f"""
        color: #bbb;
        font-size: 13px;
        padding: 8px;
        background-color: {COLOR_BG_ITEM};
        border-radius: 4px;
        border: 1px solid {COLOR_BG_BORDER};
    """


def section_title_style() -> str:
    """Style for section title labels (Inventory, Feed Supply, etc.)."""
    return f"""
        QLabel {{
            color: {COLOR_TEXT_ACCENT};
            font-size: 16px;
            font-weight: bold;
            padding: 8px 5px 4px 5px;
            margin-top: 5px;
        }}
    """


def primary_frame_style() -> str:
    """Green-bordered frame (header boxes in dialogs)."""
    return f"""
        background-color: {COLOR_PRIMARY_FRAME_BG};
        border: 2px solid {COLOR_PRIMARY};
        border-radius: 8px;
    """


def shop_item_style(enabled: bool = True) -> str:
    """Style for ShopItemWidget frames."""
    bg = "#3a4a3a" if enabled else "#2a2a2a"
    border = COLOR_PRIMARY if enabled else COLOR_BG_BORDER
    hover_bg = "#4a5a4a" if enabled else bg
    hover_border = COLOR_PRIMARY_HOVER if enabled else border
    return f"""
        ShopItemWidget {{
            background-color: {bg};
            border: 2px solid {border};
            border-radius: 8px;
            padding: 8px;
        }}
        ShopItemWidget:hover {{
            background-color: {hover_bg};
            border-color: {hover_border};
        }}
    """
