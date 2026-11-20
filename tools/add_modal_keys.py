#!/usr/bin/env python3
"""Add the modal and credit keys to the dictionary (English, German, Bosnian).

    python3 tools/add_modal_keys.py

The Italian, French and Dutch live in tools/italian.py, tools/french.py and
tools/dutch.py - edit them there and run their scripts, never edit
i18n-data.js by hand.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _dict_writer import BASE, EXTRA, HEAD, load

DICT = Path(__file__).resolve().parent.parent / "i18n-data.js"

NEW = {
    "modal_title": {
        "en": "Your enquiry has been sent",
        "de": "Ihre Anfrage wurde gesendet",
        "bs": "Vaša upit je poslat",
    },
    "modal_text": {
        "en": "We have your message and we will reply to you by email, usually the same day.",
        "de": "Wir haben Ihre Nachricht erhalten und antworten Ihnen per E-Mail, meist noch am selben Tag.",
        "bs": "Primili smo vašu poruku i odgovorit ćemo vam e-mailom, obično istog dana.",
    },
    "modal_close": {
        "en": "Close",
        "de": "Schließen",
        "bs": "Zatvori",
    },
    "foot_credit": {
        "en": "Created by",
        "de": "Erstellt von",
        "bs": "Izradio",
    },
}


def main():
    data = load()
    for key, entry in NEW.items():
        if key in data:
            print(f"ERROR: {key} already exists")
            return 1
        data[key] = entry

    out = [HEAD, "window.I18N = {\n"]
    keys = list(data.keys())
    for i, key in enumerate(keys):
        out.append(f'  "{key}": {{\n')
        entry = data[key]
        names = [b for b in BASE if b in entry] + [x for x in EXTRA if x in entry]
        for j, name in enumerate(names):
            comma = "," if j < len(names) - 1 else ""
            value = json.dumps(entry[name], ensure_ascii=False)
            out.append(f'    "{name}": {value}{comma}\n')
        out.append("  }" + ("," if i < len(keys) - 1 else "") + "\n")
    out.append("};\n")
    DICT.write_text("".join(out), encoding="utf-8")
    print(f"Added {len(NEW)} keys. Now run tools/italian.py, tools/french.py and tools/dutch.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
