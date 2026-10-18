#!/usr/bin/env python3.10
"""Convert HEIC source images to web-friendly JPEGs, ordered by filename.

Output: pages/page_001.jpg, page_002.jpg, ...
Also writes pages/manifest.json: [{"page": 1, "source": "IMG_1120.HEIC"}, ...]
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageOps
import pillow_heif

pillow_heif.register_heif_opener()

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Sheenaz-math-4th-grade"
OUT = ROOT / "pages"
MAX_WIDTH = 1600  # resize to speed up load; adjust if detail is lost
JPEG_QUALITY = 85


OSD_ROTATE_RE = re.compile(r"Rotate:\s*(\d+)")


def _osd_rotation(im: Image.Image) -> int:
    """Return clockwise degrees tesseract thinks the image needs to be upright."""
    thumb = im.copy()
    thumb.thumbnail((1200, 1200))
    buf = io.BytesIO()
    thumb.save(buf, "PNG")
    try:
        out = subprocess.run(
            ["tesseract", "stdin", "stdout", "--psm", "0"],
            input=buf.getvalue(), capture_output=True, timeout=20,
        ).stdout.decode(errors="replace")
    except Exception:
        return 0
    m = OSD_ROTATE_RE.search(out)
    return int(m.group(1)) if m else 0


def auto_rotate(im: Image.Image) -> Image.Image:
    """Rotate a landscape page so text runs horizontally.

    Preference order:
      1. If tesseract OSD gives a confident rotation, apply it.
      2. Otherwise rotate 90° CCW (the most common iPhone landscape orientation
         when photographing a book held with the spine on the left).
    """
    deg = _osd_rotation(im)
    if deg in (0, 90, 180, 270) and deg != 0:
        # Pillow rotates counter-clockwise; OSD's "Rotate" is clockwise degrees needed.
        return im.rotate(-deg, expand=True)
    # OSD couldn't decide — default to 90° CCW
    return im.rotate(90, expand=True)


def main() -> int:
    if not SRC.exists():
        print(f"source not found: {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(exist_ok=True)

    srcs = sorted(
        p for p in SRC.iterdir()
        if p.suffix.lower() in {".heic", ".heif", ".jpg", ".jpeg", ".png"}
        and ":" not in p.name  # skip NTFS ADS entries that leak through on WSL
    )
    manifest = []
    for i, src in enumerate(srcs, start=1):
        dst = OUT / f"page_{i:03d}.jpg"
        if dst.exists():
            manifest.append({"page": i, "source": src.name, "file": dst.name})
            continue
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            # If landscape, pick the rotation that puts text upright via tesseract OSD.
            if im.width > im.height:
                im = auto_rotate(im)
            if im.width > MAX_WIDTH:
                h = int(im.height * MAX_WIDTH / im.width)
                im = im.resize((MAX_WIDTH, h), Image.LANCZOS)
            im.save(dst, "JPEG", quality=JPEG_QUALITY, optimize=True)
        manifest.append({"page": i, "source": src.name, "file": dst.name})
        print(f"[{i}/{len(srcs)}] {src.name} -> {dst.name} ({im.size[0]}x{im.size[1]})")

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nwrote {len(manifest)} pages and manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
