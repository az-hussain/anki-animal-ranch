"""
Market Dialog - Sell products and animals for money.

This dialog allows players to sell their collected products
(eggs, milk, truffles) and animals at market prices.
"""

from __future__ import annotations

from ...utils.logger import get_logger
from ..theme import (
    COLOR_BG_BORDER,
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BG_SELECTED,
    COLOR_NEUTRAL,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_QUALITY_ARTISAN,
    COLOR_QUALITY_BASIC,
    COLOR_QUALITY_BG_ARTISAN,
    COLOR_QUALITY_BG_BASIC,
    COLOR_QUALITY_BG_GOOD,
    COLOR_QUALITY_BG_PREMIUM,
    COLOR_QUALITY_GOOD,
    COLOR_QUALITY_PREMIUM,
    COLOR_RETURN,
    COLOR_RETURN_HOVER,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_DIMMED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
    danger_button_style,
    neutral_button_style,
)
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.constants import (
    ProductQuality,
    ProductType,
)
from ...models.player import parse_inventory
from ...services.market_service import sell_all_products, sell_animal, sell_product
from ...services.pricing import inventory_value
from ..widgets.animal_row import AnimalRow
from ..widgets.product_row import ProductRow

if TYPE_CHECKING:
    from ...models.farm import Farm

logger = get_logger(__name__)




class MarketDialog(QDialog):
    """
    Dialog for selling products and animals at market.
    
    Features two tabs:
    - Products: Sell eggs, milk, truffles
    - Animals: Sell livestock
    """
    
    products_sold = pyqtSignal(str, int, int)  # product_type, quantity, total_value
    animal_sold = pyqtSignal(str, int)  # animal_id, sale_value
    
    def __init__(self, farm: Farm, parent: QWidget | None = None):
        super().__init__(parent)
        self.farm = farm
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Farm Market")
        self.setMinimumSize(780, 500)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_DARK};
            }}
            QTabWidget::pane {{
                border: 1px solid {COLOR_BG_BORDER};
                background-color: {COLOR_BG_DARK};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT_MUTED};
                padding: 10px 30px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLOR_BG_SELECTED};
                color: {COLOR_TEXT_WHITE};
            }}
            QTabBar::tab:hover {{
                background-color: #454545;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🏪 Farm Market")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_ACCENT};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current money display
        self.money_label = QLabel(f"💰 Current Balance: ${self.farm.money:,}")
        self.money_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_QUALITY_GOOD};
                font-size: 16px;
                padding: 10px;
                background-color: {COLOR_BG_PANEL};
                border-radius: 6px;
            }}
        """)
        self.money_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.money_label)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Products tab
        products_tab = self._create_products_tab()
        self.tabs.addTab(products_tab, "📦 Products")
        
        # Animals tab
        animals_tab = self._create_animals_tab()
        self.tabs.addTab(animals_tab, "🐾 Animals")
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(neutral_button_style())
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _create_products_tab(self) -> QWidget:
        """Create the products tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(8)
        
        # Subtitle
        subtitle = QLabel("Sell your farm products! Higher quality = better prices.")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_DIMMED}; font-size: 12px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Scroll area for products
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{
                background-color: {COLOR_BG_PANEL}; width: 10px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_NEUTRAL}; border-radius: 5px; min-height: 20px;
            }}
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(6)
        
        # Product rows - organized by product type, then quality
        self.product_rows: list[ProductRow] = []

        # Parse inventory into structured format
        products_by_type: dict[ProductType, dict[ProductQuality, int]] = {
            pt: {} for pt in ProductType
        }
        for product_type, quality, count in parse_inventory(self.farm.player.inventory):
            products_by_type[product_type][quality] = count

        # Create rows for each product type and quality (highest quality first)
        quality_order = [ProductQuality.ARTISAN, ProductQuality.PREMIUM, ProductQuality.GOOD, ProductQuality.BASIC]
        
        for product_type in [ProductType.EGG, ProductType.MILK, ProductType.TRUFFLE]:
            qualities = products_by_type.get(product_type, {})
            
            for quality in quality_order:
                quantity = qualities.get(quality, 0)
                if quantity > 0:  # Only show rows with items
                    row = ProductRow(product_type, quality, quantity)
                    row.sell_clicked.connect(self._on_sell_product)
                    self.product_rows.append(row)
                    scroll_layout.addWidget(row)
        
        # If no products, show message
        if not self.product_rows:
            empty_label = QLabel("No products in inventory")
            empty_label.setStyleSheet(f"color: {COLOR_NEUTRAL}; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(empty_label)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

        # Total inventory value
        total_value = self._calculate_product_value()
        self.product_total_label = QLabel(f"📊 Total Value: ${total_value:,}")
        self.product_total_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_MUTED};
                font-size: 14px;
                padding: 8px;
            }}
        """)
        self.product_total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.product_total_label)
        
        # Sell All Products button
        if total_value > 0:
            sell_all_btn = QPushButton(f"💰 Sell All Products (${total_value:,})")
            sell_all_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #8f4a8f;
                    color: {COLOR_TEXT_WHITE};
                    border: none;
                    padding: 12px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 8px;
                }}
                QPushButton:hover {{ background-color: #a85aa8; }}
            """)
            sell_all_btn.clicked.connect(self._on_sell_all_products)
            layout.addWidget(sell_all_btn)
        
        return tab
    
    def _create_animals_tab(self) -> QWidget:
        """Create the animals tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(10)
        
        # Subtitle
        subtitle = QLabel("Sell your livestock at market prices!")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_DIMMED}; font-size: 13px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Scroll area for animal list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {COLOR_BG_PANEL};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLOR_NEUTRAL};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #6a6a6a;
            }}
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(8)
        
        # Animal rows
        self.animal_rows: list[AnimalRow] = []
        animals = list(self.farm.animals.values())
        
        if animals:
            for animal in animals:
                row = AnimalRow(animal)
                row.sell_clicked.connect(self._on_sell_animal)
                self.animal_rows.append(row)
                scroll_layout.addWidget(row)
        else:
            empty_label = QLabel("No animals to sell")
            empty_label.setStyleSheet(f"color: {COLOR_NEUTRAL}; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(empty_label)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

        # Total animal value
        total_value = self._calculate_animal_value()
        self.animal_total_label = QLabel(f"🐾 Total Animal Value: ${total_value:,}")
        self.animal_total_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXT_MUTED};
                font-size: 14px;
                padding: 10px;
            }}
        """)
        self.animal_total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.animal_total_label)
        
        return tab
    
    def _calculate_product_value(self) -> int:
        """Calculate total value of all products (with quality multipliers)."""
        return inventory_value(self.farm.player.inventory)
    
    def _calculate_animal_value(self) -> int:
        """Calculate total value of all animals."""
        return sum(animal.sale_value for animal in self.farm.animals.values())
    
    def _on_sell_product(self, inventory_key: str, quantity: int) -> None:
        """Handle selling a product (with quality tier)."""
        total_value = sell_product(self.farm, inventory_key, quantity)
        if total_value > 0:
            self.products_sold.emit(inventory_key, quantity, total_value)
        self._refresh()
    
    def _on_sell_all_products(self) -> None:
        """Sell all products in inventory (with quality pricing)."""
        total_earned = sell_all_products(self.farm)
        if total_earned > 0:
            self.products_sold.emit("all", 0, total_earned)
        self._refresh()
    
    def _on_sell_animal(self, animal_id: str) -> None:
        """Handle selling an animal."""
        sale_value = sell_animal(self.farm, animal_id)
        if sale_value > 0:
            self.animal_sold.emit(animal_id, sale_value)
        self._refresh()
    
    def _refresh(self) -> None:
        """Refresh the dialog to show updated values."""
        # Update money label
        self.money_label.setText(f"💰 Current Balance: ${self.farm.money:,}")
        
        # Save current tab index
        current_tab = self.tabs.currentIndex()
        
        # Remove old tabs
        while self.tabs.count() > 0:
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            widget.deleteLater()
        
        # Recreate tabs with fresh data
        products_tab = self._create_products_tab()
        self.tabs.addTab(products_tab, "📦 Products")
        
        animals_tab = self._create_animals_tab()
        self.tabs.addTab(animals_tab, "🐾 Animals")
        
        # Restore tab index
        self.tabs.setCurrentIndex(current_tab)
