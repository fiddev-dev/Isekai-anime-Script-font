#!/usr/bin/env python3
"""
Image to Font Converter
Converts a folder of character glyph images (PNG/JPG) into a TrueType Font (TTF) file.
Automatically parses filenames matching the React language application naming convention:
- A_symbol.png -> Uppercase 'A' (Unicode 65)
- A_lower_symbol.png -> Lowercase 'a' (Unicode 97)
- 0_symbol.png -> Digit '0' (Unicode 48)
- A_third_symbol.png -> Private Use Area 'A' (Unicode 0xE041)
- uni_XXXX_symbol.png -> Unicode point XXXX
"""

import os
import sys
import argparse
import logging
import cv2
import numpy as np
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ImageToFont")


def parse_filename_to_unicode(filename: str) -> int:
    """Parses a filename to its corresponding Unicode codepoint based on naming conventions."""
    basename = os.path.splitext(filename)[0]
    
    # 1. Unicode format (e.g. uni_003f_symbol)
    if basename.startswith("uni_"):
        parts = basename.split("_")
        try:
            return int(parts[1], 16)
        except (ValueError, IndexError):
            pass

    # 2. Third level symbols (e.g. A_third_symbol)
    if "_third_symbol" in basename:
        char_part = basename.replace("_third_symbol", "")
        if len(char_part) == 1 and char_part.isalpha():
            # Map third-level symbols to Private Use Area (starting at 0xE000)
            return 0xE000 + ord(char_part.upper())

    # 3. Lowercase symbols (e.g. A_lower_symbol)
    if "_lower_symbol" in basename:
        char_part = basename.replace("_lower_symbol", "")
        if len(char_part) == 1 and char_part.isalpha():
            return ord(char_part.lower())

    # 4. Standard symbols (e.g. A_symbol, 0_symbol)
    if "_symbol" in basename:
        char_part = basename.replace("_symbol", "")
        if len(char_part) == 1:
            return ord(char_part)

    # 5. Simple fallback (e.g. A.png -> 65, a.png -> 97)
    if len(basename) == 1:
        return ord(basename)

    return None


def get_signed_area(pts) -> float:
    """Calculates the signed area of a polygon. 
    In a system where Y goes up (font space):
    - Negative area = Clockwise (outer contour)
    - Positive area = Counter-clockwise (inner hole)
    """
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return area / 2.0


def extract_contours_from_image(img_path: str, threshold_val: int = 127):
    """Reads an image (handling transparency), binarizes it, and extracts outlines + hierarchy."""
    # Read image including alpha channel if present
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not load image: {img_path}")

    # Handle transparent background
    if len(img.shape) == 3 and img.shape[2] == 4:
        # Separate channels
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
        
        # Convert BGR to grayscale
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        
        # Binarize: text should be white (255), background black (0)
        _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY_INV)
        
        # Mask with alpha channel to ensure transparent pixels are black
        binary = cv2.bitwise_and(binary, alpha)
    else:
        # Grayscale or RGB
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        # Binarize assuming black/dark text on white background
        _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY_INV)

    # Find contours with hierarchy (RETR_CCOMP finds outer boundaries and 1-level holes inside them)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    return contours, hierarchy, binary.shape


def main():
    parser = argparse.ArgumentParser(
        description="Convert a folder of character images into a TrueType Font (TTF) file."
    )
    parser.add_argument(
        "-i", "--input-dir", 
        required=True, 
        help="Directory containing the character images."
    )
    parser.add_argument(
        "-o", "--output-font", 
        required=True, 
        help="Output path for the generated TTF file (e.g. output/myfont.ttf)."
    )
    parser.add_argument(
        "-n", "--name", 
        default="CustomFont", 
        help="Font family name."
    )
    parser.add_argument(
        "--em-size", 
        type=int, 
        default=1000, 
        help="Grid units per em (UPM) (default: 1000)."
    )
    parser.add_argument(
        "--ascent", 
        type=int, 
        default=800, 
        help="Ascent height in font units (default: 800)."
    )
    parser.add_argument(
        "--descent", 
        type=int, 
        default=-200, 
        help="Descent depth in font units (default: -200)."
    )
    parser.add_argument(
        "--side-bearing", 
        type=int, 
        default=80, 
        help="Padding added to the left and right of each glyph in font units (default: 80)."
    )
    parser.add_argument(
        "--spacing", 
        choices=["proportional", "fixed"], 
        default="proportional", 
        help="Spacing mode: 'proportional' (variable widths based on character size) or 'fixed' (monospaced)."
    )
    parser.add_argument(
        "--threshold", 
        type=int, 
        default=127, 
        help="Binarization threshold for images (default: 127)."
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    # Collect images and map them to unicode points
    unicode_mappings = {}
    for filename in os.listdir(args.input_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            codepoint = parse_filename_to_unicode(filename)
            if codepoint is not None:
                img_path = os.path.join(args.input_dir, filename)
                unicode_mappings[codepoint] = img_path

    if not unicode_mappings:
        logger.error("No valid character images found in the input directory.")
        sys.exit(1)

    # Automatically map uppercase symbols to lowercase, and vice versa, if only one case is provided.
    case_fallback_mappings = {}
    for codepoint, img_path in unicode_mappings.items():
        if 65 <= codepoint <= 90:  # A-Z
            lower_cp = codepoint + 32
            if lower_cp not in unicode_mappings:
                case_fallback_mappings[lower_cp] = img_path
        elif 97 <= codepoint <= 122:  # a-z
            upper_cp = codepoint - 32
            if upper_cp not in unicode_mappings:
                case_fallback_mappings[upper_cp] = img_path
    
    if case_fallback_mappings:
        logger.info(f"Adding {len(case_fallback_mappings)} case-fallback mappings for missing cases.")
        unicode_mappings.update(case_fallback_mappings)

    logger.info(f"Found {len(unicode_mappings)} mapped characters in: {args.input_dir}")

    # Initialize FontBuilder
    fb = FontBuilder(args.em_size, isTTF=True)

    # Set up glyph names and mapping dictionary
    glyph_names = [".notdef", ".null", "space"]
    cmap = {
        0x0000: ".null",
        0x0020: "space"
    }

    # Add characters to mappings
    for codepoint in sorted(unicode_mappings.keys()):
        # Name the glyph by its character or unicode hex
        try:
            char_str = chr(codepoint)
            if char_str.isalnum():
                glyph_name = f"glyph_{char_str}"
            else:
                glyph_name = f"uni_{codepoint:04X}"
        except ValueError:
            glyph_name = f"uni_{codepoint:04X}"
            
        glyph_names.append(glyph_name)
        cmap[codepoint] = glyph_name

    fb.setupGlyphOrder(glyph_names)
    fb.setupCharacterMap(cmap)

    # Dictionary to store generated glyph objects and metrics (glyphName -> (advance_width, lsb))
    glyphs = {}
    advance_widths = {
        ".notdef": (600, 100),
        ".null": (0, 0),
        "space": (int(args.em_size * 0.3), 0)  # space width is 30% of EM size
    }

    # 1. Create .notdef glyph (default box with an inner hole)
    pen = TTGlyphPen(None)
    # Outer box
    pen.moveTo((100, 0))
    pen.lineTo((100, args.ascent))
    pen.lineTo((500, args.ascent))
    pen.lineTo((500, 0))
    pen.closePath()
    # Inner hole (reverse winding for hole)
    pen.moveTo((150, 50))
    pen.lineTo((450, 50))
    pen.lineTo((450, args.ascent - 50))
    pen.lineTo((150, args.ascent - 50))
    pen.closePath()
    glyphs[".notdef"] = pen.glyph()

    # 2. Create .null glyph (empty)
    pen = TTGlyphPen(None)
    glyphs[".null"] = pen.glyph()

    # 3. Create space glyph (empty but has width)
    pen = TTGlyphPen(None)
    glyphs["space"] = pen.glyph()

    # 4. Generate glyphs from images
    for codepoint, img_path in sorted(unicode_mappings.items()):
        glyph_name = cmap[codepoint]
        try:
            contours, hierarchy, shape = extract_contours_from_image(img_path, args.threshold)
            h_img, w_img = shape[:2]
            
            # Scale factor to map image grid to Font Em square
            scale = args.em_size / h_img
            
            # First pass: Extract raw coordinates in font space
            font_contours = []
            for i, cnt in enumerate(contours):
                # OpenCV hierarchy: [Next, Previous, First Child, Parent]
                # parent index is hierarchy[0][i][3]
                parent_idx = hierarchy[0][i][3] if hierarchy is not None else -1
                
                # Filter out extremely small noise contours (less than 3 points or area < 4 pixels)
                if len(cnt) < 3 or cv2.contourArea(cnt) < 4:
                    continue

                # Transform coordinates
                pts = []
                for pt in cnt:
                    x_img, y_img = pt[0][0], pt[0][1]
                    
                    # Flip Y-axis (OpenCV Y goes down, Font Y goes up)
                    x_font = int(round(x_img * scale))
                    y_font = int(round((h_img - y_img) * scale + args.descent))
                    pts.append((x_font, y_font))
                
                font_contours.append({
                    "points": pts,
                    "is_hole": (parent_idx != -1)
                })

            # Find bounding box in font coordinates to calculate advance width and LSB alignment
            all_x = [pt[0] for fc in font_contours for pt in fc["points"]]
            
            if all_x:
                min_x = min(all_x)
                max_x = max(all_x)
                bbox_w = max_x - min_x
                
                if args.spacing == "proportional":
                    # Shift points to match the desired side bearing
                    shift_x = args.side_bearing - min_x
                    advance_width = bbox_w + (2 * args.side_bearing)
                else:  # fixed (monospaced)
                    # Center the character inside the EM square width
                    shift_x = (args.em_size - bbox_w) // 2 - min_x
                    advance_width = args.em_size

                # Draw to Pen with proper winding direction
                pen = TTGlyphPen(None)
                for fc in font_contours:
                    # Apply shift
                    shifted_pts = [(pt[0] + shift_x, pt[1]) for pt in fc["points"]]
                    
                    # Winding correction (TrueType: Outer contours = Clockwise [area < 0], Holes = Counter-Clockwise [area > 0])
                    area = get_signed_area(shifted_pts)
                    if fc["is_hole"]:
                        # Wants counter-clockwise (area > 0)
                        if area < 0:
                            shifted_pts.reverse()
                    else:
                        # Wants clockwise (area < 0)
                        if area > 0:
                            shifted_pts.reverse()
                            
                    # Draw polygon
                    pen.moveTo(shifted_pts[0])
                    for pt in shifted_pts[1:]:
                        pen.lineTo(pt)
                    pen.closePath()
                    
                glyphs[glyph_name] = pen.glyph()
                advance_widths[glyph_name] = (int(advance_width), int(shift_x + min_x))
            else:
                # No contours (empty character image, or completely white)
                pen = TTGlyphPen(None)
                glyphs[glyph_name] = pen.glyph()
                advance_widths[glyph_name] = (int(args.em_size * 0.3), 0)
                
        except Exception as e:
            logger.error(f"Failed to process character '{chr(codepoint)}' (Unicode: U+{codepoint:04x}): {e}")
            # Fallback to empty glyph
            pen = TTGlyphPen(None)
            glyphs[glyph_name] = pen.glyph()
            advance_widths[glyph_name] = (600, 0)

    # 5. Build and save the font
    logger.info("Assembling font tables...")
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(advance_widths)
    fb.setupHorizontalHeader(ascent=args.ascent, descent=args.descent)
    
    # Metadata Name Table
    name_strings = {
        "familyName": args.name,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{args.name}-Regular",
        "fullName": args.name,
        "psName": f"{args.name}-Regular",
    }
    fb.setupNameTable(name_strings)
    fb.setupOS2(
        sTypoAscender=args.ascent,
        sTypoDescender=args.descent,
        usWinAscent=args.ascent,
        usWinDescent=abs(args.descent)
    )
    fb.setupPost()

    # Save TTF file
    os.makedirs(os.path.dirname(os.path.abspath(args.output_font)), exist_ok=True)
    fb.save(args.output_font)
    logger.info(f"Successfully compiled and saved TTF font to: {args.output_font}")


if __name__ == "__main__":
    main()
