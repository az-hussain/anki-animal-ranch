# systems/ — Simulation Engine

## growth_system.py
`GrowthSystem` is the simulation engine. It is called every game tick (every time cards are answered) with the number of game-hours that have elapsed.

### What it does per tick
1. Ages each animal (`animal.age_minutes += hours_passed * 60`).
2. Checks maturity thresholds and publishes `Events.ANIMAL_MATURED`.
3. Calls `_consume_daily_feed()` when a game day rolls over.
4. Advances `animal.production_timer_minutes`; when threshold is met, adds product to `farm.products` and publishes `Events.ANIMAL_PRODUCED`.

### Feed System
`GrowthSystem._consume_daily_feed()` handles daily feed consumption per animal. Feed shortfalls reduce `animal.health`. Feed inventory keys follow the same format as products: `"{feed_type}"` in `farm.products`.

### Adding Seasonal Production Modifiers
A TODO is marked in `GrowthSystem.update()` at the production calculation step. When ready:
1. Read the current season from `time_system.current_time.season`.
2. Look up `SEASON_PRODUCTION_MODIFIERS[season]` from `core/constants.py`.
3. Multiply the production rate before comparing against the timer threshold.

Do NOT apply the modifier anywhere else — keep it isolated to that one location.

### Animal Visual Wandering
`animal_ai.py` was deleted — it was dead code. `AnimalSprite` in `rendering/sprite.py` handles its own visual wandering animation independently of the simulation.

## Entry Point
`GrowthSystem` is instantiated and owned by `MainWindow`. It is called from `MainWindow.on_card_answered()` after `TimeSystem` advances the clock.
