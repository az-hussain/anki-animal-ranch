# rendering/ — Isometric Scene

## Coordinate Systems
Three systems are in use. Never mix them without converting:
| System | Type | Description |
|--------|------|-------------|
| World | `float` tile units | Logical grid position of objects |
| Screen | `float` pixels | Qt scene/viewport pixel coordinates |
| Grid | `int` tile index | Discrete tile address for housing/placement |

`utils/math_utils.py` is THE only location for conversion functions. All rendering code imports from there — never duplicate conversion math inline.

## isometric_view.py — IsometricView
`QGraphicsView` subclass that owns the `QGraphicsScene`. Handles:
- Click detection and hit-testing against sprites.
- Delegating placement and selection events to `MainWindow` via signals.
- Scene coordinate → world coordinate conversion via `math_utils`.

## sprite.py — Sprite System
Base class `Sprite` plus all subtypes: `AnimalSprite`, `PenSprite`, `DecorationSprite`, `TileSprite`, etc.

`rendering/` only defines sprite *classes*. Lifecycle management (creating, moving, removing sprites in response to game events) lives in `ui/sprite_manager.py` — `SpriteManager` owns the sprite dicts and provides the API that `MainWindow` calls.

### Z-Ordering
`SpriteLayer` enum defines Z-order. Always set `self._layer` on new sprites — do not set `zValue()` directly.

### Animation
Frame-based with per-frame `duration_ms`. Animation is NOT tied to FPS or a Qt timer — it advances on explicit `update()` calls. Each frame specifies its own duration.

### Animal Wandering
`AnimalSprite` manages its own visual wandering. `animal_ai.py` was deleted (dead code) — there is no separate AI system.

## tile_grid.py — TileGrid
- Manages terrain tile sprites and zone locking.
- `TileSprite._get_seasonal_tile_config()` — returns the sprite config for the current season. Edit here to change seasonal tile appearances.

## camera.py — Camera
Manages pan and zoom via a `QTransform`. Applied to the `QGraphicsView`. Pan and zoom limits are enforced here.
