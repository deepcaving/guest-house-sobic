#!/usr/bin/env python3
"""Make the licence explicit on both day offers — Pliva and Ribnik alike.

    python3 tools/apply_licence_setup.py

What changes, and why
---------------------
The site said the Pliva permit covers the Ribnik and the Sana. It does
not: the Ribnik is a different water with its own permit (Milka,
3 Nov 2026 — €40 a day on the Pliva, €50 a day on the Ribnik, €35 a day
on the Ribnik in November and December). So the two day offers now carry
the same setup and say it in the same words:

  * a fishing day on the Pliva: the guide's fee for the group, plus the
    licence per angler;
  * a day on the Ribnik: the car for the group, plus the licence per
    angler.

In the fishing packages the licence is already inside the price, so this
is about the room-only rates and about a Ribnik day bought on top.

The English, German and Bosnian columns live in the dictionary; Italian,
French and Dutch live in their own scripts under tools/. This script
updates the first three and patches the three scripts, then the scripts
are run to regenerate the dictionary.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DICT = ROOT / "i18n-data.js"

# --- the new text, per language ---------------------------------------------

NEW = {
    # The fishing day on the Pliva: the guide's fee, and the licence.
    "r8_s": {
        "en": ("English-speaking · €150–200 per day for the group · the licence is "
               "charged per angler, €40 a day on the Pliva"),
        "de": ("Englischsprachig · 150–200 € pro Tag für die Gruppe · die Lizenz wird "
               "pro Angler berechnet, 40 € pro Tag auf der Pliva"),
        "bs": ("Govori engleski · 150–200 € po danu za grupu · dozvola se naplaćuje "
               "po ribolovcu, 40 € po danu na Plivi"),
        "it": ("Parla inglese · 150–200 € al giorno per il gruppo · il permesso si "
               "paga a testa, 40 € al giorno sul Pliva"),
        "fr": ("Anglophone · 150–200 € par jour pour le groupe · le permis est à la "
               "charge de chaque pêcheur, 40 € par jour sur la Pliva"),
        "nl": ("Engelstalig · € 150–200 per dag voor de groep · de vergunning is per "
               "visser, € 40 per dag op de Pliva"),
    },
    # The day on the Ribnik: the car, and the licence — the same setup.
    "rib_price_sub": {
        "en": ("Up to 7 people · one car · about an hour each way · the licence is "
               "charged per angler, €50 a day on the Ribnik"),
        "de": ("Bis zu 7 Personen · ein Auto · etwa eine Stunde je Strecke · die "
               "Lizenz wird pro Angler berechnet, 50 € pro Tag am Ribnik"),
        "bs": ("Do 7 osoba · jedan auto · oko sat vremena u jednom pravcu · dozvola "
               "se naplaćuje po ribolovcu, 50 € po danu na Ribniku"),
        "it": ("Fino a 7 persone · un'auto · circa un'ora per tratta · il permesso si "
               "paga a testa, 50 € al giorno sul Ribnik"),
        "fr": ("Jusqu'à 7 personnes · une voiture · environ une heure par trajet · le "
               "permis est à la charge de chaque pêcheur, 50 € par jour sur la Ribnik"),
        "nl": ("Tot 7 personen · één auto · ongeveer een uur per kant · de vergunning "
               "is per visser, € 50 per dag op de Ribnik"),
    },
    # The old line said the Pliva permit covers the Ribnik. It does not.
    "rib_l4": {
        "en": ("<b>Its own licence</b> — a Ribnik day carries the same charge as a "
               "fishing day on the Pliva: the licence, €50 per angler per day (€35 in "
               "November and December)"),
        "de": ("<b>Eigene Lizenz</b> – ein Ribnik-Tag trägt dieselbe Gebühr wie ein "
               "Fischtag auf der Pliva: die Lizenz, 50 € pro Angler und Tag (im November "
               "und Dezember 35 €)"),
        "bs": ("<b>Zasebna dozvola</b> – ribolovni dan na Ribniku nosi istu naknadu kao "
               "ribolovni dan na Plivi: dozvolu, 50 € po ribolovcu po danu (u novembru i "
               "decembru 35 €)"),
        "it": ("<b>Permesso a parte</b> — una giornata sul Ribnik comporta la stessa voce "
               "di una giornata di pesca sul Pliva: il permesso, 50 € a testa al giorno "
               "(35 € a novembre e dicembre)"),
        "fr": ("<b>Son propre permis</b> — une journée sur la Ribnik comporte la même "
               "charge qu'une journée de pêche sur la Pliva : le permis, 50 € par pêcheur et "
               "par jour (35 € en novembre et décembre)"),
        "nl": ("<b>Eigen vergunning</b> — een Ribnikdag heeft dezelfde opzet als een visdag "
               "op de Pliva: de vergunning, € 50 per visser per dag (€ 35 in november en "
               "december)"),
    },
}

# --- 1. the dictionary: English, German, Bosnian ---------------------------

raw = DICT.read_text(encoding="utf-8")
data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])

for key, values in NEW.items():
    for lang in ("en", "de", "bs"):
        assert values[lang], f"{key}/{lang} is empty"
        data[key][lang] = values[lang]

out = [raw[: raw.index("{")], "{\n"]
keys = list(data.keys())
for i, key in enumerate(keys):
    out.append(f'  "{key}": {{\n')
    entry = data[key]
    names = [n for n in ("en", "de", "bs", "it", "fr", "nl") if n in entry]
    for j, name in enumerate(names):
        comma = "," if j < len(names) - 1 else ""
        value = json.dumps(entry[name], ensure_ascii=False)
        out.append(f'    "{name}": {value}{comma}\n')
    out.append("  }" + ("," if i < len(keys) - 1 else "") + "\n")
out.append("};\n")
DICT.write_text("".join(out), encoding="utf-8")
print(f"dictionary updated: {len(NEW)} keys, en/de/bs")

# --- 1b. the English in the markup -----------------------------------------
HTML = ROOT / "index.html"
html = HTML.read_text(encoding="utf-8")
# The closing tag of the element that carries each key: the two card
# lines are spans, the Ribnik line is a list item.
CLOSE = {"r8_s": "span", "rib_price_sub": "span", "rib_l4": "li"}
for key, values in NEW.items():
    pattern = re.compile(
        r'(data-i18n-key="%s"[^>]*>)(.*?)(</%s>)' % (re.escape(key), CLOSE[key]), re.S
    )
    m = pattern.search(html)
    assert m, f"index.html: {key} not found"
    html = html[: m.start(2)] + values["en"] + html[m.end(2) :]
HTML.write_text(html, encoding="utf-8")
print("index.html updated with the new English")

# --- 2. the scripts that hold it, fr, nl ------------------------------------
for script, lang in (("italian.py", "it"), ("french.py", "fr"), ("dutch.py", "nl")):
    path = ROOT / "tools" / script
    text = path.read_text(encoding="utf-8")
    for key, values in NEW.items():
        pattern = re.compile(r'("%s":\s*")([^"]*)(",)' % re.escape(key))
        m = pattern.search(text)
        assert m, f"{script}: {key} not found"
        text = text[: m.start(2)] + values[lang].replace('"', '\\"') + text[m.end(2) :]
    path.write_text(text, encoding="utf-8")
    print(f"{script} updated")

# --- 3. the facts file, where the false claim lives -------------------------
FACTS = ROOT / "marketing" / "site-facts.md"
facts = FACTS.read_text(encoding="utf-8")
old = "- The Pliva permit covers the Ribnik and the Sana too."
new = ("- The Ribnik has its own permit, so a Ribnik day carries the same charge as a\n"
       "  fishing day on the Pliva: the licence, €50 per angler per day (€35 a day on the\n"
       "  Ribnik in November and December). A day on both rivers means two permits.")
assert old in facts, "site-facts.md: the old line is not there"
facts = facts.replace(old, new, 1)
FACTS.write_text(facts, encoding="utf-8")
print("site-facts.md corrected")
