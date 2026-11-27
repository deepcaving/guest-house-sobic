#!/usr/bin/env python3
"""Rewrite the foot_track line: the site counts the visits now.

    python3 tools/add_foot_track.py

The English, German and Bosnian columns live in the dictionary; the
Italian, French and Dutch live in their own files under tools/ - edit
those there and run their scripts, never edit i18n-data.js by hand.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _dict_writer import BASE, EXTRA, HEAD, load

DICT = Path(__file__).resolve().parent.parent / "i18n-data.js"

TRACK = {
    "en": "We count the visits to this page (no cookies) and we note the page and the approximate location of visitors who open WhatsApp.",
    "de": "Wir zählen die Besuche auf dieser Seite (ohne Cookies) und notieren die Seite und den ungefähren Standort von Besuchern, die WhatsApp öffnen.",
    "bs": "Brojimo posjete na ovoj stranici (bez kolačića) i bilježimo stranicu i približnu lokaciju posjetilaca koji otvore WhatsApp.",
}


def main():
    data = load()
    entry = data.get("foot_track")
    if not entry:
        print("ERROR: foot_track is not in the dictionary")
        return 1
    for lang, value in TRACK.items():
        entry[lang] = value

    out = [HEAD, "window.I18N = {\n"]
    keys = list(data.keys())
    for i, key in enumerate(keys):
        out.append(f'  "{key}": {{\n')
        e = data[key]
        names = [b for b in BASE if b in e] + [x for x in EXTRA if x in e]
        for j, name in enumerate(names):
            comma = "," if j < len(names) - 1 else ""
            out.append(f'    "{name}": {json.dumps(e[name], ensure_ascii=False)}{comma}\n')
        out.append("  }" + ("," if i < len(keys) - 1 else "") + "\n")
    out.append("};\n")
    DICT.write_text("".join(out), encoding="utf-8")
    print("foot_track rewritten. Now run tools/italian.py, tools/french.py and tools/dutch.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
