"""
Game constants and configuration.

All magic numbers and configuration values should be defined here.
This makes balancing and tweaking the game much easier.
"""

from enum import Enum, auto
from typing import Final

# =============================================================================
# VERSION — derived from changelog.py (first key = current version)
# =============================================================================

from .changelog import CHANGELOG
VERSION: Final[str] = next(iter(CHANGELOG))

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================

# Window dimensions
DEFAULT_WINDOW_WIDTH: Final[int] = 1280
DEFAULT_WINDOW_HEIGHT: Final[int] = 720
MIN_WINDOW_WIDTH: Final[int] = 800
MIN_WINDOW_HEIGHT: Final[int] = 600

# Tile dimensions (isometric diamond)
TILE_WIDTH: Final[int] = 64  # Width of isometric tile
TILE_HEIGHT: Final[int] = 32  # Height of isometric tile (typically half of width)

# Sprite dimensions
SPRITE_SIZE: Final[int] = 32  # Base sprite size for animals/characters
BUILDING_TILE_SIZE: Final[int] = 64  # Base building sprite size

# Camera
DEFAULT_ZOOM: Final[float] = 1.0
MIN_ZOOM: Final[float] = 0.5
MAX_ZOOM: Final[float] = 2.0
ZOOM_STEP: Final[float] = 0.1
CAMERA_PAN_SPEED: Final[int] = 10  # Pixels per frame when edge scrolling

# Animation
TARGET_FPS: Final[int] = 60
FRAME_TIME_MS: Final[int] = 1000 // TARGET_FPS
ANIMATION_SPEED: Final[float] = 1.0  # Multiplier for animation playback

# =============================================================================
# FARM GRID
# =============================================================================

# Initial farm size (in zones)
INITIAL_FARM_ZONES: Final[int] = 1
MAX_FARM_ZONES: Final[int] = 12

# Zone size (in tiles)
ZONE_WIDTH: Final[int] = 10
ZONE_HEIGHT: Final[int] = 10

# =============================================================================
# TIME SYSTEM
# =============================================================================

# Minutes of game time per card answered (1 card = 1 minute)
MINUTES_PER_CARD: Final[int] = 1

# Game time constants
MINUTES_PER_HOUR: Final[int] = 60
HOURS_PER_DAY: Final[int] = 24
DAYS_PER_SEASON: Final[int] = 7
SEASONS_PER_YEAR: Final[int] = 4

# =============================================================================
# ECONOMY
# =============================================================================

# Starting resources
INITIAL_MONEY: Final[int] = 1500

# Zone unlock costs - Tiered pricing with cap
# Zones 2-3: $2,500 | Zones 4-6: $5,000 | Zones 7-9: $10,000 | Zones 10-12: $15,000 (cap)
ZONE_UNLOCK_COSTS: Final[list[int]] = [
    0,      # Zone 1 (free - starting zone)
    2500,   # Zone 2  (Tier 1)
    2500,   # Zone 3  (Tier 1)
    5000,   # Zone 4  (Tier 2)
    5000,   # Zone 5  (Tier 2)
    5000,   # Zone 6  (Tier 2)
    10000,  # Zone 7  (Tier 3)
    10000,  # Zone 8  (Tier 3)
    10000,  # Zone 9  (Tier 3)
    15000,  # Zone 10 (Tier 4 - cap)
    15000,  # Zone 11 (Tier 4 - cap)
    15000,  # Zone 12 (Tier 4 - cap)
]

# =============================================================================
# FEED SYSTEM
# =============================================================================

class FeedType(Enum):
    """Types of feed for different animals."""
    CHICKEN_FEED = "chicken_feed"
    PIG_FEED = "pig_feed"
    COW_FEED = "cow_feed"


# Feed prices (per 100 units)
FEED_PRICES: Final[dict[FeedType, int]] = {
    FeedType.CHICKEN_FEED: 50,   # $0.50 per unit
    FeedType.PIG_FEED: 75,       # $0.75 per unit
    FeedType.COW_FEED: 100,      # $1.00 per unit
}

# Feed consumption per animal per game day
FEED_CONSUMPTION_PER_DAY: Final[dict[FeedType, int]] = {
    FeedType.CHICKEN_FEED: 1,    # 1 unit per chicken per day
    FeedType.PIG_FEED: 2,        # 2 units per pig per day
    FeedType.COW_FEED: 3,        # 3 units per cow per day
}

# Feed bundle sizes available for purchase
FEED_BUNDLE_SIZES: Final[list[int]] = [100, 250, 500]

# Health decay rate per hour when unfed (hunger = 0)
HEALTH_DECAY_RATE_UNFED: Final[float] = 0.01  # 1% per hour when starving

# Health recovery rate per hour when fed (hunger > 0.5)
HEALTH_RECOVERY_RATE_FED: Final[float] = 0.005  # 0.5% per hour when well-fed


# =============================================================================
# ANIMALS
# =============================================================================

class AnimalType(Enum):
    """Types of animals available in the game."""
    CHICKEN = "chicken"
    PIG = "pig"
    COW = "cow"


class GrowthStage(Enum):
    """Growth stages for animals."""
    BABY = "baby"
    TEEN = "teen"
    ADULT = "adult"


# Maturity thresholds (0.0 to 1.0)
GROWTH_STAGE_THRESHOLDS: Final[dict[GrowthStage, float]] = {
    GrowthStage.BABY: 0.0,
    GrowthStage.TEEN: 0.33,
    GrowthStage.ADULT: 0.66,
}

# Base prices for buying animals
ANIMAL_PURCHASE_PRICES: Final[dict[AnimalType, int]] = {
    AnimalType.CHICKEN: 80,
    AnimalType.PIG: 200,
    AnimalType.COW: 400,
}

# Base sale prices at full maturity and health
ANIMAL_BASE_SALE_PRICES: Final[dict[AnimalType, int]] = {
    AnimalType.CHICKEN: 120,
    AnimalType.PIG: 350,
    AnimalType.COW: 700,
}

# Growth rate (maturity gained per game hour with perfect care)
# Balanced so: Chicken ~1000 cards, Pig ~1500 cards, Cow ~2100 cards to adult
ANIMAL_GROWTH_RATES: Final[dict[AnimalType, float]] = {
    AnimalType.CHICKEN: 0.040,  # ~16.5 hours to adult (~1000 cards)
    AnimalType.PIG: 0.027,      # ~24.4 hours to adult (~1500 cards)
    AnimalType.COW: 0.019,      # ~34.7 hours to adult (~2100 cards)
}

# Hours between production cycles for mature animals
ANIMAL_PRODUCTION_INTERVALS: Final[dict[AnimalType, int]] = {
    AnimalType.CHICKEN: 4,   # Produces every 4 hours
    AnimalType.PIG: 8,       # Produces every 8 hours
    AnimalType.COW: 6,       # Produces every 6 hours
}

# Animal size categories (affects building capacity calculations)
class AnimalSize(Enum):
    """Size categories for animals."""
    SMALL = 1   # Chickens
    MEDIUM = 2  # Pigs
    LARGE = 3   # Cows


ANIMAL_SIZES: Final[dict[AnimalType, AnimalSize]] = {
    AnimalType.CHICKEN: AnimalSize.SMALL,
    AnimalType.PIG: AnimalSize.MEDIUM,
    AnimalType.COW: AnimalSize.LARGE,
}

# Map animals to their feed types (populated after both enums exist)
ANIMAL_FEED_MAP: Final[dict[AnimalType, FeedType]] = {
    AnimalType.CHICKEN: FeedType.CHICKEN_FEED,
    AnimalType.PIG: FeedType.PIG_FEED,
    AnimalType.COW: FeedType.COW_FEED,
}

# =============================================================================
# PRODUCTS
# =============================================================================

class ProductType(Enum):
    """Types of products animals can produce."""
    EGG = "egg"
    TRUFFLE = "truffle"
    MILK = "milk"


class ProductQuality(Enum):
    """Quality tiers for products."""
    BASIC = "basic"
    GOOD = "good"
    PREMIUM = "premium"
    ARTISAN = "artisan"


# Which animal produces which product
ANIMAL_PRODUCTS: Final[dict[AnimalType, ProductType]] = {
    AnimalType.CHICKEN: ProductType.EGG,
    AnimalType.PIG: ProductType.TRUFFLE,
    AnimalType.COW: ProductType.MILK,
}

# Base product prices (Basic quality)
# Balanced for progression: Chicken < Pig < Cow profit per card
PRODUCT_BASE_PRICES: Final[dict[ProductType, int]] = {
    ProductType.EGG: 10,
    ProductType.TRUFFLE: 40,
    ProductType.MILK: 35,
}

# Freshness decay rates per game hour (1.0 / rate = hours to fully spoil)
PRODUCT_FRESHNESS_DECAY_RATES: Final[dict[str, float]] = {
    "egg": 0.02,      # ~50 hours to spoil
    "milk": 0.04,     # ~25 hours to spoil
    "truffle": 0.01,  # ~100 hours to spoil
}

# Quality multipliers
PRODUCT_QUALITY_MULTIPLIERS: Final[dict[ProductQuality, float]] = {
    ProductQuality.BASIC: 1.0,
    ProductQuality.GOOD: 1.3,
    ProductQuality.PREMIUM: 1.6,
    ProductQuality.ARTISAN: 2.0,
}

# Health thresholds for product quality (higher health = better quality)
HEALTH_QUALITY_THRESHOLDS: Final[dict[ProductQuality, float]] = {
    ProductQuality.ARTISAN: 0.95,  # 95%+ health → ⭐⭐⭐⭐
    ProductQuality.PREMIUM: 0.80,  # 80%+ health → ⭐⭐⭐
    ProductQuality.GOOD: 0.60,     # 60%+ health → ⭐⭐
    ProductQuality.BASIC: 0.0,     # Below 60%   → ⭐
}

# =============================================================================
# BUILDINGS
# =============================================================================

class BuildingType(Enum):
    """Types of buildings available."""
    COOP = "coop"           # For chickens
    PIGSTY = "pigsty"       # For pigs
    BARN = "barn"           # For cows
    # Future stubs — no sprites, no shop entries, not yet usable:
    FARMHOUSE = "farmhouse"        # Player home (future)
    SILO = "silo"                  # Feed storage (future)
    MARKET_STALL = "market_stall"  # On-site selling (future)
    TRUCK_DEPOT = "truck_depot"    # Vehicle storage (future)


# Maximum upgrade level for buildings
MAX_BUILDING_LEVEL: Final[int] = 4

# Building capacities by level (in "animal units" - small=1, medium=2, large=3)
BUILDING_CAPACITIES: Final[dict[BuildingType, list[int]]] = {
    BuildingType.COOP: [4, 7, 11, 16],        # Levels 1-4 (+3/+4/+5 per upgrade)
    BuildingType.PIGSTY: [3, 5, 8, 12],       # Levels 1-4 (+2/+3/+4 per upgrade)
    BuildingType.BARN: [2, 4, 6, 9],          # Levels 1-4 (+2/+2/+3 per upgrade)
}

# Building purchase costs
BUILDING_PURCHASE_COSTS: Final[dict[BuildingType, int]] = {
    BuildingType.COOP: 500,
    BuildingType.PIGSTY: 1000,
    BuildingType.BARN: 2000,
    BuildingType.SILO: 1500,
    BuildingType.MARKET_STALL: 800,
    BuildingType.TRUCK_DEPOT: 3000,
}

# Building upgrade costs (multiplied by current level)
BUILDING_UPGRADE_COSTS: Final[dict[BuildingType, int]] = {
    BuildingType.COOP: 400,       # Cheaper than building new ($500)
    BuildingType.PIGSTY: 800,     # Cheaper than building new ($1000)  
    BuildingType.BARN: 1500,      # Cheaper than building new ($2000)
}

# Building footprints (width x height in tiles)
BUILDING_FOOTPRINTS: Final[dict[BuildingType, tuple[int, int]]] = {
    BuildingType.COOP: (2, 2),
    BuildingType.PIGSTY: (3, 2),
    BuildingType.BARN: (3, 3),
    BuildingType.FARMHOUSE: (3, 3),
    BuildingType.SILO: (2, 2),
    BuildingType.MARKET_STALL: (2, 2),
    BuildingType.TRUCK_DEPOT: (4, 3),
}

# Production bonus per building level (1.0 = no bonus)
BUILDING_PRODUCTION_BONUSES: Final[list[float]] = [1.0, 1.15, 1.30, 1.50]


# =============================================================================
# DECORATIONS
# =============================================================================

class DecorationType(Enum):
    """Types of decorative items available."""
    # Nature & Plants
    HAY_BALE = "hay_bale"
    FLOWER_BED = "flower_bed"
    TREE = "tree"
    SCARECROW = "scarecrow"
    PUMPKIN_PATCH = "pumpkin_patch"
    
    # Farm Structures
    WINDMILL = "windmill"
    WATER_WELL = "water_well"
    DECORATIVE_SILO = "decorative_silo"
    WOODEN_CART = "wooden_cart"
    
    # Water Features
    POND = "pond"
    FOUNTAIN = "fountain"
    WATER_TROUGH = "water_trough"
    
    # Outdoor Living
    BENCH = "bench"
    PICNIC_TABLE = "picnic_table"
    LAMP_POST = "lamp_post"
    
    # Fun Extras
    GARDEN_GNOME = "garden_gnome"
    MAILBOX = "mailbox"
    SIGNPOST = "signpost"


class Direction(Enum):
    """Cardinal directions for decoration rotation."""
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270


# Decoration costs
DECORATION_COSTS: Final[dict[DecorationType, int]] = {
    # Nature & Plants
    DecorationType.HAY_BALE: 50,
    DecorationType.FLOWER_BED: 75,
    DecorationType.TREE: 150,
    DecorationType.SCARECROW: 100,
    DecorationType.PUMPKIN_PATCH: 125,
    # Farm Structures
    DecorationType.WINDMILL: 500,
    DecorationType.WATER_WELL: 200,
    DecorationType.DECORATIVE_SILO: 300,
    DecorationType.WOODEN_CART: 175,
    # Water Features
    DecorationType.POND: 400,
    DecorationType.FOUNTAIN: 350,
    DecorationType.WATER_TROUGH: 100,
    # Outdoor Living
    DecorationType.BENCH: 75,
    DecorationType.PICNIC_TABLE: 150,
    DecorationType.LAMP_POST: 125,
    # Fun Extras
    DecorationType.GARDEN_GNOME: 50,
    DecorationType.MAILBOX: 50,
    DecorationType.SIGNPOST: 75,
}

# Decoration footprints (width x height in tiles)
DECORATION_FOOTPRINTS: Final[dict[DecorationType, tuple[int, int]]] = {
    # Nature & Plants
    DecorationType.HAY_BALE: (1, 1),
    DecorationType.FLOWER_BED: (1, 1),
    DecorationType.TREE: (1, 1),
    DecorationType.SCARECROW: (1, 1),
    DecorationType.PUMPKIN_PATCH: (2, 1),
    # Farm Structures
    DecorationType.WINDMILL: (2, 2),
    DecorationType.WATER_WELL: (1, 1),
    DecorationType.DECORATIVE_SILO: (1, 1),
    DecorationType.WOODEN_CART: (2, 1),
    # Water Features
    DecorationType.POND: (2, 2),
    DecorationType.FOUNTAIN: (1, 1),
    DecorationType.WATER_TROUGH: (1, 1),
    # Outdoor Living
    DecorationType.BENCH: (1, 1),
    DecorationType.PICNIC_TABLE: (2, 1),
    DecorationType.LAMP_POST: (1, 1),
    # Fun Extras
    DecorationType.GARDEN_GNOME: (1, 1),
    DecorationType.MAILBOX: (1, 1),
    DecorationType.SIGNPOST: (1, 1),
}

# Building display info (name, emoji, description, animal_type)
# canonical source of truth for all UI that shows building metadata
BUILDING_DISPLAY_INFO: Final[dict[str, dict]] = {
    "coop": {
        "name": "Chicken Coop",
        "emoji": "🐔",
        "description": "Houses chickens. They produce eggs!",
        "animal_type": "chicken",
    },
    "pigsty": {
        "name": "Pig Sty",
        "emoji": "🐷",
        "description": "Houses pigs. They find truffles!",
        "animal_type": "pig",
    },
    "barn": {
        "name": "Cow Barn",
        "emoji": "🐄",
        "description": "Houses cows. They produce milk!",
        "animal_type": "cow",
    },
}

# Decoration display info (name, emoji, can_rotate)
DECORATION_INFO: Final[dict[DecorationType, dict]] = {
    # Nature & Plants
    DecorationType.HAY_BALE: {"name": "Hay Bale", "emoji": "🟨", "can_rotate": True},
    DecorationType.FLOWER_BED: {"name": "Flower Bed", "emoji": "🌸", "can_rotate": True},
    DecorationType.TREE: {"name": "Tree", "emoji": "🌳", "can_rotate": False},
    DecorationType.SCARECROW: {"name": "Scarecrow", "emoji": "🎃", "can_rotate": True},
    DecorationType.PUMPKIN_PATCH: {"name": "Pumpkin Patch", "emoji": "🎃", "can_rotate": True},
    # Farm Structures
    DecorationType.WINDMILL: {"name": "Windmill", "emoji": "🏗️", "can_rotate": True},
    DecorationType.WATER_WELL: {"name": "Water Well", "emoji": "🪣", "can_rotate": False},
    DecorationType.DECORATIVE_SILO: {"name": "Silo", "emoji": "🏛️", "can_rotate": False},
    DecorationType.WOODEN_CART: {"name": "Wooden Cart", "emoji": "🛒", "can_rotate": True},
    # Water Features
    DecorationType.POND: {"name": "Pond", "emoji": "💧", "can_rotate": False},
    DecorationType.FOUNTAIN: {"name": "Fountain", "emoji": "⛲", "can_rotate": False},
    DecorationType.WATER_TROUGH: {"name": "Water Trough", "emoji": "🪣", "can_rotate": True},
    # Outdoor Living
    DecorationType.BENCH: {"name": "Bench", "emoji": "🪑", "can_rotate": True},
    DecorationType.PICNIC_TABLE: {"name": "Picnic Table", "emoji": "🪵", "can_rotate": True},
    DecorationType.LAMP_POST: {"name": "Lamp Post", "emoji": "🏮", "can_rotate": False},
    # Fun Extras
    DecorationType.GARDEN_GNOME: {"name": "Garden Gnome", "emoji": "🧙", "can_rotate": True},
    DecorationType.MAILBOX: {"name": "Mailbox", "emoji": "📬", "can_rotate": True},
    DecorationType.SIGNPOST: {"name": "Signpost", "emoji": "🪧", "can_rotate": True},
}


# =============================================================================
# SEASONS
# =============================================================================

class Season(Enum):
    """Seasons of the year."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"


# Season order for cycling
SEASON_ORDER: Final[list[Season]] = [
    Season.SPRING,
    Season.SUMMER,
    Season.FALL,
    Season.WINTER,
]

# Seasonal modifiers — DEFINED but NOT YET APPLIED in game logic.
# TODO: Apply SEASON_PRODUCTION_MODIFIERS in systems/growth_system.py _produce()
# TODO: Apply SEASON_PRICE_MODIFIERS in services/pricing.py product_unit_price()
SEASON_PRODUCTION_MODIFIERS: Final[dict[Season, float]] = {
    Season.SPRING: 1.1,   # Breeding season bonus
    Season.SUMMER: 1.0,
    Season.FALL: 1.15,    # Harvest bonus
    Season.WINTER: 0.8,   # Cold penalty
}

SEASON_PRICE_MODIFIERS: Final[dict[Season, dict[ProductType, float]]] = {
    Season.SPRING: {ProductType.EGG: 1.2, ProductType.TRUFFLE: 1.0, ProductType.MILK: 1.0},
    Season.SUMMER: {ProductType.EGG: 1.0, ProductType.TRUFFLE: 1.0, ProductType.MILK: 0.9},
    Season.FALL: {ProductType.EGG: 1.0, ProductType.TRUFFLE: 1.3, ProductType.MILK: 1.0},
    Season.WINTER: {ProductType.EGG: 1.3, ProductType.TRUFFLE: 0.8, ProductType.MILK: 1.2},
}

# =============================================================================
# EVENTS (for event bus)
# =============================================================================

# Event names - using strings for type safety and debugging
class Events:
    """Event name constants for the event bus."""
    # Study events
    CARD_ANSWERED = "card_answered"
    STUDY_SESSION_START = "study_session_start"
    STUDY_SESSION_END = "study_session_end"
    
    # Time events
    TIME_ADVANCED = "time_advanced"
    HOUR_CHANGED = "hour_changed"
    DAY_CHANGED = "day_changed"
    SEASON_CHANGED = "season_changed"
    
    # Animal events
    ANIMAL_PURCHASED = "animal_purchased"
    ANIMAL_MATURED = "animal_matured"
    ANIMAL_PRODUCED = "animal_produced"
    ANIMAL_SICK = "animal_sick"
    ANIMAL_HEALED = "animal_healed"
    ANIMAL_SOLD = "animal_sold"
    
    # Building events
    BUILDING_PLACED = "building_placed"
    BUILDING_UPGRADED = "building_upgraded"
    BUILDING_DEMOLISHED = "building_demolished"
    
    # Economy events
    MONEY_CHANGED = "money_changed"
    PRODUCT_SOLD = "product_sold"
    TRANSACTION_COMPLETED = "transaction_completed"
    
    # UI events
    BUILDING_SELECTED = "building_selected"
    ANIMAL_SELECTED = "animal_selected"
    PANEL_OPENED = "panel_opened"
    PANEL_CLOSED = "panel_closed"
    
    # Save/Load events
    GAME_SAVED = "game_saved"
    GAME_LOADED = "game_loaded"
    
    # Social events
    FRIEND_VISIT_STARTED = "friend_visit_started"
    FRIEND_VISIT_ENDED = "friend_visit_ended"
