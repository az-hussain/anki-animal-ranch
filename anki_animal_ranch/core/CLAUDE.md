# core/ — Constants, Events, Time

## constants.py
The ONLY place for game balance numbers. Never hardcode numeric game constants anywhere else.
Key exports:
- `PRODUCT_BASE_PRICES` — base price per `ProductType`
- `PRODUCT_QUALITY_MULTIPLIERS` — multiplier per `ProductQuality`
- `SEASON_PRODUCTION_MODIFIERS` / `SEASON_PRICE_MODIFIERS` — defined but NOT yet applied (future feature)
- `HEALTH_QUALITY_THRESHOLDS` — canonical thresholds for health-to-quality mapping. The old alias `QUALITY_CARE_THRESHOLDS` was deleted; use `HEALTH_QUALITY_THRESHOLDS`.
- All enums live here: `AnimalType`, `BuildingType`, `ProductType`, `ProductQuality`, `Season`, `AnimalState`

## event_bus.py — Pub/Sub
`EventBus` is a singleton. All inter-module communication goes through it.

```python
from anki_animal_ranch.core.event_bus import event_bus, Events

# Subscribe
event_bus.subscribe(Events.ANIMAL_PRODUCED, self._on_produced)

# Publish
event_bus.publish(Events.ANIMAL_PRODUCED, animal=animal, product=product)
```

### Adding a new event type
1. Add the name to the `Events` enum in `event_bus.py`.
2. Call `event_bus.publish(Events.YOUR_EVENT, **kwargs)` at the source.
3. Subscribe with `event_bus.subscribe(Events.YOUR_EVENT, handler)` at the consumer.

## time_system.py — TimeSystem
Converts `total_cards_answered` (an integer on `farm.statistics`) into `FarmTime` (year, season, day, hour, minute).

**Never serialize TimeSystem.** On every load, reconstruct it:
```python
time_system = TimeSystem(farm)  # reads farm.statistics.total_cards_answered
```

Published events (in order of coarseness):
- `Events.TIME_ADVANCED` — every card (every minute)
- `Events.HOUR_CHANGED` — every 60 cards
- `Events.DAY_CHANGED` — every 1440 cards
- `Events.SEASON_CHANGED` — on season boundary

## changelog.py
Static string containing version history. No logic.
