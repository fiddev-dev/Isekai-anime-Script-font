#!/usr/bin/env python3
"""
Font Batch Generator
Scans the 'alfabet_image' directory, generates TTF fonts for each sub-folder
using 'image_to_font.py', and places the results in the 'font' directory.
Excludes: 'inazuma_languange_alfabet' and 'rezero_romaji_alphabet'.
"""

import os
import subprocess
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("BatchFontGenerator")

EXCLUDE_FOLDERS = {
    "inazuma_languange_alfabet",
    "rezero_romaji_alphabet"
}

def clean_font_name(folder_name: str) -> str:
    """Cleans up folder names into clean, readable Font Family Names."""
    # Special cleanups
    name = folder_name
    if "alphabetb-1024x856" in name:
        name = name.replace("alphabetb-1024x856", "Alphabet")
    
    name = name.replace("_", " ").replace("-", " ")
    
    # Standardize spelling
    name = name.replace("languange", "Language")
    name = name.replace("alfabet", "Alphabet")
    
    # Title Case each word
    words = [w.capitalize() for w in name.split()]
    return " ".join(words)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_base = os.path.join(base_dir, "alfabet_image")
    output_base = os.path.join(base_dir, "font")
    script_path = os.path.join(base_dir, "image_to_font.py")

    if not os.path.exists(input_base):
        logger.error(f"Input base directory 'alfabet_image' does not exist in: {base_dir}")
        sys.exit(1)

    os.makedirs(output_base, exist_ok=True)

    # Get all subdirectories
    subdirs = [
        d for d in os.listdir(input_base)
        if os.path.isdir(os.path.join(input_base, d))
    ]

    logger.info(f"Found {len(subdirs)} total directories in 'alfabet_image'.")

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for folder in sorted(subdirs):
        if folder in EXCLUDE_FOLDERS:
            logger.info(f"Skipping excluded directory: {folder}")
            skipped_count += 1
            continue

        input_dir = os.path.join(input_base, folder)
        # We can name the font file name as the folder name itself (or clean it a bit)
        # Let's keep it as folder_name.ttf for precise mapping, or clean it.
        # Keeping folder_name.ttf makes it extremely easy to refer to.
        output_font_name = f"{folder}.ttf"
        output_font_path = os.path.join(output_base, output_font_name)
        font_family = clean_font_name(folder)

        logger.info(f"Processing '{folder}' -> Font Family: '{font_family}'")
        
        cmd = [
            sys.executable,
            script_path,
            "-i", input_dir,
            "-o", output_font_path,
            "-n", font_family
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully generated font: {output_font_name}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate font for folder '{folder}':")
            logger.error(f"Command: {' '.join(cmd)}")
            logger.error(f"Stderr: {e.stderr}")
            logger.error(f"Stdout: {e.stdout}")
            failed_count += 1

    logger.info("==========================================")
    logger.info("Batch Generation Completed Summary:")
    logger.info(f"  Successfully Generated: {success_count} fonts")
    logger.info(f"  Skipped (Excluded): {skipped_count} folders")
    logger.info(f"  Failed: {failed_count} folders")
    logger.info("==========================================")

if __name__ == "__main__":
    main()
