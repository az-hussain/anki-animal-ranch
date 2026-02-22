# services/ — Business Operations

## Rules
- Services are the single source of truth for all user-triggered business operations.
- Services take `Farm` (and optionally `TimeSystem`) as arguments and return result objects.
- No PyQt6, no rendering, no side effects beyond `Farm` mutation and `event_bus.publish()`.
- Never compute prices inline anywhere in the codebase — always use `services/pricing.py`.

## pricing.py
All price calculations. Key functions:
```python
from anki_animal_ranch.services.pricing import product_unit_price, inventory_value

price = product_unit_price(product_type, quality)           # unit price
total = inventory_value(farm.products)                      # total inventory value
```
Price is derived solely from `PRODUCT_BASE_PRICES` and `PRODUCT_QUALITY_MULTIPLIERS` in `core/constants.py`.

A TODO in `pricing.py` marks where `SEASON_PRICE_MODIFIERS` should be applied when seasonal pricing is enabled.

## market_service.py
All sell transactions:
```python
from anki_animal_ranch.services.market_service import sell_product, sell_all_products, sell_animal

result = sell_product(farm, product_type, quality, quantity)
result = sell_all_products(farm)
result = sell_animal(farm, animal)
```
These functions mutate `farm.products`, `farm.animals`, and `farm.money`, then publish relevant events.

## shop_service.py
All buy transactions:
```python
from anki_animal_ranch.services.shop_service import (
    purchase_animal, purchase_building, purchase_decoration, purchase_feed
)

result = purchase_animal(farm, animal_type)
result = purchase_building(farm, building_type)
result = purchase_decoration(farm, decoration_type)
result = purchase_feed(farm, feed_type, quantity)
```
These functions check `farm.money`, deduct costs, add the purchased item to `farm`, and publish events.

## Adding a New Service Function
1. Add the function to the appropriate file (`market_service.py` for sells, `shop_service.py` for buys).
2. Use `product_unit_price()` from `pricing.py` for any price calculation.
3. Read all balance numbers from `core/constants.py`.
4. Return a result dataclass or named tuple — never raise exceptions for expected failures (insufficient funds, etc.).
