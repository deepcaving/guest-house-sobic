#!/usr/bin/env python3
"""Build the single-file Carrd version of the Pliva River Lodge site.

    python3 build_standalone.py            # build the standalone file
    python3 build_standalone.py --check    # only verify index.html
    python3 build_standalone.py --max-width 1000 --quality 70

What it does to index.html:

  * every image referenced from img/ is base64-embedded as a data URI
  * images are downscaled and re-compressed on the way in, so the single file
    stays a few MB instead of the ~8 MB the raw assets would produce
  * the property tour video is swapped for its poster image (base64-ing a
    5 MB video is not practical)
  * gallery links to full-size files are dropped, so each photo is embedded
    once instead of twice
  * the language switcher and every data-i18n-* attribute are removed, leaving
    the English copy that is already in the markup
  * executable <script> tags are removed (the JSON-LD block is kept, it is
    inert and still useful to search engines)
  * the enquiry form is replaced with a static WhatsApp / email call to
    action, because the free Carrd tier strips <script> and would otherwise
    leave a form that cannot send anything
  * the favicon is inlined

The result is pasted into a Carrd "Code" section. See README.md.
"""

import argparse
import base64
import io
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "site-config.json"

# How wide each embedded image needs to be, based on where it is displayed.
# The point of the standalone build is that it is one file that has to travel
# over a phone connection, so nothing gets embedded at a size it never shows.
SIZES = {
    # full-bleed hero and the stats band
    "terrace-golden.jpg": 1200,
    "terrace-lounge.jpg": 1200,
    # half-width split panels
    "dining-hall.jpg": 1100,
    "house-by-river.jpg": 1100,
    "angler-pliva.jpg": 1100,
    "ribnik-river.jpg": 1100,
    # gallery thumbnails
    "exterior.jpg": 800,
    "room-twin.jpg": 800,
    "bathroom.jpg": 800,
    "lounge-river.jpg": 800,
    "kitchen.jpg": 800,
    "dining-table-set.jpg": 800,
    "autumn-river.jpg": 800,
    "meadow-pavilion.jpg": 800,
    "riverbank-flowers.jpg": 900,
    # portrait poster for the walkthrough
    "video-poster.jpg": 900,
}


def load_config():
    with open(CONFIG, encoding="utf-8") as fh:
        return json.load(fh)


def encode_image(path, max_width, quality):
    """Return (data_uri, width, height) for an image on disk."""
    limit = SIZES.get(path.name, max_width)
    with Image.open(path) as im:
        im = im.convert("RGB")
        if im.size[0] > limit:
            ratio = limit / im.size[0]
            im = im.resize((limit, max(1, int(im.size[1] * ratio))), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
        data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{data}", im.size[0], im.size[1]


def replace_balanced(html, open_pattern, replacement, tag="div"):
    """Replace an element and everything inside it, matching nested tags.

    Non-greedy regexes are not enough here: the enquiry form and the language
    dropdown both contain nested <div>s, and a lazy match would stop at the
    wrong closing tag and eat the parent's </div> as well.
    """
    m = re.search(open_pattern, html)
    if not m:
        return html, False
    start = m.start()
    depth = 1
    pos = m.end()
    for t in re.finditer(r"<(/?)%s\b[^>]*?(/?)>" % tag, html[m.end():]):
        if t.group(1):
            depth -= 1
            if depth == 0:
                pos = m.end() + t.end()
                break
        elif not t.group(2):
            depth += 1
    return html[:start] + replacement + html[pos:], True


def strip_i18n(html):
    """Remove the translation attributes and the language switcher."""
    html = re.sub(r'\sdata-i18n[-a-z]*="[^"]*"', "", html)
    html = re.sub(r'\sdata-ph="[^"]*"', "", html)
    # the whole language dropdown, including its markup
    html, ok = replace_balanced(html, r'<div class="lang" id="langSwitch">', "")
    if not ok:
        print("  ! could not find the language switcher", file=sys.stderr)
    return html


def strip_scripts(html):
    """Remove executable scripts, keep the JSON-LD block."""
    def drop(match):
        tag = match.group(0)
        if "application/ld+json" in tag:
            return tag
        return ""
    return re.sub(r"<script\b[^>]*>.*?</script>", drop, html, flags=re.S | re.I)


def replace_video(html):
    """Swap the video for its poster image."""
    def swap(match):
        poster = re.search(r'poster="([^"]+)"', match.group(0))
        src = poster.group(1) if poster else "img/video-poster.jpg"
        return (
            f'<img src="{src}" alt="Still from the property walkthrough: '
            f'the private terrace above the Pliva" loading="lazy" decoding="async">'
        )
    html = re.sub(r"<video\b[^>]*>.*?</video>", swap, html, flags=re.S | re.I)
    # the caption promised a video, and there is no longer one
    html = re.sub(
        r'(<div class="video-tag"[^>]*>).*?(</div>)',
        r'\1A glimpse of the lodge\2',
        html,
        flags=re.S,
    )
    # the stylesheet only sized <video>, the poster is an <img> now
    html = html.replace(
        ".video-wrap video{width:100%;display:block}",
        ".video-wrap video,.video-wrap img{width:100%;display:block}",
    )
    return html


def replace_form(html, cfg):
    """Replace the enquiry form with a static call to action."""
    wa = cfg["whatsapp"]
    email = cfg["email"]
    phone = cfg["phone_display"]
    cta = f"""
        <div class="form">
          <h3 style="font-size:1.2rem;margin-bottom:6px">Enquire about availability</h3>
          <p style="font-size:.9rem;color:var(--muted);margin-bottom:18px">Tell us your dates, how many anglers and which airport you fly into. We reply within 24 hours.</p>
          <a class="btn btn-primary" href="{wa}" target="_blank" rel="noopener" style="display:block;text-align:center;margin-bottom:12px">Message us on WhatsApp</a>
          <a class="btn btn-ghost" href="mailto:{email}" style="display:block;text-align:center;margin-bottom:12px">Email {email}</a>
          <a class="btn btn-ghost" href="tel:{cfg['phone_e164']}" style="display:block;text-align:center">Call {phone}</a>
        </div>
    """
    html, ok = replace_balanced(html, r'<div class="form">', cta)
    if not ok:
        print("  ! could not find the enquiry form - left it as it was", file=sys.stderr)
    return html


def inline_favicon(html):
    svg = ROOT / "favicon.svg"
    if not svg.exists():
        return html
    data = base64.b64encode(svg.read_bytes()).decode("ascii")
    uri = f"data:image/svg+xml;base64,{data}"
    html = re.sub(
        r'<link rel="icon"[^>]*>',
        f'<link rel="icon" href="{uri}" type="image/svg+xml">',
        html,
    )
    return html


def inline_app_icon(html):
    """Inline the apple-touch-icon and drop the manifest.

    Both point at local files that do not exist on Carrd. The manifest is of no
    use on a page that is not installable, so it goes; the icon is worth
    keeping for iOS, so it becomes a data URI like the favicon.
    """
    html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)

    icon = ROOT / "apple-touch-icon.png"
    if icon.exists():
        data = base64.b64encode(icon.read_bytes()).decode("ascii")
        uri = f"data:image/png;base64,{data}"
        html = re.sub(
            r'<link rel="apple-touch-icon"[^>]*>',
            f'<link rel="apple-touch-icon" href="{uri}">',
            html,
        )
    else:
        html = re.sub(r'\s*<link rel="apple-touch-icon"[^>]*>', "", html)
    return html


def check(html, cfg):
    """Report anything in index.html that has drifted from site-config.json."""
    problems = []
    checks = [
        (cfg["phone_e164"], "phone number (tel:)"),
        (cfg["whatsapp"].replace("https://", ""), "WhatsApp link"),
        (cfg["email"], "email address"),
        (cfg["site_url"].rstrip("/"), "site url"),
    ]
    for needle, label in checks:
        if needle not in html:
            problems.append(f"{label} '{needle}' not found in index.html")
    if "data-netlify=\"true\"" not in html:
        problems.append("the enquiry form is missing data-netlify=\"true\"")
    return problems


def build(args, cfg):
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    out = src

    # The video has to become an <img> before the embedding pass, otherwise
    # its poster never gets base64-ed and Carrd shows a broken image.
    print("Replacing the video with its poster...")
    out = replace_video(out)

    # The gallery links point at files that will not exist on Carrd, and each
    # one duplicates the picture we are about to embed. Drop the wrapper.
    print("Dropping gallery lightbox links...")
    out = re.sub(r'<a href="img/[^"]+"[^>]*>(<img\b[^>]*>)</a>', r"\1", out)

    # Embed every image, and keep the width/height attributes truthful.
    print("Embedding images...")
    cache = {}

    def img_sub(match):
        tag = match.group(0)
        m = re.search(r'src="(img/[^"]+\.(?:jpg|jpeg|png))"', tag, re.I)
        if not m:
            return tag
        rel = m.group(1)
        path = ROOT / rel
        if not path.exists():
            print(f"  ! missing {rel}", file=sys.stderr)
            return tag
        if rel not in cache:
            cache[rel] = encode_image(path, args.max_width, args.quality)
            print(f"  {rel:28} {path.stat().st_size // 1024:5} KB -> "
                  f"{len(cache[rel][0]) // 1024:5} KB embedded")
        uri, w, h = cache[rel]
        tag = re.sub(r'src="[^"]*"', f'src="{uri}"', tag)
        if 'width="' not in tag:
            tag = tag.replace(" alt=", f' width="{w}" height="{h}" alt=', 1)
        else:
            tag = re.sub(r'width="\d+"', f'width="{w}"', tag)
            tag = re.sub(r'height="\d+"', f'height="{h}"', tag)
        return tag

    out = re.sub(r"<img\b[^>]*>", img_sub, out)

    print("Removing the language switcher and translation attributes...")
    out = strip_i18n(out)

    print("Removing executable scripts...")
    out = strip_scripts(out)

    print("Replacing the enquiry form with a static call to action...")
    out = replace_form(out, cfg)

    print("Inlining the favicon...")
    out = inline_favicon(out)

    print("Inlining the apple-touch-icon and dropping the manifest...")
    out = inline_app_icon(out)

    # Nothing should point at a local file any more.
    leftover = re.findall(r'(?:src|href)="(?!https?:|data:|#|mailto:|tel:)([^"]+)"', out)
    if leftover:
        print("  ! still references local files:", sorted(set(leftover)), file=sys.stderr)

    dest = ROOT / cfg.get("standalone_output", "PlivaRiverLodge-standalone.html")
    dest.write_text(out, encoding="utf-8")
    size = dest.stat().st_size
    print(f"\nWrote {dest.name}  {size / 1e6:.2f} MB")
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-width", type=int, default=1200,
                    help="max width for embedded images (default 1200)")
    ap.add_argument("--quality", type=int, default=68,
                    help="JPEG quality for embedded images (default 68)")
    ap.add_argument("--check", action="store_true",
                    help="only check index.html against site-config.json")
    args = ap.parse_args()

    cfg = load_config()
    src = (ROOT / "index.html").read_text(encoding="utf-8")

    problems = check(src, cfg)
    if problems:
        print("index.html is out of sync with site-config.json:")
        for p in problems:
            print("  -", p)
    else:
        print("index.html matches site-config.json")

    if args.check:
        return 1 if problems else 0

    build(args, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
