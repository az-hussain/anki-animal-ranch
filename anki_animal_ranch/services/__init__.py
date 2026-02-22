"""
Business logic services.

Services are the single source of truth for all user-triggered operations
(buying, selling). They take a Farm instance and return results — no PyQt6,
no rendering, no UI side effects.
"""

from .market_service import sell_all_products, sell_animal, sell_product
from .pricing import inventory_value, product_unit_price
from .shop_service import purchase_animal, purchase_building, purchase_feed

__all__ = [
    "product_unit_price",
    "inventory_value",
    "sell_product",
    "sell_all_products",
    "sell_animal",
    "purchase_animal",
    "purchase_building",
    "purchase_feed",
]
