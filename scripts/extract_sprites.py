#!/usr/bin/env python3
"""
Sprite Sheet Extractor

Takes a sprite sheet with a solid color background and extracts
individual sprites as separate transparent PNG files.

Usage:
    python extract_sprites.py <input_image> [--background RED|GREEN|BLUE|auto] [--output-dir <dir>]

Example:
    python extract_sprites.py spritesheet.png --background RED --output-dir ./sprites/
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "numpy"])
    from PIL import Image
    import numpy as np


def detect_background_color(img_array: np.ndarray) -> tuple[int, int, int]:
    """Auto-detect the background color by sampling corners."""
    h, w = img_array.shape[:2]
    
    # Sample corners
    corners = [
        img_array[0, 0],           # Top-left
        img_array[0, w-1],         # Top-right
        img_array[h-1, 0],         # Bottom-left
        img_array[h-1, w-1],       # Bottom-right
    ]
    
    # Take the most common corner color
    colors = [tuple(c[:3]) for c in corners]
    bg_color = max(set(colors), key=colors.count)
    
    print(f"Auto-detected background color: RGB{bg_color}")
    return bg_color


def create_mask(img_array: np.ndarray, bg_color: tuple[int, int, int], tolerance: int = 30) -> np.ndarray:
    """Create a binary mask where True = sprite pixel, False = background."""
    # Calculate distance from background color
    diff = np.abs(img_array[:, :, :3].astype(int) - np.array(bg_color))
    distance = np.sum(diff, axis=2)
    
    # Pixels with distance > tolerance are considered sprite pixels
    mask = distance > tolerance
    return mask


def find_sprite_bounding_boxes(mask: np.ndarray, min_size: int = 20, max_size: int = 800) -> list[tuple[int, int, int, int]]:
    """Find bounding boxes of individual sprites using connected components."""
    from scipy import ndimage
    
    # Label connected components
    labeled, num_features = ndimage.label(mask)
    print(f"Found {num_features} potential sprites")
    
    bounding_boxes = []
    
    for i in range(1, num_features + 1):
        # Find pixels belonging to this component
        component_mask = labeled == i
        rows = np.any(component_mask, axis=1)
        cols = np.any(component_mask, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            continue
            
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        
        width = x_max - x_min + 1
        height = y_max - y_min + 1
        
        # Filter out tiny noise and overly large detections (probably the whole image)
        if width >= min_size and height >= min_size and width <= max_size and height <= max_size:
            # Add padding
            padding = 2
            y_min = max(0, y_min - padding)
            x_min = max(0, x_min - padding)
            y_max = min(mask.shape[0] - 1, y_max + padding)
            x_max = min(mask.shape[1] - 1, x_max + padding)
            
            bounding_boxes.append((x_min, y_min, x_max + 1, y_max + 1))
    
    # Sort by position (top-to-bottom, left-to-right)
    bounding_boxes.sort(key=lambda b: (b[1] // 100, b[0]))
    
    return bounding_boxes


def resize_sprite(sprite: Image.Image, target_size: tuple[int, int], mode: str = "fit") -> Image.Image:
    """
    Resize a sprite to target dimensions.
    
    Modes:
    - fit: Maintain aspect ratio, fit within target size, center on transparent canvas
    - stretch: Stretch to exact target size (may distort)
    - width: Scale to target width, maintain aspect ratio
    - height: Scale to target height, maintain aspect ratio
    """
    target_w, target_h = target_size
    orig_w, orig_h = sprite.size
    
    if mode == "stretch":
        return sprite.resize(target_size, Image.Resampling.LANCZOS)
    
    elif mode == "width":
        scale = target_w / orig_w
        new_h = int(orig_h * scale)
        return sprite.resize((target_w, new_h), Image.Resampling.LANCZOS)
    
    elif mode == "height":
        scale = target_h / orig_h
        new_w = int(orig_w * scale)
        return sprite.resize((new_w, target_h), Image.Resampling.LANCZOS)
    
    else:  # fit mode (default)
        # Calculate scale to fit within target while maintaining aspect ratio
        scale = min(target_w / orig_w, target_h / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        
        # Resize the sprite
        resized = sprite.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Create transparent canvas of target size
        canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
        
        # Center the sprite on canvas (horizontally centered, vertically at bottom)
        x_offset = (target_w - new_w) // 2
        y_offset = target_h - new_h  # Anchor to bottom
        
        canvas.paste(resized, (x_offset, y_offset), resized)
        return canvas


def extract_sprite(img: Image.Image, bbox: tuple[int, int, int, int], 
                   bg_color: tuple[int, int, int], tolerance: int = 30,
                   precise_mode: bool = False) -> Image.Image:
    """
    Extract a single sprite and make background transparent.
    
    Args:
        precise_mode: If True, only removes pixels very close to the exact bg_color.
                      Use this when bg is a specific color like #FE0103 and you want
                      to preserve similar colors (orange beaks, red combs, etc.)
    """
    # Crop to bounding box
    sprite = img.crop(bbox)
    
    # Convert to RGBA
    sprite = sprite.convert("RGBA")
    data = np.array(sprite)
    
    # Direct distance from background color
    diff = np.abs(data[:, :, :3].astype(float) - np.array(bg_color))
    distance = np.sum(diff, axis=2)
    
    if precise_mode:
        # PRECISE MODE: Only remove pixels very close to the exact background color
        # This preserves orange beaks, red combs, etc.
        is_background = distance <= tolerance
    else:
        # AGGRESSIVE MODE (original behavior)
        r, g, b = bg_color
        pixel_r = data[:, :, 0].astype(float)
        pixel_g = data[:, :, 1].astype(float)
        pixel_b = data[:, :, 2].astype(float)
        
        # Detect bg-tinted pixels
        if r > g and r > b:  # Red background
            is_bg_tinted = (pixel_r > pixel_g + 30) & (pixel_r > pixel_b + 30)
        elif g > r and g > b:  # Green background
            is_bg_tinted = (pixel_g > pixel_r + 30) & (pixel_g > pixel_b + 30)
        elif b > r and b > g:  # Blue background
            is_bg_tinted = (pixel_b > pixel_r + 30) & (pixel_b > pixel_g + 30)
        else:
            is_bg_tinted = np.zeros_like(pixel_r, dtype=bool)
        
        is_background = (distance <= tolerance) | (is_bg_tinted & (distance <= tolerance * 3))
        
        # Clean up red channel bleed (only in aggressive mode)
        if r > g and r > b:
            red_tint_mask = (pixel_r > pixel_g + 50) & (pixel_r > pixel_b + 50) & (distance <= tolerance * 2)
            is_background = is_background | red_tint_mask
    
    # Set alpha to 0 for background pixels
    data[:, :, 3] = np.where(is_background, 0, 255)
    
    return Image.fromarray(data)


def main():
    parser = argparse.ArgumentParser(description="Extract sprites from a sprite sheet")
    parser.add_argument("input", help="Input sprite sheet image")
    parser.add_argument("--background", "-b", default="auto",
                       help="Background color: RED, GREEN, BLUE, MAGENTA, #RRGGBB hex, or 'auto' (default: auto)")
    parser.add_argument("--output-dir", "-o", default="./extracted_sprites",
                       help="Output directory for extracted sprites")
    parser.add_argument("--tolerance", "-t", type=int, default=50,
                       help="Color tolerance for background detection (default: 50)")
    parser.add_argument("--precise", action="store_true",
                       help="Precise mode: only remove exact background color (preserves similar colors like orange beaks)")
    parser.add_argument("--min-size", "-m", type=int, default=20,
                       help="Minimum sprite size in pixels (default: 20)")
    parser.add_argument("--max-size", "-M", type=int, default=800,
                       help="Maximum sprite size in pixels (default: 800, filters out full-image detections)")
    parser.add_argument("--prefix", "-p", default="sprite",
                       help="Prefix for output filenames (default: 'sprite')")
    parser.add_argument("--resize", "-r", type=str, default=None,
                       help="Resize sprites to WIDTHxHEIGHT (e.g., '64x64' or '128x96')")
    parser.add_argument("--resize-mode", default="fit",
                       help="Resize mode: 'fit' (maintain aspect, fit in box), 'stretch' (exact size), 'width' (scale to width), 'height' (scale to height)")
    
    args = parser.parse_args()
    
    # Load image
    print(f"Loading: {args.input}")
    img = Image.open(args.input)
    img_array = np.array(img.convert("RGB"))
    
    print(f"Image size: {img.width}x{img.height}")
    
    # Determine background color
    bg_colors = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "magenta": (255, 0, 255),
        "cyan": (0, 255, 255),
    }
    
    if args.background.lower() == "auto":
        bg_color = detect_background_color(img_array)
    elif args.background.lower() in bg_colors:
        bg_color = bg_colors[args.background.lower()]
    elif args.background.startswith("#"):
        # Parse hex color like #FE0103
        try:
            hex_color = args.background.lstrip("#")
            bg_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except:
            print(f"Invalid hex color: {args.background}")
            sys.exit(1)
    else:
        # Try to parse as RGB
        try:
            parts = args.background.split(",")
            bg_color = tuple(int(p.strip()) for p in parts)
        except:
            print(f"Unknown background color: {args.background}")
            print("Use RED, GREEN, BLUE, MAGENTA, #RRGGBB, auto, or R,G,B values")
            sys.exit(1)
    
    print(f"Using background color: RGB{bg_color}")
    
    # Create mask
    print("Creating sprite mask...")
    mask = create_mask(img_array, bg_color, args.tolerance)
    
    # Find sprites
    print("Finding sprite bounding boxes...")
    try:
        bboxes = find_sprite_bounding_boxes(mask, args.min_size, args.max_size)
    except ImportError:
        print("scipy not found, installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])
        from scipy import ndimage
        bboxes = find_sprite_bounding_boxes(mask, args.min_size, args.max_size)
    
    print(f"Found {len(bboxes)} sprites to extract")
    
    if len(bboxes) == 0:
        print("No sprites found! Try adjusting --tolerance or --min-size")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse resize option if provided
    target_size = None
    if args.resize:
        try:
            w, h = args.resize.lower().split('x')
            target_size = (int(w), int(h))
            print(f"Will resize sprites to: {target_size[0]}x{target_size[1]} ({args.resize_mode} mode)")
        except:
            print(f"Invalid resize format: {args.resize}. Use WIDTHxHEIGHT (e.g., 64x64)")
            sys.exit(1)
    
    # Extract and save sprites
    mode_str = "PRECISE" if args.precise else "aggressive"
    print(f"\nExtracting sprites to: {output_dir}/ (mode: {mode_str})")
    for i, bbox in enumerate(bboxes):
        sprite = extract_sprite(img, bbox, bg_color, args.tolerance, precise_mode=args.precise)
        original_size = f"{sprite.width}x{sprite.height}"
        
        # Resize if requested
        if target_size:
            sprite = resize_sprite(sprite, target_size, args.resize_mode)
        
        filename = f"{args.prefix}_{i+1:03d}.png"
        filepath = output_dir / filename
        sprite.save(filepath, "PNG")
        
        size_info = f"{original_size} → {sprite.width}x{sprite.height}" if target_size else f"{sprite.width}x{sprite.height}"
        print(f"  [{i+1:3d}] {filename} - {size_info} px")
    
    print(f"\n✅ Done! Extracted {len(bboxes)} sprites to {output_dir}/")
    
    # Create a preview grid
    print("\nSprite summary:")
    for i, bbox in enumerate(bboxes):
        x1, y1, x2, y2 = bbox
        print(f"  {i+1:3d}: pos=({x1:4d},{y1:4d}) size={x2-x1:3d}x{y2-y1:3d}")


if __name__ == "__main__":
    main()
