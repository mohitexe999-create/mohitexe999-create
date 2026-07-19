#!/usr/bin/env python3
"""
prep_photo.py — Prepare a source photo for ASCII art conversion.

Steps:
  1. Remove background with rembg
  2. Boost local contrast with OpenCV CLAHE
  3. Composite onto pure white
  4. Save as grayscale source-prepped.png

Usage:
    python scripts/prep_photo.py [source-photo.jpg]
"""

import sys
import pathlib
import numpy as np
import cv2
from PIL import Image
from rembg import remove

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "source-photo.jpg"
OUTPUT = ROOT / "source-prepped.png"


def remove_background(img: Image.Image) -> Image.Image:
    """Remove background using rembg, return RGBA image."""
    return remove(img)


def boost_contrast(gray: np.ndarray) -> np.ndarray:
    """Apply CLAHE (contrast-limited adaptive histogram equalization)."""
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def composite_on_white(rgba: Image.Image) -> Image.Image:
    """Composite RGBA image onto a pure-white background, return grayscale."""
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composite = Image.alpha_composite(white, rgba)
    return composite.convert("L")


def main():
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    if not src.exists():
        print(f"[!] Source photo not found: {src}")
        print("    Place a photo at source-photo.jpg or pass a path as argument.")
        sys.exit(1)

    print(f"[1/4] Loading {src.name} ...")
    img = Image.open(src).convert("RGBA")

    print("[2/4] Removing background ...")
    no_bg = remove_background(img)

    print("[3/4] Compositing on white + converting to grayscale ...")
    gray_pil = composite_on_white(no_bg)

    print("[4/4] Boosting contrast with CLAHE ...")
    gray_np = np.array(gray_pil)
    enhanced = boost_contrast(gray_np)

    result = Image.fromarray(enhanced)
    result.save(OUTPUT)
    print(f"[OK] Saved {OUTPUT}")


if __name__ == "__main__":
    main()
