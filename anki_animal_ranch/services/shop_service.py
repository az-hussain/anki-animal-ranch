"""
Shop service — purchase transactions.

All buy operations (animals, buildings, decorations, feed) flow through
these functions. Callers should not call farm.spend_money or model
constructors directly for purchase operations.

Note: Building and decoration purchases return the model only. The caller
(MainWindow) is responsible for creating sprites and marking grid tiles.
"""

from __future__ import annotations

from ..core.constants import (
    ANIMAL_PURCHASE_PRICES,
    BUILDING_PURCHASE_COSTS,
    DECORATION_COSTS,
    AnimalType,
    BuildingType,
    DecorationType,
    FeedType,
)
from ..models.animal import Animal
from ..models.building import Building
from ..models.decoration import Decoration
from ..models.farm import Farm
from ..utils.logger import get_logger

logger = get_logger(__name__)


def purchase_animal(
    farm: Farm, animal_type: AnimalType, building_id: str
) -> Animal | None:
    """
    Purchase an animal and add it to the specified building (model only).

    The caller is responsible for creating the sprite and positioning it.

    Args:
        farm: The current Farm instance.
        animal_type: Type of animal to purchase.
        building_id: ID of the building to house the animal in.

    Returns:
        The new Animal model on success, or None if the purchase failed.
    """
    building = farm.buildings.get(building_id)
    if not building:
        logger.warning(f"Building {building_id} not found")
        return None

    if not building.can_add_animal(animal_type):
        logger.warning(f"Building cannot accept {animal_type.value}")
        return None

    cost = ANIMAL_PURCHASE_PRICES.get(animal_type, 100)
    if not farm.spend_money(cost, f"Purchase {animal_type.value}"):
        logger.warning(f"Cannot afford {animal_type.value}")
        return None

    animal = Animal(type=animal_type, building_id=building_id)
    farm.add_animal(animal)
    building.add_animal(animal.id)

    logger.info(f"Purchased {animal_type.value} for ${cost}")
    return animal


def purchase_building(
    farm: Farm, building_type: BuildingType, position: tuple[int, int]
) -> Building | None:
    """
    Purchase a building (model only).

    The caller is responsible for creating the sprite, marking grid tiles,
    and ending placement mode.

    Args:
        farm: The current Farm instance.
        building_type: Type of building to purchase.
        position: (grid_x, grid_y) tile coordinates.

    Returns:
        The new Building model on success, or None if the purchase failed.
    """
    cost = BUILDING_PURCHASE_COSTS.get(building_type, 500)
    if not farm.spend_money(cost, f"Purchase {building_type.value}"):
        logger.warning(f"Cannot afford {building_type.value}")
        return None

    building = Building(type=building_type, position=position)
    farm.add_building(building)

    logger.info(f"Purchased {building_type.value} at {position}")
    return building


def purchase_decoration(
    farm: Farm, decoration_type: DecorationType, position: tuple[int, int], direction: object
) -> Decoration | None:
    """
    Purchase a decoration (model only).

    The caller is responsible for creating the sprite, marking grid tiles,
    and ending placement mode.

    Args:
        farm: The current Farm instance.
        decoration_type: Type of decoration to purchase.
        position: (grid_x, grid_y) tile coordinates.
        direction: Facing direction (Direction enum value).

    Returns:
        The new Decoration model on success, or None if the purchase failed.
    """
    cost = DECORATION_COSTS.get(decoration_type, 100)
    if not farm.spend_money(cost, f"Purchase {decoration_type.value}"):
        logger.warning(f"Cannot afford {decoration_type.value}")
        return None

    decoration = Decoration(type=decoration_type, position=position, direction=direction)
    farm.add_decoration(decoration)

    logger.info(f"Purchased {decoration_type.value} at {position}")
    return decoration


def purchase_feed(farm: Farm, feed_type: FeedType, bundle_size: int) -> bool:
    """
    Purchase a bundle of feed.

    Args:
        farm: The current Farm instance.
        feed_type: Type of feed to purchase.
        bundle_size: Number of units to purchase.

    Returns:
        True if the purchase was successful.
    """
    return farm.buy_feed(feed_type, bundle_size)
