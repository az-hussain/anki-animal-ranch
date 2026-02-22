# models/ — Pure Data Layer

## Rules
- No UI imports, no rendering imports, no services imports.
- Models are pure data + simple derived properties. All business operations live in `services/`.
- No PyQt6 anywhere in this package.

## farm.py — Aggregate Root
`Farm` is the single aggregate root. All game state is accessed through it:
- `farm.animals: list[Animal]`
- `farm.buildings: list[Building]`
- `farm.decorations: list[Decoration]`
- `farm.products: dict[str, int]` — inventory (see format below)
- `farm.money: float`
- `farm.statistics.total_cards_answered: int` — the canonical time source

Never hold references to internal lists across operations — always re-read from `farm`.

## Inventory Format
Keys are `"{ProductType.value}_{ProductQuality.value}"` — e.g. `"egg_premium"`, `"milk_standard"`.

**Use `parse_inventory()` in `player.py` to read inventory.** Never split or parse keys by hand.

```python
from anki_animal_ranch.models.player import parse_inventory

items = parse_inventory(farm.products)
# returns list of (ProductType, ProductQuality, count) tuples
```

## animal.py — Animal
Key fields: `animal_type`, `age_minutes`, `health`, `hunger`, `state`, `production_timer_minutes`.

- `animal.health` is the authoritative health value. The old `care_quality` property was removed — do not reference it.
- Maturity, growth, and production timing are driven by `GrowthSystem`, not by the model itself.

## building.py — Building
Tracks capacity, level, and which animals are housed. Housing assignment logic belongs in `shop_service.py`.

## decoration.py — Decoration
Holds position, rotation, and footprint data. No game logic.

## product.py — Product
`Product.freshness` exists as a field but does NOT affect sale prices.
Sale price is computed solely from inventory counts via `services/pricing.py`.

## player.py — Player / Inventory Helpers
- `parse_inventory(products: dict[str, int])` — canonical inventory parser; always use this.
- Other helpers for reading and mutating the inventory dict safely.
