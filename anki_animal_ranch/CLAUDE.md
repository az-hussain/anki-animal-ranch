# Anki Animal Ranch — Master Reference

## What This Is
An Anki addon (`__init__.py` registers the hooks) that embeds a PyQt6 isometric farm game. Cards answered in Anki drive game time. The game can also run standalone via `python run_game.py`.

## The Central Invariant
**1 card answered = 1 game minute.**
`TimeSystem` derives all time from `farm.statistics.total_cards_answered`. `TimeSystem` is NEVER serialized — it is always reconstructed from that integer on load. Do not store time state anywhere else.

## Critical Invariants
- **Time**: `TimeSystem` reconstructed from `total_cards_answered` on every load. Never save it.
- **Inventory keys**: `"{ProductType.value}_{ProductQuality.value}"` (e.g. `"egg_premium"`). Use `parse_inventory()` in `models/player.py` to read them — never parse keys by hand.
- **Pricing**: `PRODUCT_BASE_PRICES` and `PRODUCT_QUALITY_MULTIPLIERS` in `core/constants.py` are the only source of truth. Always use `services/pricing.py` — never compute prices inline.
- **Balance numbers**: All game balance lives in `core/constants.py`. Never hardcode numeric constants in other files.
- **Colors**: All colors live in `ui/theme.py`. Never hardcode hex values in UI files.
- **Seasonal modifiers**: `SEASON_PRODUCTION_MODIFIERS` and `SEASON_PRICE_MODIFIERS` are defined in `constants.py` but NOT yet applied anywhere (future feature).
- **Building stubs**: `BuildingType.FARMHOUSE`, `SILO`, `MARKET_STALL`, `TRUCK_DEPOT` have no sprites and are not in the shop — they are future stubs.

## Folder Map
```
anki_animal_ranch/
├── __init__.py            Anki hooks, global window singleton, entry point
├── core/                  Enums, constants, event bus, time system, changelog
├── data/                  Save/load (atomic JSON + backup + migration), account/friends files
├── models/                Pure data: Farm, Animal, Building, Decoration, Product, Player
├── network/               Supabase REST calls via urllib
├── rendering/             QGraphicsView scene, sprites, tile grid, camera
├── services/              Business logic: pricing, market transactions, shop purchases
├── systems/               Simulation engine: GrowthSystem (aging, feed, production)
├── ui/                    MainWindow coordinator, theme, SpriteManager, SidePanel, dialogs, widgets
└── utils/                 Logger, isometric math utilities
```

## Card-to-Game Event Flow
```
Anki reviewer_did_answer_card hook
  → __init__.on_card_answered(reviewer, card, ease)
    → MainWindow.on_card_answered(ease)
      → TimeSystem.on_card_answered(ease)      # increments total_cards_answered by 1
        → publishes TIME_ADVANCED, HOUR_CHANGED, DAY_CHANGED, SEASON_CHANGED
          → GrowthSystem.update(hours_passed)  # ages animals, checks production
            → publishes ANIMAL_PRODUCED, ANIMAL_MATURED
              → MainWindow._update_ui()
                → side_panel.refresh()
```

## Known Incomplete Features
- `SEASON_PRODUCTION_MODIFIERS` / `SEASON_PRICE_MODIFIERS` defined in `constants.py` but not applied; TODOs exist in `growth_system.py` and `pricing.py`.
- `BuildingType.FARMHOUSE`, `SILO`, `MARKET_STALL`, `TRUCK_DEPOT` — no sprites, not purchasable, no logic.
- Cloud sync is fire-and-forget; no retry logic.

## Development Commands
```bash
# Run standalone (no Anki required)
python run_game.py

# Type check
python -m mypy anki_animal_ranch
```

## Publishing a Release

`core/changelog.py` is the **single source of truth** for the version. The first key in `CHANGELOG` is always the current version — `constants.py` derives `VERSION` from it automatically.

### Step 1 — Write the changelog entry
In `core/changelog.py`, add the new version at the **top** of the `CHANGELOG` dict:
```python
CHANGELOG: Final[dict[str, list[str]]] = {
    "0.4.0": [
        "What changed in this release",
        "Another change",
    ],
    "0.3.0": [ ... ],
```
This one edit sets the version everywhere — `VERSION` in `constants.py` picks it up automatically.

### Step 2 — Sync and build
```bash
./scripts/bump_version.sh
```
Reads the new version from the changelog, updates `manifest.json` and `README.md`, then runs `build_addon.sh` to produce `anki_animal_ranch_v0.4.0.ankiaddon`.

### Step 3 — Commit and tag
```bash
git add anki_animal_ranch/core/changelog.py anki_animal_ranch/manifest.json README.md
git commit -m "v0.4.0"
git tag v0.4.0
```

### Step 4 — Upload to AnkiWeb
Go to `https://ankiweb.net/shared/upload` and upload the `.ankiaddon` file to the existing addon page.
