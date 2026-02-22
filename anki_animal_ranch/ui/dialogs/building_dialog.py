"""
Building Details Dialog - View and manage a building and its animals.

Shows:
- Building info (name, level, capacity)
- Upgrade options with cost/benefits preview
- List of all animals inside with their stats
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...core.constants import (
    BUILDING_CAPACITIES,
    BUILDING_DISPLAY_INFO,
    BUILDING_PRODUCTION_BONUSES,
    BUILDING_UPGRADE_COSTS,
    MAX_BUILDING_LEVEL,
    BuildingType,
)
from ...utils.logger import get_logger
from ..theme import (
    COLOR_BG_BORDER,
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_PRIMARY,
    COLOR_PRIMARY_FRAME_BG,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_DIMMED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
    COLOR_UPGRADE,
    COLOR_UPGRADE_FRAME_BG,
    move_button_style,
    neutral_button_style,
    upgrade_button_style,
)

if TYPE_CHECKING:
    from ...models.animal import Animal
    from ...models.building import Building
    from ...models.farm import Farm

logger = get_logger(__name__)


class AnimalStatsWidget(QFrame):
    """Widget showing a single animal's stats."""
    
    def __init__(self, animal: Animal, parent: QWidget | None = None):
        super().__init__(parent)
        self.animal = animal
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        self.setStyleSheet(f"""
            AnimalStatsWidget {{
                background-color: {COLOR_BG_PANEL};
                border: 1px solid {COLOR_BG_BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        
        # Animal emoji and type
        type_emojis = {"chicken": "🐔", "pig": "🐷", "cow": "🐄"}
        emoji = type_emojis.get(self.animal.type.value, "🐾")
        
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(emoji_label)
        
        # Info column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Name and stage
        stage = self.animal.growth_stage.value.capitalize()
        name_label = QLabel(f"{self.animal.type.value.capitalize()} ({stage})")
        name_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLOR_TEXT_WHITE};")
        info_layout.addWidget(name_label)
        
        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        
        # Maturity progress
        maturity_pct = int(self.animal.maturity * 100)
        maturity_label = QLabel(f"📈 {maturity_pct}%")
        maturity_label.setStyleSheet("font-size: 11px; color: #8af;")
        maturity_label.setToolTip(f"Maturity: {maturity_pct}%")
        stats_layout.addWidget(maturity_label)
        
        # Health (affects product quality)
        health_pct = int(self.animal.health * 100)
        health_color = "#8f8" if health_pct >= 80 else "#ff8" if health_pct >= 60 else "#f88"
        health_label = QLabel(f"❤️ {health_pct}%")
        health_label.setStyleSheet(f"font-size: 11px; color: {health_color};")
        health_label.setToolTip(f"Health: {health_pct}% (affects product quality)")
        stats_layout.addWidget(health_label)
        
        stats_layout.addStretch()
        info_layout.addLayout(stats_layout)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Production status
        if self.animal.is_mature:
            prod_label = QLabel("✅ Producing")
            prod_label.setStyleSheet("font-size: 10px; color: #8f8;")
        else:
            prod_label = QLabel("🌱 Growing")
            prod_label.setStyleSheet("font-size: 10px; color: #fa8;")
        layout.addWidget(prod_label)


class BuildingDetailsDialog(QDialog):
    """
    Dialog showing building details and allowing upgrades.
    
    Signals:
        building_upgraded: Emitted when building is upgraded
    """
    
    building_upgraded = pyqtSignal(str)  # building_id
    building_move_requested = pyqtSignal(str)  # building_id
    
    def __init__(
        self,
        building: Building,
        farm: Farm,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.building = building
        self.farm = farm
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        display = BUILDING_DISPLAY_INFO.get(self.building.type.value, {"name": "Building", "emoji": "🏠"})
        
        self.setWindowTitle(f"{display['emoji']} {self.building.display_name}")
        self.setMinimumSize(450, 400)
        self.resize(500, 500)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Header
        header = self._create_header(display)
        layout.addWidget(header)
        
        # Upgrade section
        upgrade_section = self._create_upgrade_section()
        layout.addWidget(upgrade_section)
        
        # Animals section
        animals_label = QLabel(f"🐾 Animals ({self.building.current_occupancy}/{self.building.capacity})")
        animals_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_MUTED}; margin-top: 10px;")
        layout.addWidget(animals_label)
        
        # Scrollable animals list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        self.animals_layout = QVBoxLayout(scroll_content)
        self.animals_layout.setSpacing(6)
        
        self._populate_animals()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Move button
        move_btn = QPushButton("📍 Move")
        move_btn.setStyleSheet(move_button_style())
        move_btn.clicked.connect(self._on_move_clicked)
        buttons_layout.addWidget(move_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(neutral_button_style())
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_header(self, display: dict) -> QFrame:
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
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Emoji
        emoji_label = QLabel(display["emoji"])
        emoji_label.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        emoji_label.setFixedWidth(60)
        layout.addWidget(emoji_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(self.building.display_name)
        name_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT_WHITE}; background: transparent; border: none;")
        name_label.setMinimumWidth(200)
        info_layout.addWidget(name_label)
        
        level_label = QLabel(f"Level {self.building.level} / {MAX_BUILDING_LEVEL}")
        level_label.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED}; background: transparent; border: none;")
        info_layout.addWidget(level_label)
        
        capacity_label = QLabel(f"Capacity: {self.building.current_occupancy}/{self.building.capacity}")
        capacity_label.setStyleSheet("font-size: 12px; color: #8a8; background: transparent; border: none;")
        info_layout.addWidget(capacity_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        return frame
    
    def _create_upgrade_section(self) -> QFrame:
        """Create the upgrade section."""
        frame = QFrame()
        frame.setObjectName("upgradeFrame")
        frame.setStyleSheet(f"""
            #upgradeFrame {{
                background-color: {COLOR_UPGRADE_FRAME_BG};
                border: 2px solid {COLOR_UPGRADE};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("⬆️ Upgrade Building")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #aaf; background: transparent; border: none;")
        layout.addWidget(title)
        
        if self.building.can_upgrade:
            # Current vs Next level comparison
            current_level = self.building.level
            next_level = current_level + 1
            
            # Get capacities
            capacities = BUILDING_CAPACITIES.get(self.building.type, [5, 10, 20, 40])
            current_cap = capacities[current_level - 1] if current_level <= len(capacities) else capacities[-1]
            next_cap = capacities[next_level - 1] if next_level <= len(capacities) else capacities[-1]
            
            # Get production bonuses
            current_bonus = BUILDING_PRODUCTION_BONUSES[current_level - 1] if current_level <= len(BUILDING_PRODUCTION_BONUSES) else 1.0
            next_bonus = BUILDING_PRODUCTION_BONUSES[next_level - 1] if next_level <= len(BUILDING_PRODUCTION_BONUSES) else 1.5
            
            # Comparison text - using separate labels for better rendering
            level_text = QLabel(f"Level {current_level} → Level {next_level}")
            level_text.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_WHITE}; background: transparent; border: none;")
            layout.addWidget(level_text)
            
            cap_text = QLabel(f"📦 Capacity: {current_cap} → {next_cap} (+{next_cap - current_cap})")
            cap_text.setStyleSheet("font-size: 12px; color: #8f8; background: transparent; border: none;")
            layout.addWidget(cap_text)
            
            prod_text = QLabel(f"⚡ Production: {int(current_bonus*100)}% → {int(next_bonus*100)}% (+{int((next_bonus-current_bonus)*100)}%)")
            prod_text.setStyleSheet("font-size: 12px; color: #8af; background: transparent; border: none;")
            layout.addWidget(prod_text)
            
            # Cost and upgrade button
            cost = self.building.upgrade_cost
            can_afford = self.farm.money >= cost
            
            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)
            
            cost_label = QLabel(f"💰 Cost: ${cost:,}")
            cost_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_ACCENT if can_afford else '#f66'}; background: transparent; border: none;")
            btn_row.addWidget(cost_label)
            
            btn_row.addStretch()
            
            self.upgrade_btn = QPushButton(f"⬆️ Upgrade to Lv.{next_level}")
            self.upgrade_btn.setEnabled(can_afford)
            self.upgrade_btn.setStyleSheet(upgrade_button_style(enabled=can_afford))
            self.upgrade_btn.clicked.connect(self._on_upgrade_clicked)
            btn_row.addWidget(self.upgrade_btn)
            
            layout.addLayout(btn_row)
            
            if not can_afford:
                need_more = QLabel(f"⚠️ Need ${cost - self.farm.money:,} more")
                need_more.setStyleSheet("font-size: 11px; color: #f88; background: transparent; border: none;")
                layout.addWidget(need_more)
        else:
            # Max level reached
            max_label = QLabel("🏆 Maximum Level Reached!")
            max_label.setStyleSheet("font-size: 14px; color: #fa0; font-weight: bold; background: transparent; border: none;")
            layout.addWidget(max_label)
            
            bonus = BUILDING_PRODUCTION_BONUSES[-1]
            bonus_label = QLabel(f"⚡ Production Bonus: +{int((bonus-1)*100)}%")
            bonus_label.setStyleSheet("font-size: 12px; color: #8f8; background: transparent; border: none;")
            layout.addWidget(bonus_label)
        
        return frame
    
    def _populate_animals(self) -> None:
        """Populate the animals list."""
        # Clear existing
        while self.animals_layout.count():
            item = self.animals_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get animals in this building
        animals = [
            self.farm.animals[aid]
            for aid in self.building.animals
            if aid in self.farm.animals
        ]
        
        if not animals:
            empty_label = QLabel("No animals yet. Buy some from the Shop!")
            empty_label.setStyleSheet(f"color: {COLOR_TEXT_DIMMED}; font-size: 13px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.animals_layout.addWidget(empty_label)
        else:
            for animal in animals:
                widget = AnimalStatsWidget(animal)
                self.animals_layout.addWidget(widget)
        
        self.animals_layout.addStretch()
    
    def _on_upgrade_clicked(self) -> None:
        """Handle upgrade button click."""
        cost = self.building.upgrade_cost
        
        if not self.farm.spend_money(cost, f"Upgrade {self.building.display_name}"):
            logger.warning("Cannot afford upgrade")
            return
        
        if self.building.upgrade():
            logger.info(f"Upgraded {self.building.display_name} to level {self.building.level}")
            self.building_upgraded.emit(self.building.id)
            
            # Refresh the dialog
            self._refresh_ui()
    
    def _on_move_clicked(self) -> None:
        """Handle move button click."""
        logger.info(f"Move requested for building {self.building.id}")
        self.building_move_requested.emit(self.building.id)
        self.close()
    
    def _refresh_ui(self) -> None:
        """Refresh the dialog after upgrade."""
        # Recreate the whole dialog is simpler than updating individual parts
        self.close()
        
        # The main window will handle reopening if needed
        # For now, just close and let user reopen
