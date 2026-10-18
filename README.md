# Sheenaz Math 4th Grade — Digital Workbook

A standalone browser-based viewer for the FCPS Math 4 / Math 4 ADV Student Workbook, built from photos of the printed book.

## Features

- 245 pages, viewable in any browser
- **Arrow keys** or on-screen buttons for prev/next
- **Chapter dropdown** + sidebar table of contents (10 Units with subsections)
- **Full-text search** across all pages (OCR'd with tesseract)
- **Jump to page** by number
- **Zoom** and per-page rotate (`r` / `Shift+R`) with rotations saved in your browser
- Current page reflected in URL (`?p=42`) so you can bookmark or share

## Run it locally

```bash
python3 -m http.server 8765
# then open http://localhost:8765/
```

Or just open `index.html` directly in a browser if your browser allows loading JSON over `file://` (most don't; the server is simpler).

## Rebuilding from source images (optional)

If you have the source HEIC images in `Sheenaz-math-4th-grade/`:

```bash
python3 scripts/convert_heic.py     # HEIC -> JPEG, auto-orient landscape pages
python3 scripts/ocr_pages.py        # tesseract OCR -> pages/ocr.json
python3 scripts/build_chapters.py   # scan OCR for Unit boundaries -> chapters.json
```

Dependencies: `pip install pillow pillow-heif` and `tesseract-ocr` installed on the system.

## Edit the index

`chapters.json` is a plain JSON file — rename, reorder, add, or remove any chapter/subsection and the viewer picks it up on reload.
