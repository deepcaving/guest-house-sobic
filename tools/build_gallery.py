#!/usr/bin/env python3
"""Build the photo gallery: copy the pictures in and write the markup.

    python3 tools/build_gallery.py <the folder with the extracted photos>

The folder is the one that came out of the photo pack Milka sent:

    unzip "Guest House Sobic, Sipovo (updated prices 2027).zip" -d photos

Every picture is there in two sizes - "<id>.jpg" (large) and
"<id> (1).jpg" (small). The small one goes in the grid and on the phone,
the large one is what the visitor sees when a photo is opened.

The gallery markup is written between the markers in index.html, so the
order and the alt texts live in tools/gallery_photos.py and nowhere
else. Run this after changing that file.
"""

import html
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gallery_photos import PHOTOS  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
IMG = REPO / "img" / "photos"
INDEX = REPO / "index.html"

START = "    <!-- GALLERY:START -->"
END = "    <!-- GALLERY:END -->"


def find_pair(folder, photo_id):
    """The small and the large version of one picture."""
    small = large = None
    for name in os.listdir(folder):
        if not name.lower().endswith((".jpg", ".jpeg")):
            continue
        m = re.match(r"^(.*?)(?:\s*\((\d+)\))?(\.\w+)$", name)
        if not m or m.group(1) != photo_id:
            continue
        path = Path(folder) / name
        size = path.stat().st_size
        if small is None or size < small[1]:
            small = (path, size)
        if large is None or size > large[1]:
            large = (path, size)
    if small is None:
        raise SystemExit(f"no picture called {photo_id} in {folder}")
    return small[0], large[0]


def copy_photos(folder):
    IMG.mkdir(parents=True, exist_ok=True)
    rows = []
    for n, (photo_id, alt) in enumerate(PHOTOS, start=1):
        small, large = find_pair(folder, photo_id)
        stem = f"{n:02d}"
        shutil.copyfile(small, IMG / f"{stem}-s.jpg")
        shutil.copyfile(large, IMG / f"{stem}-l.jpg")
        from PIL import Image
        with Image.open(IMG / f"{stem}-s.jpg") as im:
            sw, sh = im.size
        with Image.open(IMG / f"{stem}-l.jpg") as im:
            lw, lh = im.size
        rows.append({
            "n": n, "id": photo_id, "alt": alt,
            "small": f"img/photos/{stem}-s.jpg", "large": f"img/photos/{stem}-l.jpg",
            "sw": sw, "sh": sh, "lw": lw, "lh": lh,
        })
    return rows


def markup(rows):
    out = [START]
    for r in rows:
        out.append(
            '      <button class="g-item" type="button" data-full="{large}" '
            'data-index="{n}" data-alt="{alt}">'
            '<img src="{small}" width="{sw}" height="{sh}" loading="lazy" decoding="async" '
            'alt="{alt}"></button>'.format(
                large=r["large"], n=r["n"], alt=html.escape(r["alt"], quote=True),
                small=r["small"], sw=r["sw"], sh=r["sh"])
        )
    out.append(END)
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    folder = Path(sys.argv[1])
    rows = copy_photos(folder)
    text = INDEX.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("the markers are missing from index.html")
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), markup(rows), text, flags=re.S)
    INDEX.write_text(new, encoding="utf-8")
    total = sum(p.stat().st_size for p in IMG.glob("*.jpg"))
    print(f"{len(rows)} photos written to img/photos/ ({total / 1024 / 1024:.1f} MB)")
    print("the gallery markup in index.html is up to date")


if __name__ == "__main__":
    main()
