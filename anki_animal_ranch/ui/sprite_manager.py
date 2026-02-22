"""
SpriteManager — owns and manages all entity sprites.

MainWindow delegates all sprite creation, movement, and removal to this class.
It holds the three sprite dicts and exposes a clean API so MainWindow does not
need to know sprite internals.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ..rendering.sprite import AnimalSprite, DecorationSprite, PenSprite

if TYPE_CHECKING:
    from ..core.constants import Direction
    from ..models.animal import Animal
    from ..models.building import Building
    from ..models.decoration import Decoration
    from ..models.farm import Farm
    from ..rendering.isometric_view import IsometricView


class SpriteManager:
    """Manages entity sprites (buildings, animals, decorations) for the isometric view."""

    def __init__(self, iso_view: IsometricView) -> None:
        self._iso_view = iso_view
        self._building_sprites: dict[str, PenSprite] = {}
        self._animal_sprites: dict[str, AnimalSprite] = {}
        self._decoration_sprites: dict[str, DecorationSprite] = {}

    # ------------------------------------------------------------------ #
    # Building sprites
    # ------------------------------------------------------------------ #

    def add_building_sprite(self, building: Building, width: int, height: int) -> PenSprite:
        """Create and register a PenSprite for a building."""
        pen_sprite = PenSprite(
            world_x=float(building.position[0]),
            world_y=float(building.position[1]),
            pen_width=width,
            pen_height=height,
        )
        pen_sprite.building_id = building.id
        self._iso_view.add_sprite(f"building_{building.id}", pen_sprite)
        self._building_sprites[building.id] = pen_sprite
        return pen_sprite

    def move_building_sprite(
        self, building: Building, grid_x: int, grid_y: int, width: int, height: int
    ) -> None:
        """Move a building sprite and update pen bounds for all housed animals."""
        pen_sprite = self._building_sprites.get(building.id)
        if pen_sprite is None:
            return
        pen_sprite.set_world_pos(float(grid_x), float(grid_y))
        for animal_id in building.animals:
            animal_sprite = self._animal_sprites.get(animal_id)
            if animal_sprite:
                animal_sprite.set_pen_bounds(grid_x, grid_y, grid_x + width, grid_y + height)

    def get_building_sprite(self, building_id: str) -> PenSprite | None:
        return self._building_sprites.get(building_id)

    # ------------------------------------------------------------------ #
    # Animal sprites
    # ------------------------------------------------------------------ #

    def add_animal_sprite(
        self,
        animal: Animal,
        building_id: str,
        fallback_pos: tuple[float, float] | None = None,
    ) -> AnimalSprite:
        """Create and register an AnimalSprite, positioned randomly inside its pen."""
        pen_sprite = self._building_sprites.get(building_id)
        if pen_sprite:
            bounds = pen_sprite.get_animal_bounds()
            start_x = random.uniform(bounds[0], bounds[2])
            start_y = random.uniform(bounds[1], bounds[3])
        elif fallback_pos is not None:
            start_x, start_y = fallback_pos
        else:
            start_x, start_y = animal.position

        animal_sprite = AnimalSprite(
            world_x=start_x,
            world_y=start_y,
            animal_type=animal.type.value,
            animal_id=animal.id,
        )
        animal_sprite.growth_stage = animal.growth_stage.value
        if pen_sprite:
            bounds = pen_sprite.get_animal_bounds()
            animal_sprite.set_pen_bounds(bounds[0], bounds[1], bounds[2], bounds[3])

        self._iso_view.add_sprite(f"animal_{animal.id}", animal_sprite)
        self._animal_sprites[animal.id] = animal_sprite
        return animal_sprite

    def remove_animal_sprite(self, animal_id: str) -> None:
        """Remove an animal sprite from the view."""
        if animal_id in self._animal_sprites:
            self._animal_sprites.pop(animal_id)
            self._iso_view.remove_sprite(f"animal_{animal_id}")

    def get_animal_sprite(self, animal_id: str) -> AnimalSprite | None:
        return self._animal_sprites.get(animal_id)

    def update_animal_growth_stage(self, animal_id: str, stage: str) -> None:
        """Update the visual growth stage of an animal sprite."""
        sprite = self._animal_sprites.get(animal_id)
        if sprite:
            sprite.growth_stage = stage

    # ------------------------------------------------------------------ #
    # Decoration sprites
    # ------------------------------------------------------------------ #

    def add_decoration_sprite(
        self, decoration: Decoration, width: int, height: int
    ) -> DecorationSprite:
        """Create and register a DecorationSprite."""
        deco_sprite = DecorationSprite(
            world_x=float(decoration.position[0]),
            world_y=float(decoration.position[1]),
            decoration_type=decoration.type,
            direction=decoration.direction,
            footprint_width=width,
            footprint_height=height,
        )
        deco_sprite.decoration_id = decoration.id
        self._iso_view.add_sprite(f"decoration_{decoration.id}", deco_sprite)
        self._decoration_sprites[decoration.id] = deco_sprite
        return deco_sprite

    def move_decoration_sprite(self, decoration: Decoration, grid_x: int, grid_y: int) -> None:
        """Move a decoration sprite to a new position (direction already set on model)."""
        deco_sprite = self._decoration_sprites.get(decoration.id)
        if deco_sprite:
            deco_sprite.set_world_pos(float(grid_x), float(grid_y))
            deco_sprite.set_direction(decoration.direction)

    def remove_decoration_sprite(self, decoration_id: str) -> None:
        """Remove a decoration sprite from the view."""
        if decoration_id in self._decoration_sprites:
            self._decoration_sprites.pop(decoration_id)
            self._iso_view.remove_sprite(f"decoration_{decoration_id}")

    # ------------------------------------------------------------------ #
    # Bulk operations
    # ------------------------------------------------------------------ #

    def clear_all(self) -> None:
        """Remove all entity sprites from the view and clear the internal dicts."""
        for building_id in list(self._building_sprites):
            self._iso_view.remove_sprite(f"building_{building_id}")
        self._building_sprites.clear()

        for animal_id in list(self._animal_sprites):
            self._iso_view.remove_sprite(f"animal_{animal_id}")
        self._animal_sprites.clear()

        for deco_id in list(self._decoration_sprites):
            self._iso_view.remove_sprite(f"decoration_{deco_id}")
        self._decoration_sprites.clear()

    def recreate_from_save(self, farm: Farm) -> None:
        """
        Recreate all entity sprites from a Farm's saved state.

        Clears existing building/animal/decoration sprites, then recreates them
        and marks the grid tiles as occupied.
        """
        from ..core.constants import BUILDING_FOOTPRINTS

        # Clear existing building and animal sprites
        for sprite_id in list(self._building_sprites):
            self._iso_view.remove_sprite(f"building_{sprite_id}")
        for sprite_id in list(self._animal_sprites):
            self._iso_view.remove_sprite(f"animal_{sprite_id}")
        self._building_sprites.clear()
        self._animal_sprites.clear()

        # Recreate building sprites
        for building_id, building in farm.buildings.items():
            w, h = BUILDING_FOOTPRINTS.get(building.type, (2, 2))
            self.add_building_sprite(building, w, h)
            if self._iso_view.grid:
                self._iso_view.grid.mark_building(
                    building_id, building.position[0], building.position[1], w, h
                )

        # Recreate animal sprites
        for animal in farm.animals.values():
            self.add_animal_sprite(animal, animal.building_id)

        # Clear and recreate decoration sprites
        for sprite_id in list(self._decoration_sprites):
            self._iso_view.remove_sprite(f"decoration_{sprite_id}")
        self._decoration_sprites.clear()

        for decoration_id, decoration in farm.decorations.items():
            w, h = decoration.rotated_footprint
            self.add_decoration_sprite(decoration, w, h)
            if self._iso_view.grid:
                self._iso_view.grid.mark_building(
                    decoration_id, decoration.position[0], decoration.position[1], w, h
                )
