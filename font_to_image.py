#!/usr/bin/env python3
"""
Font to Image Converter
Converts a TrueType Font (TTF) file into a folder of character glyph images.
Supports the standard naming conventions expected by image_to_font.py:
- A-Z -> [Char]_symbol.png
- a-z -> [Char_Upper]_lower_symbol.png
- 0-9 -> [Digit]_symbol.png
- PUA 0xE041-0xE05A -> [Char]_third_symbol.png
- Other -> uni_[hex]_symbol.png
"""

import os
import sys
import argparse
import logging
from PIL import Image, ImageDraw, ImageFont, ImageOps
from fontTools.ttLib import TTFont

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FontToImage")

def parse_codepoint_to_filename(cp: int) -> str:
    """Maps a Unicode codepoint to its corresponding filename using project conventions."""
    if 65 <= cp <= 90:  # A-Z
        return f"{chr(cp)}_symbol.png"
    elif 97 <= cp <= 122:  # a-z
        return f"{chr(cp - 32)}_lower_symbol.png"
    elif 48 <= cp <= 57:  # 0-9
        return f"{chr(cp)}_symbol.png"
    elif 0xE041 <= cp <= 0xE05A:  # PUA mapped A-Z third symbols
        char_name = chr(cp - 0xE000)
        return f"{char_name}_third_symbol.png"
    else:
        # Ignore space, carriage return, non-breaking space, etc. from rendering if they are empty
        if cp in {0, 9, 10, 13, 32, 160}:
            return None
        return f"uni_{cp:04x}_symbol.png"

def render_character_to_image(font_path: str, char_str: str, target_size: int = 128, padding: int = 12) -> Image.Image:
    """Renders a character to a target_size x target_size image, centered and padded, using PIL."""
    # 1. Create a large temporary white canvas to render high resolution
    temp_size = target_size * 4  # 512 for target_size=128
    img = Image.new("RGB", (temp_size, temp_size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 2. Load the font at a large size
    font_size = int(temp_size * 0.75)  # 384 for temp_size=512
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logger.error(f"Error loading font for rendering: {e}")
        return None
        
    # 3. Draw character in center
    try:
        draw.text((temp_size // 2, temp_size // 2), char_str, fill=(0, 0, 0), font=font, anchor="mm")
    except ValueError:
        # Fallback if anchor is not supported in the PIL version
        draw.text((temp_size // 8, temp_size // 8), char_str, fill=(0, 0, 0), font=font)
        
    # 4. Find bounding box of the text glyph (black on white)
    gray = img.convert("L")
    inverted = ImageOps.invert(gray)
    bbox = inverted.getbbox()
    
    if bbox is None:
        # The glyph is empty (e.g. whitespace)
        return None
        
    # Crop the glyph from the large image
    glyph_img = img.crop(bbox)
    
    # 5. Calculate resize dimensions keeping aspect ratio
    w, h = glyph_img.size
    max_inner_size = target_size - (2 * padding)
    
    scale = min(max_inner_size / w, max_inner_size / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.ANTIALIAS
        
    resized_glyph = glyph_img.resize((new_w, new_h), resample_filter)
    
    # 6. Paste resized glyph onto final target_size x target_size canvas
    out_img = Image.new("RGB", (target_size, target_size), (255, 255, 255))
    x = (target_size - new_w) // 2
    y = (target_size - new_h) // 2
    out_img.paste(resized_glyph, (x, y))
    
    return out_img

def main():
    parser = argparse.ArgumentParser(
        description="Convert a TrueType Font (TTF) file into a folder of character glyph images."
    )
    parser.add_argument(
        "-f", "--font", 
        required=True, 
        help="Path to the input TTF font file."
    )
    parser.add_argument(
        "-o", "--output-dir", 
        required=True, 
        help="Output directory to save the character images."
    )
    parser.add_argument(
        "--size", 
        type=int, 
        default=128, 
        help="Target size (width and height) of the output images in pixels (default: 128)."
    )
    parser.add_argument(
        "--padding", 
        type=int, 
        default=12, 
        help="Padding/margin inside the output images in pixels (default: 12)."
    )

    args = parser.parse_args()

    if not os.path.exists(args.font):
        logger.error(f"Font file does not exist: {args.font}")
        sys.exit(1)

    # Load font using fontTools to inspect cmap
    try:
        ttfont = TTFont(args.font)
        cmap = ttfont.getBestCmap()
    except Exception as e:
        logger.error(f"Failed to parse font with fontTools: {e}")
        sys.exit(1)

    if not cmap:
        logger.error("No character map found in font.")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    logger.info(f"Loaded font '{args.font}' containing {len(cmap)} mapped characters.")

    success_count = 0
    skipped_count = 0

    for cp in sorted(cmap.keys()):
        filename = parse_codepoint_to_filename(cp)
        if not filename:
            # Skip space/controls
            skipped_count += 1
            continue

        try:
            char_str = chr(cp)
        except ValueError:
            logger.warning(f"Skipping invalid codepoint: {cp}")
            skipped_count += 1
            continue

        # Render glyph to image
        img = render_character_to_image(args.font, char_str, target_size=args.size, padding=args.padding)
        if img is None:
            # Empty glyph
            logger.info(f"Skipping empty glyph for codepoint U+{cp:04X} ({filename})")
            skipped_count += 1
            continue

        output_path = os.path.join(args.output_dir, filename)
        img.save(output_path, "PNG")
        success_count += 1

    logger.info(f"Generated {success_count} character images in: {args.output_dir}")
    logger.info(f"Skipped {skipped_count} character(s) (empty, control, or space characters).")

if __name__ == "__main__":
    main()
