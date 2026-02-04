"""
Market Dialog - Sell products and animals for money.

This dialog allows players to sell their collected products
(eggs, milk, truffles) and animals at market prices.
"""

from __future__ import annotations

from ...utils.logger import get_logger
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.constants import (
    ANIMAL_BASE_SALE_PRICES,
    PRODUCT_BASE_PRICES,
    PRODUCT_QUALITY_MULTIPLIERS,
    AnimalType,
    ProductQuality,
    ProductType,
)

if TYPE_CHECKING:
    from ...models.animal import Animal
    from ...models.farm import Farm

logger = get_logger(__name__)


class ProductRow(QFrame):
    """A row displaying a product with quality tier and sell controls."""
    
    sell_clicked = pyqtSignal(str, int)  # inventory_key (e.g. "egg_premium"), quantity
    
    def __init__(
        self,
        product_type: ProductType,
        quality: ProductQuality,
        quantity: int,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.product_type = product_type
        self.quality = quality
        self.quantity = quantity
        
        # Calculate price with quality multiplier
        base_price = PRODUCT_BASE_PRICES.get(product_type, 10)
        quality_mult = PRODUCT_QUALITY_MULTIPLIERS.get(quality, 1.0)
        self.price = int(base_price * quality_mult)
        
        # Inventory key format: "egg_premium"
        self.inventory_key = f"{product_type.value}_{quality.value}"
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the row UI."""
        # Color based on quality
        quality_colors = {
            ProductQuality.ARTISAN: "#4a4a5a",  # Purple tint
            ProductQuality.PREMIUM: "#4a5a4a",  # Green tint
            ProductQuality.GOOD: "#4a4a4a",     # Neutral
            ProductQuality.BASIC: "#3a3a3a",    # Dark
        }
        bg_color = quality_colors.get(self.quality, "#3a3a3a")
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 8px;
                padding: 5px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)
        
        # Product icon
        emoji = self._get_emoji()
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 20px;")
        emoji_label.setFixedWidth(35)
        layout.addWidget(emoji_label)
        
        # Product name and quality
        quality_stars = self._get_quality_stars()
        name_label = QLabel(f"{self.product_type.value.capitalize()} {quality_stars}")
        name_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        name_label.setFixedWidth(140)
        layout.addWidget(name_label)
        
        # Quantity owned
        self.quantity_label = QLabel(f"×{self.quantity}")
        self.quantity_label.setStyleSheet("color: #aaa; font-size: 13px;")
        self.quantity_label.setFixedWidth(50)
        layout.addWidget(self.quantity_label)
        
        # Price per unit (with quality bonus shown)
        price_color = self._get_price_color()
        price_label = QLabel(f"${self.price}")
        price_label.setStyleSheet(f"color: {price_color}; font-size: 13px; font-weight: bold;")
        price_label.setFixedWidth(50)
        layout.addWidget(price_label)
        
        # Spacer
        layout.addStretch()
        
        # Sell controls (only if we have items)
        if self.quantity > 0:
            # Quantity selector with +/- buttons
            self._sell_qty = 1
            
            # Minus button
            minus_btn = QPushButton("−")
            minus_btn.setFixedSize(28, 28)
            minus_btn.setStyleSheet("""
                QPushButton {
                    background-color: #5a5a5a;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #6a6a6a; }
            """)
            minus_btn.clicked.connect(self._decrement)
            layout.addWidget(minus_btn)
            
            # Quantity display
            self.qty_display = QLabel("1")
            self.qty_display.setStyleSheet("""
                background-color: #4a4a4a;
                color: white;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            """)
            self.qty_display.setFixedWidth(40)
            self.qty_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.qty_display)
            
            # Plus button
            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(28, 28)
            plus_btn.setStyleSheet("""
                QPushButton {
                    background-color: #5a5a5a;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #6a6a6a; }
            """)
            plus_btn.clicked.connect(self._increment)
            layout.addWidget(plus_btn)
            
            # Total value
            self.total_label = QLabel(f"= ${self.price}")
            self.total_label.setStyleSheet("color: #f0c040; font-size: 13px; font-weight: bold;")
            self.total_label.setFixedWidth(60)
            layout.addWidget(self.total_label)
            
            # Sell button
            sell_btn = QPushButton("Sell")
            sell_btn.setStyleSheet("""
                QPushButton {
                    background-color: #5a8f4a;
                    color: white;
                    border: none;
                    padding: 6px 15px;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #6ba85a; }
            """)
            sell_btn.clicked.connect(self._on_sell)
            layout.addWidget(sell_btn)
            
            # Sell All button
            sell_all_btn = QPushButton("All")
            sell_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8f6a4a;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #a87a5a; }
            """)
            sell_all_btn.clicked.connect(self._on_sell_all)
            layout.addWidget(sell_all_btn)
        else:
            empty_label = QLabel("—")
            empty_label.setStyleSheet("color: #555; font-size: 13px;")
            layout.addWidget(empty_label)
    
    def _get_emoji(self) -> str:
        """Get emoji for product type."""
        emojis = {
            ProductType.EGG: "🥚",
            ProductType.MILK: "🥛",
            ProductType.TRUFFLE: "🍄",
        }
        return emojis.get(self.product_type, "📦")
    
    def _get_quality_stars(self) -> str:
        """Get star representation of quality."""
        stars = {
            ProductQuality.ARTISAN: "⭐⭐⭐⭐",
            ProductQuality.PREMIUM: "⭐⭐⭐",
            ProductQuality.GOOD: "⭐⭐",
            ProductQuality.BASIC: "⭐",
        }
        return stars.get(self.quality, "⭐")
    
    def _get_price_color(self) -> str:
        """Get color based on quality tier."""
        colors = {
            ProductQuality.ARTISAN: "#d4af37",  # Gold
            ProductQuality.PREMIUM: "#7dd",     # Cyan
            ProductQuality.GOOD: "#7d7",        # Green
            ProductQuality.BASIC: "#aaa",       # Gray
        }
        return colors.get(self.quality, "#aaa")
    
    def _increment(self) -> None:
        """Increment sell quantity."""
        if self._sell_qty < self.quantity:
            self._sell_qty += 1
            self._update_display()
    
    def _decrement(self) -> None:
        """Decrement sell quantity."""
        if self._sell_qty > 1:
            self._sell_qty -= 1
            self._update_display()
    
    def _update_display(self) -> None:
        """Update quantity display and total."""
        self.qty_display.setText(str(self._sell_qty))
        total = self._sell_qty * self.price
        self.total_label.setText(f"= ${total}")
    
    def _on_sell(self) -> None:
        """Handle sell button click."""
        self.sell_clicked.emit(self.inventory_key, self._sell_qty)
    
    def _on_sell_all(self) -> None:
        """Handle sell all button click."""
        self.sell_clicked.emit(self.inventory_key, self.quantity)


class AnimalRow(QFrame):
    """A row displaying an animal with sell controls."""
    
    sell_clicked = pyqtSignal(str)  # animal_id
    
    def __init__(
        self,
        animal: Animal,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.animal = animal
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the row UI."""
        self.setStyleSheet("""
            QFrame {
                background-color: #3a3a3a;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Animal icon and name
        emoji = self._get_emoji()
        name = self.animal.display_name
        name_label = QLabel(f"{emoji} {name}")
        name_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        name_label.setFixedWidth(130)
        layout.addWidget(name_label)
        
        # Stage/maturity info
        stage = self.animal.growth_stage.value.capitalize()
        maturity = f"{self.animal.maturity:.0%}"
        info_label = QLabel(f"{stage} ({maturity})")
        info_label.setStyleSheet("color: #aaa; font-size: 13px;")
        info_label.setFixedWidth(100)
        layout.addWidget(info_label)
        
        # Health (affects sale value)
        health_pct = int(self.animal.health * 100)
        health_label = QLabel(f"❤️ {health_pct}%")
        health_label.setStyleSheet("color: #a77; font-size: 12px;")
        health_label.setFixedWidth(70)
        layout.addWidget(health_label)
        
        # Spacer
        layout.addStretch()
        
        # Sale value
        value = self.animal.sale_value
        value_label = QLabel(f"${value:,}")
        value_label.setStyleSheet("color: #f0c040; font-size: 15px; font-weight: bold;")
        value_label.setFixedWidth(80)
        layout.addWidget(value_label)
        
        # Sell button
        sell_btn = QPushButton("Sell")
        sell_btn.setStyleSheet("""
            QPushButton {
                background-color: #8f4a4a;
                color: white;
                border: none;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #a85a5a;
            }
            QPushButton:pressed {
                background-color: #7f3a3a;
            }
        """)
        sell_btn.clicked.connect(self._on_sell)
        layout.addWidget(sell_btn)
    
    def _get_emoji(self) -> str:
        """Get emoji for animal type."""
        emojis = {
            AnimalType.CHICKEN: "🐔",
            AnimalType.PIG: "🐷",
            AnimalType.COW: "🐄",
        }
        return emojis.get(self.animal.type, "🐾")
    
    def _on_sell(self) -> None:
        """Handle sell button click."""
        self.sell_clicked.emit(self.animal.id)


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
        self.setStyleSheet("""
            QDialog {
                background-color: #2c2c2c;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #2c2c2c;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #aaa;
                padding: 10px 30px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #454545;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🏪 Farm Market")
        title.setStyleSheet("""
            QLabel {
                color: #f0c040;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current money display
        self.money_label = QLabel(f"💰 Current Balance: ${self.farm.money:,}")
        self.money_label.setStyleSheet("""
            QLabel {
                color: #7d7;
                font-size: 16px;
                padding: 10px;
                background-color: #353535;
                border-radius: 6px;
            }
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
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
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
        subtitle.setStyleSheet("color: #888; font-size: 12px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Scroll area for products
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical {
                background-color: #3a3a3a; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5a5a; border-radius: 5px; min-height: 20px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(6)
        
        # Product rows - organized by product type, then quality
        self.product_rows: list[ProductRow] = []
        inventory = self.farm.player.inventory
        
        # Parse inventory into structured format
        products_by_type: dict[ProductType, dict[ProductQuality, int]] = {
            pt: {} for pt in ProductType
        }
        
        for key, count in inventory.items():
            if count <= 0:
                continue
            parts = key.split("_")
            if len(parts) >= 2:
                try:
                    product_type = ProductType(parts[0])
                    quality = ProductQuality(parts[1])
                    products_by_type[product_type][quality] = count
                except (ValueError, KeyError):
                    # Legacy format - treat as basic
                    try:
                        product_type = ProductType(key)
                        products_by_type[product_type][ProductQuality.BASIC] = count
                    except ValueError:
                        pass
            else:
                # Legacy format
                try:
                    product_type = ProductType(key)
                    products_by_type[product_type][ProductQuality.BASIC] = count
                except ValueError:
                    pass
        
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
            empty_label.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(empty_label)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)
        
        # Total inventory value
        total_value = self._calculate_product_value()
        self.product_total_label = QLabel(f"📊 Total Value: ${total_value:,}")
        self.product_total_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 14px;
                padding: 8px;
            }
        """)
        self.product_total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.product_total_label)
        
        # Sell All Products button
        if total_value > 0:
            sell_all_btn = QPushButton(f"💰 Sell All Products (${total_value:,})")
            sell_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8f4a8f;
                    color: white;
                    border: none;
                    padding: 12px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #a85aa8; }
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
        subtitle.setStyleSheet("color: #888; font-size: 13px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Scroll area for animal list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #3a3a3a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6a;
            }
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
            empty_label.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(empty_label)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)
        
        # Total animal value
        total_value = self._calculate_animal_value()
        self.animal_total_label = QLabel(f"🐾 Total Animal Value: ${total_value:,}")
        self.animal_total_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 14px;
                padding: 10px;
            }
        """)
        self.animal_total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.animal_total_label)
        
        return tab
    
    def _calculate_product_value(self) -> int:
        """Calculate total value of all products (with quality multipliers)."""
        inventory = self.farm.player.inventory
        total = 0
        
        for key, quantity in inventory.items():
            if quantity <= 0:
                continue
            
            parts = key.split("_")
            if len(parts) >= 2:
                try:
                    product_type = ProductType(parts[0])
                    quality = ProductQuality(parts[1])
                    base_price = PRODUCT_BASE_PRICES.get(product_type, 10)
                    quality_mult = PRODUCT_QUALITY_MULTIPLIERS.get(quality, 1.0)
                    total += int(quantity * base_price * quality_mult)
                except (ValueError, KeyError):
                    # Legacy format
                    try:
                        product_type = ProductType(key)
                        total += quantity * PRODUCT_BASE_PRICES.get(product_type, 10)
                    except ValueError:
                        pass
            else:
                # Legacy format
                try:
                    product_type = ProductType(key)
                    total += quantity * PRODUCT_BASE_PRICES.get(product_type, 10)
                except ValueError:
                    pass
        
        return total
    
    def _calculate_animal_value(self) -> int:
        """Calculate total value of all animals."""
        return sum(animal.sale_value for animal in self.farm.animals.values())
    
    def _on_sell_product(self, inventory_key: str, quantity: int) -> None:
        """Handle selling a product (with quality tier)."""
        inventory = self.farm.player.inventory
        current_qty = inventory.get(inventory_key, 0)
        
        if quantity > current_qty:
            quantity = current_qty
        
        if quantity <= 0:
            return
        
        # Parse inventory key (e.g., "egg_premium")
        parts = inventory_key.split("_")
        if len(parts) >= 2:
            try:
                product_type = ProductType(parts[0])
                quality = ProductQuality(parts[1])
                base_price = PRODUCT_BASE_PRICES.get(product_type, 10)
                quality_mult = PRODUCT_QUALITY_MULTIPLIERS.get(quality, 1.0)
                price = int(base_price * quality_mult)
            except (ValueError, KeyError):
                return
        else:
            # Legacy format
            try:
                product_type = ProductType(inventory_key)
                price = PRODUCT_BASE_PRICES.get(product_type, 10)
            except ValueError:
                return
        
        total_value = quantity * price
        
        # Update inventory
        inventory[inventory_key] = current_qty - quantity
        if inventory[inventory_key] <= 0:
            del inventory[inventory_key]
        
        # Add money and record statistics
        self.farm.add_money(total_value, f"Sold {quantity} {inventory_key}")
        self.farm.statistics.record_sale(total_value, product_type.value, is_animal=False)
        
        # Emit signal
        self.products_sold.emit(inventory_key, quantity, total_value)
        
        logger.info(f"Sold {quantity} {inventory_key} for ${total_value}")
        
        # Refresh dialog
        self._refresh()
    
    def _on_sell_all_products(self) -> None:
        """Sell all products in inventory (with quality pricing)."""
        inventory = self.farm.player.inventory
        total_earned = 0
        
        # Get all product keys to sell
        keys_to_sell = [k for k in list(inventory.keys()) if inventory.get(k, 0) > 0]
        
        for key in keys_to_sell:
            quantity = inventory.get(key, 0)
            if quantity <= 0:
                continue
            
            # Parse key for quality pricing
            parts = key.split("_")
            if len(parts) >= 2:
                try:
                    product_type = ProductType(parts[0])
                    quality = ProductQuality(parts[1])
                    base_price = PRODUCT_BASE_PRICES.get(product_type, 10)
                    quality_mult = PRODUCT_QUALITY_MULTIPLIERS.get(quality, 1.0)
                    price = int(base_price * quality_mult)
                except (ValueError, KeyError):
                    continue
            else:
                # Legacy format
                try:
                    product_type = ProductType(key)
                    price = PRODUCT_BASE_PRICES.get(product_type, 10)
                except ValueError:
                    continue
            
            # Calculate value and add to total (runs for both formats)
            value = quantity * price
            total_earned += value
            
            # Clear from inventory
            del inventory[key]
            
            logger.info(f"Sold {quantity} {key} for ${value}")
        
        if total_earned > 0:
            self.farm.add_money(total_earned, "Sold all products")
            self.products_sold.emit("all", 0, total_earned)
        
        # Refresh dialog
        self._refresh()
    
    def _on_sell_animal(self, animal_id: str) -> None:
        """Handle selling an animal."""
        animal = self.farm.animals.get(animal_id)
        if not animal:
            return
        
        sale_value = animal.sale_value
        
        # Remove from building
        if animal.building_id:
            building = self.farm.buildings.get(animal.building_id)
            if building:
                building.remove_animal(animal_id)
        
        # Remove from farm
        self.farm.remove_animal(animal_id)
        
        # Add money and record statistics
        self.farm.add_money(sale_value, f"Sold {animal.display_name}")
        self.farm.statistics.record_sale(sale_value, animal.type.value, is_animal=True)
        
        # Emit signal
        self.animal_sold.emit(animal_id, sale_value)
        
        logger.info(f"Sold {animal.display_name} for ${sale_value}")
        
        # Refresh dialog
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
