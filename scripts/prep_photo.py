"""
prep_photo.py
- Reads source-photo.jpg from the repo root
- Removes background with rembg
- Applies CLAHE via OpenCV for contrast enhancement
- Composites result onto a pure-white background
- Outputs source-prepped.png in the repo root
"""

import pathlib
import sys
import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "source-photo.jpg"
OUT = ROOT / "source-prepped.png"


def remove_background(img_pil: Image.Image) -> Image.Image:
    """Strip background using rembg; returns RGBA image."""
    return remove(img_pil)


def apply_clahe(img_pil: Image.Image) -> Image.Image:
    """
    Apply CLAHE to the L channel of the image for contrast enhancement.
    Works on RGBA: extracts RGB, applies CLAHE in LAB space, merges alpha back.
    """
    rgba = np.array(img_pil)  # H x W x 4
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_chan = clahe.apply(l_chan)

    lab_merged = cv2.merge([l_chan, a_chan, b_chan])
    rgb_enhanced = cv2.cvtColor(lab_merged, cv2.COLOR_LAB2RGB)

    result = np.dstack([rgb_enhanced, alpha])
    return Image.fromarray(result, mode="RGBA")


def composite_on_white(img_pil: Image.Image) -> Image.Image:
    """Alpha-composite the RGBA image onto a pure-white background."""
    white = Image.new("RGBA", img_pil.size, (255, 255, 255, 255))
    white.paste(img_pil, mask=img_pil.split()[3])
    return white.convert("RGB")


def main():
    if not SRC.exists():
        print(f"ERROR: {SRC} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {SRC} …")
    src_img = Image.open(SRC).convert("RGBA")

    print("Removing background …")
    no_bg = remove_background(src_img)

    print("Applying CLAHE …")
    enhanced = apply_clahe(no_bg)

    print("Compositing onto white …")
    final = composite_on_white(enhanced)

    final.save(OUT, "PNG")
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    main()
