#!/usr/bin/env python3.10
"""Scan OCR text to detect Unit boundaries and Topic subsections.

Strategy:
  - A unit's *start page* is the standalone "Unit N" title page detected
    by a short, early-in-page "Unit N" or "Unit N <title>" line.
  - A unit's *title* comes from the (greedy) footer pattern seen on
    inside pages: "Math 4/Math 4 ADV Unit N: <Title> <printed-page>".
  - Topic subsections are "Topic: <name>" lines encountered inside each
    unit's page range.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR_JSON = ROOT / "pages" / "ocr.json"
OUT = ROOT / "chapters.json"

FOOTER_RE = re.compile(
    r"Math\s*[4A]\s*[/\\]?\s*Math\s*[4A]\s*ADV\s*Unit\s*(\d{1,2})\s*[:;.-]?\s*(.+?)(?:\s+\d{1,3})?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
# Title page: an early line that is just "Unit N" or "Unit N <Title>"
UNIT_TITLE_RE = re.compile(r"^\s*Unit\s+(\d{1,2})\b\s*(.{0,60})?\s*$", re.IGNORECASE)
TOPIC_RE = re.compile(r"^\s*Topic\s*[:;]\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().rstrip(" .,:;-")


def main() -> int:
    ocr = json.loads(OCR_JSON.read_text())

    # 1) Learn each unit's title from footers (greedy match keeps "Part N")
    unit_title: dict[int, str] = {}
    for entry in ocr:
        text = entry.get("text", "") or ""
        for m in FOOTER_RE.finditer(text):
            n = int(m.group(1))
            t = clean(m.group(2))
            # keep the longest non-empty title we see for each unit
            if t and len(t) > len(unit_title.get(n, "")):
                unit_title[n] = t

    # 2) Find each unit's actual start page from body "Unit N" lines
    unit_start: dict[int, int] = {}
    for entry in ocr:
        page = entry["page"]
        text = entry.get("text", "") or ""
        # Only look at the first ~12 non-empty lines of the page body
        lines = [ln for ln in text.splitlines() if ln.strip()][:12]
        for ln in lines:
            m = UNIT_TITLE_RE.match(ln)
            if not m:
                continue
            n = int(m.group(1))
            # ignore obvious noise like "Unit 1 Building Community..." in a mid-paragraph
            # by requiring the line to be short-ish
            if len(ln.strip()) > 60:
                continue
            # keep the EARLIEST page where we saw this body marker
            if n not in unit_start or page < unit_start[n]:
                unit_start[n] = page
            break  # one match per page is enough

    # Sanity: for each unit found in titles but missing a start, fall back to the earliest footer page
    footer_first: dict[int, int] = {}
    for entry in ocr:
        text = entry.get("text", "") or ""
        for m in FOOTER_RE.finditer(text):
            n = int(m.group(1))
            if n not in footer_first or entry["page"] < footer_first[n]:
                footer_first[n] = entry["page"]
    for n in unit_title:
        unit_start.setdefault(n, footer_first.get(n, 1))

    # 3) Collect topic subsections
    topics_by_page: list[tuple[int, str]] = []
    for entry in ocr:
        text = entry.get("text", "") or ""
        for tm in TOPIC_RE.finditer(text):
            t = clean(tm.group(1))
            if 3 <= len(t) <= 80 and not t.lower().startswith(("math 4", "unit")):
                topics_by_page.append((entry["page"], t))

    # 4) Build chapters, bounding topic ranges by next unit start
    unit_nums = sorted(unit_start)
    chapters = []
    total_pages = max(e["page"] for e in ocr)
    for i, n in enumerate(unit_nums):
        start = unit_start[n]
        end = unit_start[unit_nums[i + 1]] - 1 if i + 1 < len(unit_nums) else total_pages
        title = unit_title.get(n, "").strip()
        label = f"Unit {n}: {title}" if title else f"Unit {n}"
        subs: list[dict] = []
        seen = set()
        for p, t in topics_by_page:
            if start <= p <= end:
                key = t.lower()
                if key in seen:
                    continue
                seen.add(key)
                subs.append({"title": f"Topic: {t}", "page": p})
        chapters.append({"title": label, "page": start, "subsections": subs})

    OUT.write_text(json.dumps({"chapters": chapters}, indent=2))
    print(f"wrote {OUT} with {len(chapters)} chapters, {sum(len(c['subsections']) for c in chapters)} subsections")
    for c in chapters:
        print(f"  p{c['page']:>3}  {c['title']}  ({len(c['subsections'])} topics)")
        for s in c["subsections"]:
            print(f"         p{s['page']:>3}  {s['title']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
