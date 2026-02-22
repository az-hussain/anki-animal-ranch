"""
Market service — sell transactions.

All sell operations (products and animals) flow through these functions.
Callers (MarketDialog) should never directly mutate farm.player.inventory
or call farm.add_money / farm.statistics.record_sale themselves.
"""

from __future__ import annotations

from ..models.farm import Farm
from ..models.player import parse_inventory_item
from ..utils.logger import get_logger
from .pricing import product_unit_price

logger = get_logger(__name__)


def sell_product(farm: Farm, inventory_key: str, quantity: int) -> int:
    """
    Sell `quantity` units of a product from the player's inventory.

    Args:
        farm: The current Farm instance.
        inventory_key: Inventory key such as "egg_premium".
        quantity: Number of units to sell.

    Returns:
        Total money earned (0 if the sale could not be completed).
    """
    current = farm.player.inventory.get(inventory_key, 0)
    quantity = min(quantity, current)
    if quantity <= 0:
        return 0

    parsed = parse_inventory_item(inventory_key, quantity)
    if parsed is None:
        return 0

    product_type, quality, _ = parsed
    price = product_unit_price(product_type, quality)
    total = quantity * price

    farm.player.remove_from_inventory(inventory_key, quantity)
    farm.add_money(total, f"Sold {quantity} {inventory_key}")
    farm.statistics.record_sale(total, product_type.value, is_animal=False)

    logger.info(f"Sold {quantity} {inventory_key} for ${total}")
    return total


def sell_all_products(farm: Farm) -> int:
    """
    Sell every product in the player's inventory.

    Args:
        farm: The current Farm instance.

    Returns:
        Total money earned.
    """
    total_earned = 0
    for key in list(farm.player.inventory.keys()):
        quantity = farm.player.inventory.get(key, 0)
        if quantity <= 0:
            continue
        earned = sell_product(farm, key, quantity)
        total_earned += earned

    if total_earned > 0:
        logger.info(f"Sold all products for ${total_earned}")
    return total_earned


def sell_animal(farm: Farm, animal_id: str) -> int:
    """
    Sell an animal from the farm.

    Args:
        farm: The current Farm instance.
        animal_id: ID of the animal to sell.

    Returns:
        Sale value (0 if animal not found).
    """
    animal = farm.animals.get(animal_id)
    if not animal:
        return 0

    sale_value = animal.sale_value

    # Remove from building
    if animal.building_id:
        building = farm.buildings.get(animal.building_id)
        if building:
            building.remove_animal(animal_id)

    # Remove from farm
    farm.remove_animal(animal_id)

    # Record transaction
    farm.add_money(sale_value, f"Sold {animal.display_name}")
    farm.statistics.record_sale(sale_value, animal.type.value, is_animal=True)

    logger.info(f"Sold {animal.display_name} for ${sale_value}")
    return sale_value
