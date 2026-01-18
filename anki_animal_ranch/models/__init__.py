"""
Data models for Anki Animal Ranch.

This package contains pure Python data classes that represent
game entities. These models have no Qt dependencies and can
be serialized/deserialized for save games.

Modules:
- animal: Animal entities and lifecycle
- building: Farm buildings
- decoration: Decorative items
- player: Player inventory
- product: Animal products
- farm: Main farm container
"""

from .animal import Animal
from .building import Building
from .decoration import Decoration
from .product import Product
from .player import Player
from .farm import Farm

__all__ = [
    "Animal",
    "Building",
    "Decoration",
    "Product",
    "Player",
    "Farm",
]
