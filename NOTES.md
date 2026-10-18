# Sheenaz Math 4th Grade — Build Notes

Full chronology of how this project was built, what decisions were made, and
how to extend or repeat the process.

Date built: **2026-10-17**
Final site: **https://sujan00-git.github.io/Sheenaz-math-4thgrade/**
Repo: **https://github.com/sujan00-git/Sheenaz-math-4thgrade**

---

## Goal

Turn a stack of iPhone photos of a 4th-grade math workbook (shared via a Google
Drive folder) into a browser-based digital book with:

- Forward / backward page navigation (buttons + keyboard arrows)
- A clickable index/table of contents with chapters and subsections
- A chapter dropdown for quick jumps
- Full-text search that jumps to the page containing a keyword
- Direct jump by page number

## Final feature set

| Feature | How |
|---|---|
| Prev / Next | ◀ / ▶ buttons, `←` `→` arrows, `Space`, `PageUp` / `PageDown`, `Home` / `End` |
| Chapter nav | Top-bar dropdown + sidebar TOC with 10 Units and their topic subsections |
| Full-text search | Searches `pages/ocr.json`; shows a snippet with hits; typing a number alone jumps directly to that page; `/` focuses the search box |
| Zoom | − / 100% / + buttons |
| Rotate single page | ↺ / ↻ buttons, `r` / `Shift+R`; persists in `localStorage` so it sticks |
| Deep-link to page | URL `?p=42` reflects current page |
| Current chapter highlight | Active chapter/subsection highlights in sidebar as you page through |

---

## Pipeline (what each script does)

```
Sheenaz-math-4th-grade/*.HEIC   (iPhone photos, 553 MB, 244 files)
            │
            ▼  scripts/convert_heic.py
pages/page_NNN.jpg              (JPEG, resized to 1600 px wide, auto-oriented)
pages/manifest.json             ([{page,source,file}, …])
            │
            ▼  scripts/ocr_pages.py
pages/ocr/page_NNN.txt          (per-page OCR text)
pages/ocr.json                  ([{page,file,source,text}, …])
            │
            ▼  scripts/build_chapters.py   (one-shot auto-detector; final chapters.json was hand-cleaned)
chapters.json                   ({chapters:[{title,page,subsections:[…]}, …]})
            │
            ▼  index.html
http://localhost:8765/          (viewer)
```

Dependencies:

```bash
sudo apt-get install -y tesseract-ocr
pip install --user pillow pillow-heif gdown
```

---

## Build chronology (what we actually hit)

### 1. Getting the photos

- Tried `gdown --folder <share-link>`: hit Google Drive's anonymous-download
  quota at page 105 of 275. Many "Cannot retrieve the public link" errors.
- Tried Drive's "Download folder" (ZIP) via browser: Drive produced a 234-byte
  stub containing only the folder entry (empty). May have been a transient
  Drive-side failure.
- **Worked**: user copied the HEIC files directly from Windows Explorer
  (`\\wsl.localhost\Ubuntu-22.04\home\...`) into the project folder. 244 HEICs
  from `IMG_1120.HEIC` to `IMG_1394.HEIC` with a few gaps.

### 2. HEIC → JPEG + resize

- Browsers can't display HEIC. Used `pillow-heif` to decode, Pillow to resize
  to 1600 px wide and save as JPEG q=85 → **245 JPEGs, 70 MB total**.
- Numbering: `page_001.jpg` … `page_245.jpg` by sorted source filename.

### 3. Orientation fix (big round of surgery)

- First pass: EXIF orientation was `1` on every file — so no automatic rotation
  was applied. But pixel dimensions differed: 177 portrait (4284×5712),
  67 landscape (5712×4284). Phone was turned sideways for some shots.
- Added `auto_rotate()` using tesseract OSD (`--psm 0`) which reads text
  direction, rotates the image to match. Fell back to 90° CCW when OSD was
  undecided.
- After auto-rotate: 240/245 portrait, 5 stragglers (74, 84, 90, 92, 99)
  where OSD was confidently wrong — force-rotated those 90° CW.
- User reported another 13 pages upside-down (180°): 9, 10, 11, 29, 36, 72,
  82, 83, 85, 98, 102, 140, 141 — rotated each 180° and re-OCR'd just those.
- Also added **per-page rotate buttons** to the viewer so any future surprise
  can be fixed in-browser (persisted to `localStorage`).

### 4. OCR

- Tesseract 4.1.1, `--psm 3`, English. ~150 KB of text indexed, ~245
  per-page txt files kept locally (gitignored).
- Rebuilt `ocr.json` after each rotation fix so search stayed accurate.

### 5. Chapter index

- First tried fully-automatic: regex-scraped page footers
  (`Math 4/Math 4 ADV Unit N: <Title> <printed-page>`) and body "Unit N" lines.
- Issues:
  - Non-greedy regex ate "Part 1/2/3" out of titles ("Fractions Part" instead
    of "Fractions Part 1"). Fixed by making the title match greedy.
  - Book printing bug: pages 182–206 are Unit 8 (Geometry) in the body but
    carry a Unit 9 (Measurement) footer. Had to prefer body "Unit N" markers
    over footers.
  - Unit 9 Measurement body title actually appears on page 207, not 182.
- Final `chapters.json` was hand-written using the auto-detection as a draft:
  10 Units + Front Matter + Attribution sections, each with 2–5 topic
  subsections at verified page numbers.

### 6. Viewer

- `index.html` — single file, no build step. Vanilla JS, CSS variables for
  light/dark auto. Grid layout: 48 px top bar, 300 px sidebar, main area.
- Loads `pages/manifest.json`, `pages/ocr.json`, `chapters.json` on boot.
- All search / navigation / rotate state kept in memory + optional localStorage
  for rotations.

### 7. Privacy pass (before publishing)

- Searched OCR for occurrences of the student and teacher name — only the
  cover (page 1) contained them.
- Pixelated the handwritten names on `page_001.jpg` using a 28-px block
  (unrecoverable at this resolution). Kept the original cover as
  `page_001.original.jpg` locally for rollback (gitignored).
- Re-OCR'd page 1: zero occurrences of names in search index. Verified by
  grepping all pages for "sheenaz", "rahman", "hayles", "watson" — all 0.

### 8. Publish to GitHub

- `gh repo create` as **public** under `sujan00-git/Sheenaz-math-4thgrade`.
- Enabled GitHub Pages from `main` branch, `/` path.
- Site URL: **https://sujan00-git.github.io/Sheenaz-math-4thgrade/**

---

## What ended up in git (and what didn't)

**Tracked (254 files, 77 MB):**

- `index.html`, `README.md`, `NOTES.md`, `.gitignore`
- `chapters.json`
- `pages/page_001.jpg` … `pages/page_245.jpg`
- `pages/manifest.json`, `pages/ocr.json`
- `scripts/convert_heic.py`, `scripts/ocr_pages.py`, `scripts/build_chapters.py`

**Excluded via `.gitignore`:**

- `Sheenaz-math-4th-grade/` — 553 MB of HEIC source photos
- `pages/page_001.original.jpg` — unredacted cover (local rollback only)
- `pages/ocr/` — per-page OCR text (regenerable from JPEGs)
- `*:Zone.Identifier`, `*:sec.endpointdlp` — WSL/Windows file-stream metadata
- `*.zip`, `__pycache__/`, `.venv/`, `.claude/`, OS/editor junk

---

## Rebuilding / updating

### Reproduce the whole book from scratch

Assuming `Sheenaz-math-4th-grade/*.HEIC` exists:

```bash
python3 scripts/convert_heic.py       # HEIC -> JPEG w/ auto-orient
python3 scripts/ocr_pages.py          # per-page OCR + ocr.json
python3 scripts/build_chapters.py     # auto-detect chapters (overwrite chapters.json)
```

### Add new pages later

1. Drop new `IMG_*.HEIC` into `Sheenaz-math-4th-grade/`.
2. Delete `pages/` and `pages/ocr/` to force a rebuild (or edit
   `convert_heic.py` to append).
3. Re-run the three scripts above.
4. Hand-edit `chapters.json` if any new chapter boundaries moved.
5. `git add -A && git commit -m "add pages …" && git push`

### Fix a single rotated page

- In the viewer: open the page, click ↺ or ↻ (or `r` / `Shift+R`). Saved in
  your browser's localStorage. Does NOT change the file on GitHub.
- Permanent fix: `python3 -c "from PIL import Image; Image.open('pages/page_NNN.jpg').rotate(-90, expand=True).save('pages/page_NNN.jpg')"`
  then `git commit && git push`.

### Redact additional pages

```python
from PIL import Image
im = Image.open('pages/page_NNN.jpg').convert('RGB')
box = (x1, y1, x2, y2)   # pixel coords
w, h = box[2]-box[0], box[3]-box[1]
region = im.crop(box)
small = region.resize((max(1,w//28), max(1,h//28)), Image.NEAREST)
im.paste(small.resize((w, h), Image.NEAREST), box)
im.save('pages/page_NNN.jpg', 'JPEG', quality=85, optimize=True)
```

Then re-OCR just that page and rebuild `ocr.json`:

```bash
cd pages/ocr && rm -f page_NNN.txt && tesseract ../page_NNN.jpg page_NNN -l eng --psm 3
# regenerate ocr.json from per-page txt files (see scripts/ocr_pages.py)
```

---

## Shortcuts cheat sheet

| Key | Action |
|---|---|
| `←` / `PageUp` | Previous page |
| `→` / `PageDown` / `Space` | Next page |
| `Home` / `End` | First / last page |
| `/` | Focus search box |
| `r` / `Shift+R` | Rotate current page 90° CCW / CW |
| `Esc` | Close search results |

---

## Known limitations / future ideas

- **OCR quality** on handwritten portions is low. Tesseract was tuned for
  printed text; the printed workbook content is well-indexed but her
  handwritten answers mostly aren't.
- **No two-page spread view.** Could add — toggle a `pair` mode that shows
  pages N and N+1 side by side.
- **No annotations.** If you want highlights or sticky notes, add a JSON
  overlay keyed by page number.
- **Chapters are hand-maintained** in `chapters.json`. `build_chapters.py`
  can regenerate a rough draft but will miss some subsections.

---

## File index at a glance

```
/
├─ index.html               ← the viewer
├─ chapters.json            ← table of contents
├─ README.md                ← user-facing README
├─ NOTES.md                 ← this file
├─ .gitignore
├─ pages/
│  ├─ page_001.jpg … page_245.jpg
│  ├─ manifest.json         ← page order + source filenames
│  └─ ocr.json              ← per-page OCR text (search index)
└─ scripts/
   ├─ convert_heic.py       ← HEIC → JPEG + auto-orient
   ├─ ocr_pages.py          ← tesseract batch OCR
   └─ build_chapters.py     ← auto-detect chapter structure
```
