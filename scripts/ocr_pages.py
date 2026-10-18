#!/usr/bin/env python3.10
"""OCR every page JPEG with tesseract, writing pages/ocr/page_NNN.txt
and pages/ocr.json (one entry per page with normalized text).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"
OCR_DIR = PAGES / "ocr"


def ocr_one(jpg: Path, out_txt: Path) -> str:
    # tesseract <input> <output-base> — produces <output-base>.txt
    base = out_txt.with_suffix("")
    subprocess.run(
        ["tesseract", str(jpg), str(base), "-l", "eng", "--psm", "3"],
        check=True,
        capture_output=True,
    )
    return out_txt.read_text(errors="replace")


def normalize(text: str) -> str:
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> int:
    if not PAGES.exists():
        print(f"pages dir not found: {PAGES}", file=sys.stderr)
        return 1
    OCR_DIR.mkdir(exist_ok=True)

    manifest = json.loads((PAGES / "manifest.json").read_text())
    out = []
    for entry in manifest:
        n = entry["page"]
        jpg = PAGES / entry["file"]
        txt = OCR_DIR / f"page_{n:03d}.txt"
        if not txt.exists():
            try:
                ocr_one(jpg, txt)
            except subprocess.CalledProcessError as e:
                print(f"[{n}] tesseract failed: {e.stderr.decode(errors='replace')[:200]}", file=sys.stderr)
                txt.write_text("")
        text = normalize(txt.read_text(errors="replace"))
        out.append({"page": n, "file": entry["file"], "source": entry["source"], "text": text})
        print(f"[{n}/{len(manifest)}] {len(text)} chars")

    (PAGES / "ocr.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote ocr.json with {len(out)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
