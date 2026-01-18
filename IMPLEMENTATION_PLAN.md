# 🐄 Anki Animal Ranch - Implementation Plan

> **Version:** 0.1.34  
> **Last Updated:** 2026-01-18  
> **Status:** ✅ Phase 2 - Core Economy (100% Complete)

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technical Stack](#technical-stack)
3. [Architecture Overview](#architecture-overview)
4. [Implementation Phases](#implementation-phases)
5. [Detailed Task Breakdown](#detailed-task-breakdown)
6. [Data Models](#data-models)
7. [API Specifications](#api-specifications)
8. [Asset Requirements](#asset-requirements)
9. [Testing Strategy](#testing-strategy)
10. [Progress Tracking](#progress-tracking)

---

## Project Overview

### Vision
An Anki addon that transforms flashcard studying into an immersive isometric farm simulation. Players manage animals, buildings, workers, and a farm economy - all driven by their study activity.

### Core Principles
- **Clean, maintainable code** - Production-ready quality
- **Separation of concerns** - Clear module boundaries
- **Test-driven development** - Comprehensive test coverage
- **Performance-first** - Smooth 60fps rendering
- **Offline-first** - Works without internet, syncs when available

### Target Platform
- Anki Desktop (Windows, macOS, Linux)
- Python 3.9+
- PyQt6

---

## Technical Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **GUI Framework** | PyQt6 | Anki's native toolkit, full-featured |
| **Rendering** | QGraphicsView + QGraphicsScene | Hardware-accelerated, supports transforms |
| **Local Database** | SQLite3 | Lightweight, no dependencies |
| **Cloud Backend** | Supabase | Free tier, real-time, PostgreSQL |
| **Asset Format** | PNG spritesheets | Universal support, good compression |
| **Audio** | QMediaPlayer | Built into Qt |
| **Serialization** | JSON | Human-readable, easy debugging |

---

## Architecture Overview

```
anki_animal_ranch/
├── __init__.py                 # Anki addon entry point
├── manifest.json               # Anki addon manifest
├── config.json                 # Default configuration
│
├── core/                       # Core game systems
│   ├── __init__.py
│   ├── game_engine.py          # Main game loop & state machine
│   ├── time_system.py          # Study-to-game-time conversion
│   ├── event_bus.py            # Pub/sub event system
│   └── constants.py            # Game constants & configuration
│
├── models/                     # Data models (pure Python, no Qt)
│   ├── __init__.py
│   ├── farm.py                 # Farm container & state
│   ├── animal.py               # Animal lifecycle & behavior
│   ├── building.py             # Building types & upgrades
│   ├── worker.py               # Worker types & AI
│   ├── player.py               # Player avatar & inventory
│   ├── product.py              # Products & quality system
│   ├── market.py               # Market & pricing
│   └── vehicle.py              # Transport vehicles
│
├── systems/                    # Game systems (logic)
│   ├── __init__.py
│   ├── growth_system.py        # Animal growth calculations
│   ├── production_system.py    # Product generation
│   ├── health_system.py        # Animal health & disease
│   ├── worker_ai.py            # Worker task assignment
│   ├── economy_system.py       # Money & transactions
│   ├── transport_system.py     # Vehicle & market trips
│   └── social_system.py        # Friends & visits
│
├── rendering/                  # Visual rendering (Qt-dependent)
│   ├── __init__.py
│   ├── isometric_view.py       # Main QGraphicsView
│   ├── camera.py               # Camera controls (pan, zoom)
│   ├── tile_renderer.py        # Ground tile rendering
│   ├── sprite.py               # Animated sprite base class
│   ├── animal_sprite.py        # Animal sprite rendering
│   ├── building_sprite.py      # Building sprite rendering
│   ├── character_sprite.py     # Player & worker sprites
│   ├── effect_sprite.py        # Particle effects
│   └── layers.py               # Z-ordering & layer management
│
├── ui/                         # User interface
│   ├── __init__.py
│   ├── main_window.py          # Main game window
│   ├── hud.py                  # Heads-up display overlay
│   ├── panels/
│   │   ├── __init__.py
│   │   ├── stats_panel.py      # Money, time, resources
│   │   ├── inventory_panel.py  # Player inventory
│   │   ├── building_panel.py   # Building management
│   │   └── animal_panel.py     # Animal details
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── shop_dialog.py      # Buy animals/buildings
│   │   ├── market_dialog.py    # Sell products/animals
│   │   ├── worker_dialog.py    # Hire/manage workers
│   │   ├── settings_dialog.py  # Game settings
│   │   └── social_dialog.py    # Friends & leaderboard
│   └── widgets/
│       ├── __init__.py
│       ├── progress_bar.py     # Custom styled progress bars
│       └── tooltip.py          # Rich tooltips
│
├── network/                    # Cloud & multiplayer
│   ├── __init__.py
│   ├── cloud_sync.py           # Supabase sync manager
│   ├── friend_system.py        # Friend requests & list
│   ├── farm_visits.py          # Visit friend's farm
│   └── leaderboard.py          # Global rankings
│
├── data/                       # Data persistence
│   ├── __init__.py
│   ├── save_manager.py         # Local save/load
│   ├── database.py             # SQLite operations
│   ├── migration.py            # Database migrations
│   └── schemas/
│       ├── __init__.py
│       └── v1.py               # Schema version 1
│
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── pathfinding.py          # A* pathfinding
│   ├── math_utils.py           # Isometric conversions
│   ├── resource_loader.py      # Asset loading & caching
│   └── logger.py               # Logging configuration
│
├── assets/                     # Game assets
│   ├── sprites/
│   │   ├── animals/            # Animal spritesheets
│   │   ├── buildings/          # Building sprites
│   │   ├── characters/         # Player & worker sprites
│   │   ├── effects/            # Particle effects
│   │   └── ui/                 # UI elements
│   ├── tiles/                  # Ground tiles
│   ├── audio/
│   │   ├── music/              # Background music
│   │   └── sfx/                # Sound effects
│   └── fonts/                  # Custom fonts
│
└── tests/                      # Test suite
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures
    ├── test_models/
    ├── test_systems/
    ├── test_rendering/
    └── test_integration/
```

---

## Implementation Phases

### Phase 1: Foundation (MVP) 🎯
**Goal:** Playable core loop with one animal type  
**Duration:** ~2 weeks  
**Status:** ✅ Complete

| Task | Status | Priority |
|------|--------|----------|
| Project scaffolding & architecture | ✅ | P0 |
| Isometric rendering system | ✅ | P0 |
| Tile-based farm grid | ✅ | P0 |
| Player avatar with movement | ✅ | P0 |
| Camera controls (pan/zoom) | ✅ | P0 |
| Basic chicken implementation | ✅ | P0 |
| Coop building (single tier) | ✅ | P0 |
| Study → time → growth loop | ✅ | P0 |
| Basic HUD (money, time, inventory) | ✅ | P0 |
| Shop dialog (buy buildings/animals) | ✅ | P0 |
| Building placement mode | ✅ | P0 |
| Pen rendering with fences | ✅ | P0 |
| Animal wandering AI | ✅ | P0 |
| Market dialog (sell products/animals) | ✅ | P0 |
| Visual production feedback | ✅ | P0 |
| Local save/load | ✅ | P0 |
| Anki hook integration | ✅ | P0 |

### Phase 2: Core Economy 💰
**Goal:** Full animal roster, buildings, and market system  
**Duration:** ~2 weeks  
**Status:** ✅ Complete

| Task | Status | Priority |
|------|--------|----------|
| Pig implementation | ✅ | P1 |
| Cow implementation | ✅ | P1 |
| Economy balancing | ✅ | P1 |
| Building upgrade system | ✅ | P1 |
| Farm plot unlocking | ✅ | P1 |
| Product quality tiers | ✅ | P2 |
| Feed system (buy, consume, affects health) | ✅ | P2 |
| Building placement preview | ✅ | P2 |
| Grid visibility toggle | ✅ | P2 |
| ~~Worker system~~ | ❌ Removed | - |
| ~~Transport vehicles~~ | ❌ Removed | - |
| ~~Market system with distance~~ | ❌ Removed | - |
| Dynamic pricing | 🔴 | P3 |

### Phase 3: ~~Workers & Automation~~ Additional Features 🎮
**Goal:** QoL improvements and advanced mechanics  
**Duration:** ~1 week  
**Status:** 🔴 Not Started

| Task | Status | Priority |
|------|--------|----------|
| Dynamic market pricing | 🔴 | P2 |
| Seasonal system | 🔴 | P3 |
| Achievement system | 🔴 | P3 |
| Quest system | 🔴 | P3 |
| Study quality bonuses | 🔴 | P3 |

### Phase 4: Polish & Animation ✨
**Goal:** Full visual polish  
**Duration:** ~2 weeks  
**Status:** 🔴 Not Started

| Task | Status | Priority |
|------|--------|----------|
| Animal animations (idle, walk, eat, produce) | 🔴 | P2 |
| Worker animations | 🔴 | P2 |
| Building animations | 🔴 | P2 |
| Day/night cycle | 🔴 | P2 |
| Weather effects | 🔴 | P2 |
| Particle effects | 🔴 | P2 |
| Sound effects | 🔴 | P2 |
| Background music | 🔴 | P2 |
| UI polish & transitions | 🔴 | P2 |

### Phase 5: Social Features 🌐
**Goal:** Multiplayer and social systems  
**Duration:** ~2 weeks  
**Status:** 🔴 Not Started

| Task | Status | Priority |
|------|--------|----------|
| Cloud sync (Supabase) | 🔴 | P2 |
| User authentication | 🔴 | P2 |
| Friend system | 🔴 | P2 |
| Farm visit system | 🔴 | P2 |
| Help actions on friend farms | 🔴 | P2 |
| Trading system | 🔴 | P2 |
| Leaderboards | 🔴 | P2 |

### Phase 6: Advanced Features 🚀
**Goal:** Depth and replayability  
**Duration:** ~2 weeks  
**Status:** 🔴 Not Started

| Task | Status | Priority |
|------|--------|----------|
| Seasonal system | 🔴 | P3 |
| Health & disease system | 🔴 | P3 |
| Breeding system | 🔴 | P3 |
| Achievement system | 🔴 | P3 |
| Quest system | 🔴 | P3 |
| Study quality bonuses | 🔴 | P3 |
| Streak rewards | 🔴 | P3 |
| Player customization | 🔴 | P3 |
| Rare animals/items | 🔴 | P3 |

---

## Detailed Task Breakdown

### Phase 1 Detailed Tasks

#### 1.1 Project Scaffolding
```
[x] Create directory structure as defined in architecture
[x] Set up pyproject.toml with dependencies
[x] Configure pytest
[ ] Set up logging
[x] Create constants.py with game configuration
[x] Create __init__.py with Anki menu hook
[ ] Create manifest.json for Anki addon
```

#### 1.2 Isometric Rendering System
```
[x] Implement IsometricView (QGraphicsView subclass)
[x] Implement screen-to-iso coordinate conversion
[x] Implement iso-to-screen coordinate conversion
[x] Implement tile rendering with proper Z-ordering
[x] Implement sprite layering system
[x] Add render loop with delta time
[ ] Optimize with dirty rect updates
```

#### 1.3 Tile-Based Farm Grid
```
[x] Define Tile model (grass, dirt, water, etc.)
[x] Implement FarmGrid class with 2D tile array
[x] Load tile sprites (using placeholders)
[x] Render grid with proper isometric projection
[x] Implement tile click detection
[ ] Add tile highlighting on hover
```

#### 1.4 Player Avatar
```
[x] Define Player model
[x] Implement A* pathfinding
[x] Create player sprite with walk animations (placeholders)
[x] Handle click-to-move input
[x] Implement smooth movement interpolation
[x] Add interaction radius detection
```

#### 1.5 Camera System
```
[x] Implement pan with mouse drag / edge scroll
[x] Implement zoom with scroll wheel
[x] Add zoom limits (min/max)
[x] Implement smooth zoom transitions
[x] Add camera follow player option
[x] Implement camera bounds (don't show outside farm)
```

#### 1.6 Chicken Implementation
```
[x] Define Animal base model
[x] Define Chicken subclass with stats
[x] Define growth stages (baby, teen, adult)
[x] Implement age/maturity tracking
[x] Implement production cycle (egg laying)
[ ] Create chicken sprite with animations
[ ] Add chicken to farm and render
```

#### 1.7 Coop Building
```
[x] Define Building base model
[x] Define Coop building type
[x] Implement capacity system
[ ] Implement building placement
[ ] Create coop sprite
[ ] Handle building click to open panel
[ ] Implement animal containment within building bounds
```

#### 1.8 Study-Time-Growth Loop
```
[x] Create Anki hook for card answer events
[x] Implement TimeSystem with configurable rates
[x] Connect card answers to time advancement
[x] Trigger growth updates on time advance
[x] Trigger production checks on time advance
[x] Update UI to reflect changes
[x] Add visual feedback (floating product icons)
```

#### 1.9 Basic HUD
```
[x] Create HUD in side panel
[x] Display current money
[x] Display current farm time/day
[x] Display inventory (eggs, milk, truffles)
[x] Style with farm theme
```

#### 1.10 On-Site Selling
```
[x] Implement basic inventory system
[x] Create Market dialog with tabs
[x] Products tab - sell eggs/milk/truffles
[x] Animals tab - sell livestock
[x] Calculate product/animal values
[x] Execute sales transactions
[x] Update money display
[x] Remove sold animal sprites from view
```

#### 1.11 Local Save/Load
```
[ ] Define save data schema
[ ] Implement SaveManager class
[ ] Serialize farm state to JSON
[ ] Deserialize JSON to farm state
[ ] Auto-save on key events
[ ] Load save on game start
[ ] Handle missing/corrupted saves
```

#### 1.12 Anki Integration
```
[ ] Register addon in Anki menu
[ ] Create game window launch action
[ ] Hook into reviewer_did_answer_card
[ ] Pass card ease to game engine
[ ] Handle Anki sync events
[ ] Clean up on Anki close
```

---

## Data Models

### Core Entities

```python
# models/animal.py
@dataclass
class Animal:
    id: str                      # UUID
    type: AnimalType             # CHICKEN, PIG, COW
    name: str                    # Optional pet name
    age_hours: int               # Total age in game hours
    maturity: float              # 0.0 to 1.0
    health: float                # 0.0 to 1.0
    happiness: float             # 0.0 to 1.0
    hunger: float                # 0.0 to 1.0 (1 = full)
    building_id: str             # Which building they're in
    position: Tuple[float, float]  # Position within building
    
    # Calculated properties
    @property
    def growth_stage(self) -> GrowthStage:
        if self.maturity < 0.33:
            return GrowthStage.BABY
        elif self.maturity < 0.66:
            return GrowthStage.TEEN
        return GrowthStage.ADULT
    
    @property
    def can_produce(self) -> bool:
        return self.maturity >= 1.0 and self.health > 0.3
    
    @property
    def sale_value(self) -> int:
        base = ANIMAL_BASE_PRICES[self.type]
        return int(base * self.maturity * self.health)
```

```python
# models/building.py
@dataclass
class Building:
    id: str                      # UUID
    type: BuildingType           # COOP, BARN, etc.
    level: int                   # Upgrade level (1-4)
    position: Tuple[int, int]    # Grid position
    animals: List[str]           # Animal IDs
    cleanliness: float           # 0.0 to 1.0
    assigned_workers: List[str]  # Worker IDs
    
    @property
    def capacity(self) -> int:
        return BUILDING_CAPACITIES[self.type][self.level]
    
    @property
    def is_full(self) -> bool:
        return len(self.animals) >= self.capacity
    
    @property
    def production_bonus(self) -> float:
        return 1.0 + (self.level - 1) * 0.15
```

```python
# models/worker.py
@dataclass
class Worker:
    id: str
    type: WorkerType             # FARMHAND, VET, DRIVER, MANAGER
    name: str
    level: int                   # 1-10
    experience: int
    energy: float                # 0.0 to 1.0
    happiness: float
    salary: int                  # Per day
    assigned_zone: Optional[str]
    current_task: Optional[Task]
    
    @property
    def capacity(self) -> int:
        base = WORKER_BASE_CAPACITY[self.type]
        return int(base * (1 + self.level * 0.1))
    
    @property
    def efficiency(self) -> float:
        return (self.level / 10) * (self.energy * 0.5 + 0.5) * (self.happiness * 0.3 + 0.7)
```

```python
# models/farm.py
@dataclass
class Farm:
    id: str
    name: str
    owner_id: str
    money: int
    current_time: FarmTime       # Day, hour, minute
    season: Season
    unlocked_zones: List[str]
    buildings: Dict[str, Building]
    animals: Dict[str, Animal]
    workers: Dict[str, Worker]
    vehicles: Dict[str, Vehicle]
    inventory: Inventory
    statistics: FarmStatistics
```

---

## API Specifications

### Event Bus Events

```python
# core/event_bus.py

# Study Events
CARD_ANSWERED = "card_answered"           # {ease: str, card_id: int}
STUDY_SESSION_START = "study_session_start"
STUDY_SESSION_END = "study_session_end"

# Time Events  
TIME_ADVANCED = "time_advanced"           # {hours: int, new_time: FarmTime}
DAY_CHANGED = "day_changed"               # {day: int, season: Season}
SEASON_CHANGED = "season_changed"         # {season: Season}

# Animal Events
ANIMAL_BORN = "animal_born"               # {animal: Animal}
ANIMAL_MATURED = "animal_matured"         # {animal: Animal}
ANIMAL_PRODUCED = "animal_produced"       # {animal: Animal, product: Product}
ANIMAL_SICK = "animal_sick"               # {animal: Animal}
ANIMAL_SOLD = "animal_sold"               # {animal: Animal, price: int}

# Building Events
BUILDING_PLACED = "building_placed"       # {building: Building}
BUILDING_UPGRADED = "building_upgraded"   # {building: Building}
BUILDING_FULL = "building_full"           # {building: Building}

# Worker Events
WORKER_HIRED = "worker_hired"             # {worker: Worker}
WORKER_TASK_COMPLETE = "worker_task_complete"  # {worker: Worker, task: Task}
WORKER_LEVEL_UP = "worker_level_up"       # {worker: Worker}

# Economy Events
MONEY_CHANGED = "money_changed"           # {old: int, new: int, reason: str}
TRANSACTION = "transaction"               # {type: str, amount: int, items: list}

# Social Events
FRIEND_VISIT = "friend_visit"             # {visitor_id: str}
TRADE_RECEIVED = "trade_received"         # {trade: Trade}
```

### Cloud API Endpoints

```
Supabase Tables:

users
├── id: uuid (PK)
├── username: text (unique)
├── password_hash: text
├── created_at: timestamp
└── last_active: timestamp

farms
├── id: uuid (PK)
├── user_id: uuid (FK → users)
├── name: text
├── data: jsonb (full farm state)
├── total_money_earned: bigint (for leaderboard)
├── updated_at: timestamp
└── is_public: boolean

friends
├── id: uuid (PK)
├── user_id: uuid (FK → users)
├── friend_id: uuid (FK → users)
├── status: text (pending, accepted)
└── created_at: timestamp

visits
├── id: uuid (PK)
├── visitor_id: uuid (FK → users)
├── farm_id: uuid (FK → farms)
├── visited_at: timestamp
└── help_actions: jsonb

trades
├── id: uuid (PK)
├── from_user_id: uuid (FK → users)
├── to_user_id: uuid (FK → users)
├── offered_items: jsonb
├── requested_items: jsonb
├── status: text
└── created_at: timestamp
```

---

## Asset Requirements

### Sprites Needed (Stardew Valley Style)

#### Animals (per type)
```
chickens/
├── baby_idle.png       (4 frames, 32x32 each)
├── baby_walk.png       (8 frames, 4 directions)
├── teen_idle.png       (4 frames)
├── teen_walk.png       (8 frames)
├── adult_idle.png      (4 frames)
├── adult_walk.png      (8 frames)
├── adult_eat.png       (6 frames)
├── adult_produce.png   (8 frames, laying egg)
└── adult_sleep.png     (2 frames)

pigs/
├── (same structure)
└── adult_mudroll.png   (6 frames, unique)

cows/
├── (same structure)
└── adult_graze.png     (4 frames, unique)
```

#### Buildings
```
buildings/
├── coop_level1.png     (64x64 isometric)
├── coop_level2.png
├── coop_level3.png
├── coop_level4.png
├── barn_level1.png     (96x96 isometric)
├── barn_level2.png
├── ...
├── farmhouse.png
├── silo.png
├── market_stall.png
└── truck_depot.png
```

#### Characters
```
characters/
├── player/
│   ├── idle.png        (4 directions)
│   ├── walk.png        (8 frames x 4 directions)
│   └── interact.png    (4 frames)
├── farmhand/
│   ├── idle.png
│   ├── walk.png
│   ├── feed.png
│   └── clean.png
├── vet/
│   └── ...
└── driver/
    └── ...
```

#### Tiles
```
tiles/
├── grass_01.png        (32x16 isometric diamond)
├── grass_02.png
├── grass_03.png        (variation)
├── dirt_01.png
├── dirt_02.png
├── path_straight.png
├── path_corner.png
├── water.png           (animated, 4 frames)
└── fence_*.png         (various orientations)
```

#### UI
```
ui/
├── panel_background.png
├── button_normal.png
├── button_hover.png
├── button_pressed.png
├── icons/
│   ├── coin.png
│   ├── clock.png
│   ├── heart.png
│   ├── star.png
│   └── ...
└── cursors/
    ├── normal.png
    ├── interact.png
    └── move.png
```

---

## Testing Strategy

### Unit Tests
- All model classes
- All system calculations
- Coordinate conversions
- Pathfinding algorithm
- Save/load serialization

### Integration Tests
- Study → time → growth flow
- Buy → place → manage → sell flow
- Worker assignment → task execution
- Cloud sync round-trip

### Visual Tests
- Sprite rendering
- Animation playback
- Z-ordering correctness
- UI responsiveness

### Performance Tests
- 100+ animals rendering at 60fps
- Large farm pathfinding (<16ms)
- Save/load under 500ms

---

## Progress Tracking

### Current Sprint: Phase 1 - Foundation

**Sprint Goal:** Playable MVP with chickens, coops, and basic loop

**Start Date:** TBD  
**Target End:** TBD

### Completed Tasks
```
[2026-01-17] Project scaffolding & directory structure
[2026-01-17] Core models: Animal, Building, Product, Worker, Player, Vehicle, Farm
[2026-01-17] Event bus system
[2026-01-17] Time system with study-to-game-time conversion
[2026-01-17] Constants and configuration
[2026-01-17] Math utilities for isometric transformations
[2026-01-17] Basic main window with placeholder UI
[2026-01-17] Test fixtures and initial Animal model tests
[2026-01-17] Sprite base class with animation system
[2026-01-17] TileSprite, BuildingSprite, CharacterSprite, AnimalSprite
[2026-01-17] Camera system with pan/zoom controls
[2026-01-17] IsometricView (QGraphicsView) renderer
[2026-01-17] Tile grid system with zone management
[2026-01-17] A* pathfinding for player movement
[2026-01-17] PathFollower for smooth movement interpolation
[2026-01-17] Main window integration with isometric view
[2026-01-17] Click-to-move player interaction
[2026-01-17] Anki addon entry point and hooks
[2026-01-17] Standalone runner for testing outside Anki
[2026-01-17] Shop dialog for buying buildings and animals
[2026-01-17] Building placement mode with preview
[2026-01-17] PenSprite with fence rendering
[2026-01-17] Animal wandering AI within pen bounds
[2026-01-17] Growth system connecting time → animal maturity
[2026-01-17] Production system (mature animals produce products)
[2026-01-17] Inventory display in side panel HUD
[2026-01-17] Market dialog with Products tab (sell eggs/milk/truffles)
[2026-01-17] Market dialog with Animals tab (sell livestock)
[2026-01-17] FloatingEffectSprite for visual production feedback
[2026-01-17] Balanced growth rates (~1000 cards for chicken maturity)
[2026-01-17] Local save/load system with JSON serialization
[2026-01-17] Auto-save on key events (building, animal purchase, sales)
[2026-01-17] Auto-save every 25 cards answered
[2026-01-17] Consolidated logging to Anki profile folder
[2026-01-17] AnkiWeb addon packaging and distribution scripts
[2026-01-17] Simplified time system (1 card = 1 minute, removed modes)
[2026-01-17] Fixed time progression bug (was not advancing on Again/Hard)
[2026-01-17] Pig & Cow implementation (buildings, sprites, production)
[2026-01-17] Economy balancing (Chicken < Pig < Cow profit progression)
[2026-01-17] Removed test Study button, fixed UI text cutoff
[2026-01-17] Fixed animal capacity bug (cows taking 3 slots instead of 1)
[2026-01-17] Shop UI live-updates building occupancy after purchase
[2026-01-17] Redesigned Animals tab: animal-first selection, scrollable building list
[2026-01-17] Added dev test button (+1 Hour) for testing time progression
[2026-01-17] Building Details Dialog - click pen to see animals & stats
[2026-01-17] Building upgrade system (Level 1-4 with capacity/production bonuses)
[2026-01-17] Fixed Building Dialog styling (labels were showing as empty boxes)
[2026-01-17] Removed Controls section from sidebar, fixed inventory text cutoff
[2026-01-17] Rebalanced pen capacities (max 16/12/9 instead of 50/30/25)
[2026-01-17] Rebalanced upgrade costs (cheaper than building new pens)
[2026-01-17] Farm Zone Unlocking system with tiered pricing
[2026-01-17] Locked zones render darker, click to unlock dialog
[2026-01-17] HUD shows zones unlocked and next zone cost
[2026-01-17] Custom styled ZoneUnlockDialog (dark theme)
[2026-01-17] Custom styled ZoneLockedDialog (wrong order message)
[2026-01-17] Zone hover highlight (shows boundary + "Plot X" label)
[2026-01-17] Renamed "Zones" to "Plots" (more farm-themed)
[2026-01-18] Product quality tiers (Basic → Good → Premium → Artisan)
[2026-01-18] Feed system (buy feed, auto-consume, affects health → quality)
[2026-01-18] Removed happiness metric (simplified to health-only)
[2026-01-18] Removed player sprite and movement logic (no player character)
[2026-01-18] Cleaned up JSON save data (removed unused fields)
[2026-01-18] Removed vehicles, workers, and market types (simplified)
[2026-01-18] Grid hidden by default, shows only during building placement
[2026-01-18] Building placement preview (green/red isometric footprint)
```

### In Progress
```
[SPRITES] Awaiting Stardew Valley-style sprites from user
[PHASE2] Phase 2: Core Economy - Product Quality next
```

### Blocked
```
[NONE] - Placeholder rendering system allows parallel development
```

### Next Priority (Phase 3)
```
[1] Dynamic market pricing (supply/demand fluctuations)
[2] Seasonal system (affects production rates)
[3] Achievement system (milestones & rewards)
[4] Quest system (daily/weekly objectives)
```

### Notes & Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-17 | Use Stardew Valley pixel art style | User preference, matches casual farming aesthetic |
| 2026-01-17 | PyQt6 + QGraphicsView for rendering | Native to Anki, hardware accelerated |
| 2026-01-17 | SQLite for local, Supabase for cloud | Offline-first with sync capability |
| 2026-01-17 | Deterministic growth system | More satisfying than random, rewards consistent study |
| 2026-01-17 | Event-driven architecture | Decoupled systems, easier testing, extensible |
| 2026-01-17 | Dataclass models with serialization | Clean, type-safe, easy JSON persistence |
| 2026-01-17 | Separate models from Qt code | Enables testing without GUI, cleaner architecture |

---

## How to Use This Document

### For Developers
1. Check **Progress Tracking** for current sprint status
2. Pick tasks from **In Progress** or **Completed Tasks** sections
3. Reference **Data Models** for entity structures
4. Follow **Architecture Overview** for file placement

### For Code Review
1. Ensure new code matches **Architecture Overview**
2. Verify models match **Data Models** specifications
3. Check events match **Event Bus Events**

### Updating This Document
1. Move tasks between status sections as work progresses
2. Add decisions to **Notes & Decisions Log**
3. Update **Last Updated** date at top
4. Keep task granularity consistent

---

*This is a living document. Update it as implementation progresses.*
