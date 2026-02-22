# ui/ — User Interface Layer

## theme.py
ALL colors come from `theme.py`. Never hardcode hex values in any UI file.
```python
from anki_animal_ranch.ui.theme import COLOR_BG_DARK, COLOR_PRIMARY, primary_button_style
```
Colors are module-level constants (`COLOR_*`). Button/label styles are helper functions (`primary_button_style()`, etc.).

## placement_state.py
`PlacementState` and `VisitState` are dataclasses that hold all mode flags for the UI.
- `PlacementState`: tracks whether placement mode is active, what item is being placed, and its pending position.
- `VisitState`: tracks whether the player is visiting a friend's farm.

All mode flags live here — never store mode booleans as ad-hoc attributes on `MainWindow`.

## sprite_manager.py — SpriteManager
Owns and manages all entity sprites (buildings, animals, decorations). `MainWindow` creates one instance and calls its methods instead of managing sprite dicts directly.
```python
sprites.add_building_sprite(building, width, height)
sprites.add_animal_sprite(animal, building_id)
sprites.remove_animal_sprite(animal_id)
sprites.update_animal_growth_stage(animal_id, stage)
sprites.clear_all()
sprites.recreate_from_save(farm)
```

## main_window.py — Coordinator (~1189 lines)
`MainWindow` owns and wires together:
- `Farm` (game state)
- `TimeSystem` (reconstructed from `farm.statistics.total_cards_answered` on load)
- `GrowthSystem` (simulation engine)
- `IsometricView` (rendering)
- `SidePanel` (HUD)
- `PlacementState`, `VisitState` (mode state)

Responsibilities: handles the Anki hook (`on_card_answered`), save/load, signal wiring, and delegating to services. It is the coordinator — business logic belongs in `services/`, not here.

## panels/side_panel.py — SidePanel
The HUD panel widget. Update it by calling:
```python
side_panel.refresh(farm, time_system)       # update all labels and counters
side_panel.set_placement_mode(active, text) # switch placement banner on/off
side_panel.set_visit_mode(active)           # switch visit mode indicator
```
`SidePanel` owns all HUD labels and buttons. Do not read `farm` directly from other UI files — pass it through `refresh()`.

## dialogs/
All dialog classes are purely presentational:
- They read state to display it.
- They call `services/` functions for any mutations.
- They emit PyQt6 signals when the user confirms an action.
- They contain NO business logic.

## widgets/
- `product_row.py` — `ProductRow`: reusable row widget for the market dialog.
- `animal_row.py` — `AnimalRow`: reusable row widget for the animal management dialog.

Both are display-only; they emit signals for user actions and leave mutation to the dialog's signal handler.
