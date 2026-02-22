"""
Pricing service — single source of truth for all product price calculations.

All price formulas live here. Dialogs and systems import from this module
rather than re-implementing the formula inline.
"""

from __future__ import annotations

from ..core.constants import (
    PRODUCT_BASE_PRICES,
    PRODUCT_QUALITY_MULTIPLIERS,
    ProductQuality,
    ProductType,
)
from ..models.player import parse_inventory


def product_unit_price(product_type: ProductType, quality: ProductQuality) -> int:
    """
    Return the sale price for one unit of a product.

    Args:
        product_type: Type of the product (EGG, MILK, TRUFFLE)
        quality: Quality tier (BASIC, GOOD, PREMIUM, ARTISAN)

    Returns:
        Unit price in game currency.
    """
    base = PRODUCT_BASE_PRICES.get(product_type, 10)
    mult = PRODUCT_QUALITY_MULTIPLIERS.get(quality, 1.0)
    return int(base * mult)
    # TODO: multiply by SEASON_PRICE_MODIFIERS[current_season][product_type] when seasons are enabled


def inventory_value(inventory: dict[str, int]) -> int:
    """
    Calculate the total sale value of all items in a player inventory dict.

    Args:
        inventory: Raw inventory dict (e.g. {"egg_premium": 5, "milk_basic": 3})

    Returns:
        Total value in game currency.
    """
    total = 0
    for product_type, quality, count in parse_inventory(inventory):
        total += count * product_unit_price(product_type, quality)
    return total
