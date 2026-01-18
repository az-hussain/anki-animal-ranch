# Sprite Generation Guide for Anki Animal Ranch

## 🎨 Master Style Prompt

Use this base prompt for ALL sprites to ensure visual consistency:

```
Stardew Valley pixel art style, isometric 2.5D perspective viewed from above at 45-degree angle, 
warm and cozy farm aesthetic, soft pastel colors with gentle shadows, thick black outlines (2px), 
clean pixel art with limited color palette (max 16 colors per sprite), charming and whimsical feel,
PNG format with transparent background, NO gradients, NO anti-aliasing on edges
```

---

## 📐 Dimension Reference

### Tile System
- **Base tile size:** 64×32 pixels (isometric diamond)
- **1×1 footprint sprite:** 64×64 pixels (includes height for 3D objects)
- **2×1 footprint sprite:** 96×64 pixels
- **2×2 footprint sprite:** 128×96 pixels
- **3×2 footprint sprite:** 160×96 pixels
- **3×3 footprint sprite:** 192×128 pixels

### Height Guidelines
- **Flat items** (flower beds, ponds): Base height only
- **Short items** (benches, troughs): +16-24px above base
- **Medium items** (hay bales, carts): +24-32px above base  
- **Tall items** (trees, scarecrows, lamp posts): +48-64px above base
- **Very tall items** (windmill, silo): +80-100px above base

---

## 🐔 ANIMALS

### Chicken
| Variant | Dimensions | Directions | Filename Pattern |
|---------|------------|------------|------------------|
| Baby | 24×24 | 4 (N/E/S/W) | `chicken_baby_{dir}.png` |
| Teen | 28×28 | 4 | `chicken_teen_{dir}.png` |
| Adult | 32×32 | 4 | `chicken_adult_{dir}.png` |
| Walking animation | 32×32 | 4 dirs × 4 frames | `chicken_walk_{dir}_{frame}.png` |
| Idle animation | 32×32 | 4 dirs × 2 frames | `chicken_idle_{dir}_{frame}.png` |

**Prompt addition:** "cute farm chicken, fluffy white/brown feathers, small red comb, yellow beak and feet"

### Pig
| Variant | Dimensions | Directions | Filename Pattern |
|---------|------------|------------|------------------|
| Baby | 28×28 | 4 | `pig_baby_{dir}.png` |
| Teen | 36×36 | 4 | `pig_teen_{dir}.png` |
| Adult | 44×44 | 4 | `pig_adult_{dir}.png` |
| Walking animation | 44×44 | 4 dirs × 4 frames | `pig_walk_{dir}_{frame}.png` |
| Idle animation | 44×44 | 4 dirs × 2 frames | `pig_idle_{dir}_{frame}.png` |

**Prompt addition:** "adorable pink pig, curly tail, floppy ears, snout with nostrils visible"

### Cow
| Variant | Dimensions | Directions | Filename Pattern |
|---------|------------|------------|------------------|
| Baby | 32×32 | 4 | `cow_baby_{dir}.png` |
| Teen | 44×44 | 4 | `cow_teen_{dir}.png` |
| Adult | 56×56 | 4 | `cow_adult_{dir}.png` |
| Walking animation | 56×56 | 4 dirs × 4 frames | `cow_walk_{dir}_{frame}.png` |
| Idle animation | 56×56 | 4 dirs × 2 frames | `cow_idle_{dir}_{frame}.png` |

**Prompt addition:** "friendly dairy cow, black and white spotted pattern, pink udder, gentle eyes, small horns"

---

## 🏠 BUILDINGS (Pens)

### Chicken Coop (2×2)
| Level | Dimensions | Filename |
|-------|------------|----------|
| Level 1 | 128×96 | `coop_lv1.png` |
| Level 2 | 128×96 | `coop_lv2.png` |
| Level 3 | 128×96 | `coop_lv3.png` |
| Level 4 | 128×96 | `coop_lv4.png` |

**Prompt addition:** "wooden chicken coop with red roof, small door with ramp, nesting boxes visible, hay on ground"

### Pig Sty (3×2)
| Level | Dimensions | Filename |
|-------|------------|----------|
| Level 1 | 160×96 | `pigsty_lv1.png` |
| Level 2 | 160×96 | `pigsty_lv2.png` |
| Level 3 | 160×96 | `pigsty_lv3.png` |
| Level 4 | 160×96 | `pigsty_lv4.png` |

**Prompt addition:** "rustic pig pen with wooden fence, mud puddle, feeding trough, covered shelter area"

### Cow Barn (3×3)
| Level | Dimensions | Filename |
|-------|------------|----------|
| Level 1 | 192×128 | `barn_lv1.png` |
| Level 2 | 192×128 | `barn_lv2.png` |
| Level 3 | 192×128 | `barn_lv3.png` |
| Level 4 | 192×128 | `barn_lv4.png` |

**Prompt addition:** "classic red barn with white trim, large doors, hay loft window, weathervane on top"

---

## 🎨 DECORATIONS

### 🌿 Nature & Plants

#### Hay Bale (1×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 64×64 | `hay_bale_n.png` |
| East | 64×64 | `hay_bale_e.png` |
| South | 64×64 | `hay_bale_s.png` |
| West | 64×64 | `hay_bale_w.png` |

**Prompt addition:** "rectangular hay bale, golden yellow straw, twine wrapped around middle, loose strands"

#### Flower Bed (1×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 64×64 | `flower_bed_n.png` |
| East | 64×64 | `flower_bed_e.png` |
| South | 64×64 | `flower_bed_s.png` |
| West | 64×64 | `flower_bed_w.png` |

**Prompt addition:** "garden flower bed with colorful flowers (pink, yellow, purple), green leaves, brown soil border"

#### Tree (1×1) - NO ROTATION
| Variant | Dimensions | Filename |
|---------|------------|----------|
| Standard | 64×80 | `tree.png` |
| (Optional) Spring | 64×80 | `tree_spring.png` |
| (Optional) Summer | 64×80 | `tree_summer.png` |
| (Optional) Fall | 64×80 | `tree_fall.png` |
| (Optional) Winter | 64×80 | `tree_winter.png` |

**Prompt addition:** "oak tree with thick brown trunk, lush green round canopy, visible texture in bark"

#### Scarecrow (1×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 64×80 | `scarecrow_n.png` |
| East | 64×80 | `scarecrow_e.png` |
| South | 64×80 | `scarecrow_s.png` |
| West | 64×80 | `scarecrow_w.png` |

**Prompt addition:** "friendly scarecrow on wooden post, plaid shirt, straw hat, button eyes, straw sticking out"

#### Pumpkin Patch (2×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 96×64 | `pumpkin_patch_n.png` |
| East | 64×96 | `pumpkin_patch_e.png` |
| South | 96×64 | `pumpkin_patch_s.png` |
| West | 64×96 | `pumpkin_patch_w.png` |

**Prompt addition:** "patch with 3-4 orange pumpkins of different sizes, green vines, large leaves"

---

### 🏚️ Farm Structures

#### Windmill (2×2) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 128×120 | `windmill_n.png` |
| East | 128×120 | `windmill_e.png` |
| South | 128×120 | `windmill_s.png` |
| West | 128×120 | `windmill_w.png` |
| Blade animation | 128×120 | `windmill_{dir}_frame{1-4}.png` |

**Prompt addition:** "Dutch-style windmill, stone/brick base, wooden blades, small windows, pointed roof"

#### Water Well (1×1) - NO ROTATION
| Variant | Dimensions | Filename |
|---------|------------|----------|
| Standard | 64×72 | `water_well.png` |

**Prompt addition:** "stone well with wooden roof, rope and bucket, cobblestone base"

#### Decorative Silo (1×1) - NO ROTATION
| Variant | Dimensions | Filename |
|---------|------------|----------|
| Standard | 64×96 | `silo.png` |

**Prompt addition:** "tall cylindrical grain silo, corrugated metal texture, domed top, small ladder"

#### Wooden Cart (2×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 96×64 | `wooden_cart_n.png` |
| East | 64×96 | `wooden_cart_e.png` |
| South | 96×64 | `wooden_cart_s.png` |
| West | 64×96 | `wooden_cart_w.png` |

**Prompt addition:** "old wooden farm cart with two wheels, open cargo area, weathered wood texture"

---

### 💧 Water Features

#### Pond (2×2) - NO ROTATION
| Variant | Dimensions | Filename |
|---------|------------|----------|
| Standard | 128×80 | `pond.png` |
| With ducks (optional) | 128×80 | `pond_ducks.png` |

**Prompt addition:** "small farm pond, blue water with reflections, rocks around edge, lily pads, cattails"

#### Fountain (1×1) - NO ROTATION
| Variant | Dimensions | Filename |
|---------|------------|----------|
| Standard | 64×72 | `fountain.png` |
| Water animation | 64×72 | `fountain_frame{1-3}.png` |

**Prompt addition:** "stone garden fountain, tiered bowls, water splashing, decorative base"

#### Water Trough (1×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 64×48 | `water_trough_n.png` |
| East | 64×48 | `water_trough_e.png` |
| South | 64×48 | `water_trough_s.png` |
| West | 64×48 | `water_trough_w.png` |

**Prompt addition:** "wooden animal water trough, rectangular shape, metal bands, water inside"

---

### 🪑 Outdoor Living

#### Bench (1×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 64×48 | `bench_n.png` |
| East | 64×48 | `bench_e.png` |
| South | 64×48 | `bench_s.png` |
| West | 64×48 | `bench_w.png` |

**Prompt addition:** "rustic wooden bench, plank seat, simple backrest, slightly weathered"

#### Picnic Table (2×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 96×56 | `picnic_table_n.png` |
| East | 64×96 | `picnic_table_e.png` |
| South | 96×56 | `picnic_table_s.png` |
| West | 64×96 | `picnic_table_w.png` |

**Prompt addition:** "wooden picnic table with attached benches, classic A-frame legs"

#### Lamp Post (1×1) - NO ROTATION
| Variant | Dimensions | Filename |
|---------|------------|----------|
| Day (off) | 64×80 | `lamp_post_off.png` |
| Night (on) | 64×80 | `lamp_post_on.png` |

**Prompt addition:** "old-fashioned street lamp, black iron post, glass lantern top, warm yellow glow when lit"

---

### 🎪 Fun Extras

#### Garden Gnome (1×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 64×56 | `garden_gnome_n.png` |
| East | 64×56 | `garden_gnome_e.png` |
| South | 64×56 | `garden_gnome_s.png` |
| West | 64×56 | `garden_gnome_w.png` |

**Prompt addition:** "classic garden gnome, red pointy hat, white beard, blue jacket, holding fishing rod or shovel"

#### Mailbox (1×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 64×56 | `mailbox_n.png` |
| East | 64×56 | `mailbox_e.png` |
| South | 64×56 | `mailbox_s.png` |
| West | 64×56 | `mailbox_w.png` |

**Prompt addition:** "rural mailbox on wooden post, red flag, rounded top, slightly rusty metal"

#### Signpost (1×1) - ROTATABLE
| Direction | Dimensions | Filename |
|-----------|------------|----------|
| North | 64×72 | `signpost_n.png` |
| East | 64×72 | `signpost_e.png` |
| South | 64×72 | `signpost_s.png` |
| West | 64×72 | `signpost_w.png` |

**Prompt addition:** "wooden signpost with arrow signs pointing different directions, weathered wood"

---

## 🥚 PRODUCTS

| Product | Dimensions | Filename | Prompt Addition |
|---------|------------|----------|-----------------|
| Egg (Normal) | 24×24 | `egg_normal.png` | "brown farm egg, oval shape, slight shine" |
| Egg (Silver) | 24×24 | `egg_silver.png` | "silver/white premium egg with sparkle" |
| Egg (Gold) | 24×24 | `egg_gold.png` | "golden glowing egg with star sparkles" |
| Milk (Normal) | 24×32 | `milk_normal.png` | "glass milk bottle, white milk, metal cap" |
| Milk (Silver) | 24×32 | `milk_silver.png` | "silver-labeled premium milk bottle" |
| Milk (Gold) | 24×32 | `milk_gold.png` | "golden milk bottle with sparkles" |
| Truffle (Normal) | 24×24 | `truffle_normal.png` | "brown truffle mushroom, bumpy texture" |
| Truffle (Silver) | 24×24 | `truffle_silver.png` | "silver-dusted truffle, premium quality" |
| Truffle (Gold) | 24×24 | `truffle_gold.png` | "rare golden truffle with glow effect" |

---

## 🌍 TERRAIN TILES

| Tile Type | Dimensions | Filename | Prompt Addition |
|-----------|------------|----------|-----------------|
| Grass | 64×32 | `tile_grass.png` | "isometric grass tile, green with subtle texture variation" |
| Grass with flowers | 64×32 | `tile_grass_flowers.png` | "grass tile with small wildflowers scattered" |
| Dirt | 64×32 | `tile_dirt.png` | "brown dirt/soil tile, farming ground" |
| Path (stone) | 64×32 | `tile_path_stone.png` | "cobblestone path tile, grey stones" |
| Water | 64×32 | `tile_water.png` | "water tile, blue with wave pattern" |

---

## 🖼️ UI ELEMENTS

| Element | Dimensions | Filename | Description |
|---------|------------|----------|-------------|
| Coin | 16×16 | `ui_coin.png` | Gold coin icon for money display |
| Heart | 16×16 | `ui_heart.png` | Red heart for health display |
| Feed bag | 24×24 | `ui_feed.png` | Feed bag icon |
| Clock | 24×24 | `ui_clock.png` | Clock icon for time display |

---

## 📋 GENERATION CHECKLIST

### Priority 1 - Core (Start here)
- [ ] 3 grass tile variants
- [ ] Chicken (adult, 4 directions)
- [ ] Chicken coop (level 1)
- [ ] Egg (3 qualities)

### Priority 2 - Expanded Animals
- [ ] Chicken (baby, teen, animations)
- [ ] Pig (all variants)
- [ ] Cow (all variants)
- [ ] Pig sty (all levels)
- [ ] Cow barn (all levels)
- [ ] Milk, Truffle products

### Priority 3 - Decorations
- [ ] All 1×1 non-rotating decorations (tree, well, silo, fountain, lamp)
- [ ] All 1×1 rotating decorations (hay, flower, scarecrow, gnome, etc.)
- [ ] All 2×1 and 2×2 decorations (pond, windmill, cart, table)

### Priority 4 - Polish
- [ ] Building level variants (2-4)
- [ ] Seasonal tree variants
- [ ] Animation frames
- [ ] UI elements

---

## 💡 TIPS FOR GENERATION

1. **Always specify "transparent background"** - Critical for layering
2. **Generate at 2x size, then downscale** - Better quality
3. **Keep color count low** - Max 16 colors per sprite for pixel art feel
4. **Test isometric alignment** - Use a grid overlay to verify angles
5. **Batch similar items** - Generate all directions of one item in sequence
6. **Save as PNG-8 or PNG-24** - Preserve transparency

---

## 📁 Folder Structure

```
anki_animal_ranch/assets/
├── animals/
│   ├── chicken/
│   ├── pig/
│   └── cow/
├── buildings/
│   ├── coop/
│   ├── pigsty/
│   └── barn/
├── decorations/
│   ├── nature/
│   ├── structures/
│   ├── water/
│   ├── outdoor/
│   └── extras/
├── products/
├── tiles/
└── ui/
```

---

**Total sprites needed:**
- Animals: ~72 (3 types × 3 stages × 4 directions × 2+ animation states)
- Buildings: ~12 (3 types × 4 levels)
- Decorations: ~58 (19 types, some with 4 directions)
- Products: 9
- Tiles: 5
- UI: 4

**Grand total: ~160 sprites**
