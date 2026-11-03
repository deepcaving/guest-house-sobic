#!/usr/bin/env python3
"""Apply Milka's confirmed answers (3 Nov 2026) to index.html.

    python3 tools/apply_milka_html.py

This is the HTML half of the Milka update. The dictionary half lives in
tools/apply_milka.py. Both are idempotent: running them again on an
already-updated file changes nothing, and they fail loudly if an expected
original string is not found, so a silent half-apply cannot happen.

Run both, then check:

    python3 tools/apply_milka.py
    python3 tools/apply_milka_html.py
    python3 check_i18n.py --strict
    python3 test_site.py --strict
"""

import sys
from pathlib import Path

HTML = Path(__file__).resolve().parent.parent / "index.html"

# (old, new, why)
EDITS = [
    # --- Q5: no equipment rental ---
    (
        '<li data-i18n-key="angl_l3" data-i18n="angl_l3"><b>Guided days</b> — a local guide, waders and rods included</li>',
        '<li data-i18n-key="angl_l3" data-i18n="angl_l3"><b>Guided days</b> — a local English-speaking guide on the river</li>',
        "Q5 the fishing section claimed waders and rods were included",
    ),
    (
        '<li data-i18n="pkg1_l6" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="pkg1_l6">Rod and waders on request</li>',
        '<li data-i18n="pkg1_l6" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="pkg1_l6">Own rods and waders — bring your own or hire them in Šipovo</li>',
        "Q5 the Pliva Week offered rods and waders on request",
    ),
    (
        '<div><b data-i18n-key="r8_b" data-i18n="r8_b" data-i18n-inline="1">Equipment rental</b><span data-i18n-key="r8_s" data-i18n="r8_s" data-i18n-inline="1">Rod, reel, line and waders · €22 per day</span></div>',
        '<div><b data-i18n-key="r8_b" data-i18n="r8_b" data-i18n-inline="1">Fishing guide</b><span data-i18n-key="r8_s" data-i18n="r8_s" data-i18n-inline="1">English-speaking · €150–200 per day for the group</span></div>',
        "Q5 the rates grid sold an equipment rental that does not exist",
    ),
    # --- Q10: the licence is a range ---
    (
        '<li data-i18n="pkg1_l4" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="pkg1_l4">Pliva fishing licence — €50/day non-resident rate, included</li>',
        '<li data-i18n="pkg1_l4" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="pkg1_l4">Fishing licence — €40–70 per day depending on the river, included</li>',
        "Q10 the Pliva Week quoted a flat €50/day licence",
    ),
    (
        '<li data-i18n="pkg3_l4" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="pkg3_l4">Pliva fishing licence — €50/day non-resident rate, included</li>',
        '<li data-i18n="pkg3_l4" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="pkg3_l4">Fishing licence — €40–70 per day depending on the river, included</li>',
        "Q10 the Short Break quoted a flat €50/day licence",
    ),
    (
        'The Pliva fishing licence is <b>€50 per day</b> for non-resident guests and is not included in room-only rates; we arrange it for you on arrival. Children under 6 stay free and pay no licence. Children 6–12 pay half rate and no licence. Tourist tax is €2 per person per night, charged on arrival and shown separately on your invoice.',
        'The fishing licence is <b>€40–70 per day</b> depending on which river you fish, and is not included in room-only rates; we arrange it for you on arrival. Children under 6 stay free and pay no licence. Children 6–12 pay half rate and no licence. Tourist tax is €2 per person per night — it is already included in our packages, and on room-only stays it is charged on arrival and shown separately on your invoice.',
        "Q10/Q11 the rates note had a flat licence price and the tax paid on arrival",
    ),
    # --- Q11: the tourist tax is included in the packages ---
    (
        'All packages include the lodge, the table, the guide and the fishing licence. Tourist tax is €2 per person per night, paid on arrival. November and December rates are lower — see each card.',
        'All packages include the lodge, the table, the guide, the fishing licence and the tourist tax — there is nothing to pay on arrival. November and December rates are lower — see each card.',
        "Q11 the packages said the tourist tax was paid on arrival",
    ),
    (
        'Seven nights, six days of guided fishing, full board, licence and the Sarajevo transfer. Group of four.',
        'Seven nights, six days of guided fishing, full board, licence, tourist tax and the Sarajevo transfer. Group of four.',
        "Q11 the November Pliva Week left out the tourist tax",
    ),
    (
        'Four nights, three fishing days, half board, licence and transfer. The easy way to try the river',
        'Four nights, three fishing days, half board, licence, tourist tax and transfer. The easy way to try the river',
        "Q11 the Short Break season card left out the tourist tax",
    ),
    # --- Q9: guides speak English, EUR 150-200 per day for the group ---
    (
        'Hosted weeks with named guides (UK, German, French- and Italian-speaking) are available from €1,790 per person. Ask about the autumn Blue-Winged Olive hatch.',
        'Fishing guides speak English. A guided day costs €150–200 for the group, depending on how many of you there are — so it works out cheaper the more anglers you bring. Ask about the autumn Blue-Winged Olive hatch.',
        "Q9 the hosted-weeks line invented named guides and a €1,790 price",
    ),
    (
        '6 days guided fishing with a local English-speaking guide',
        '6 days guided fishing with a local English-speaking guide',
        "Q9 the Pliva Week guide line is already correct - kept for parity",
    ),
    # --- Q2 + Q4: all three airports ---
    (
        '<span data-i18n-key="r7_s" data-i18n="r7_s" data-i18n-inline="1">Sarajevo included · Banja Luka and Split on request</span>',
        '<span data-i18n-key="r7_s" data-i18n="r7_s" data-i18n-inline="1">Sarajevo, Banja Luka and Split — arranged with the lodge</span>',
        "Q2/Q4 the transfer row said Banja Luka and Split were on request",
    ),
    (
        'We arrange door-to-door transfers in a private car or minivan. Tell us your flight and we will be waiting with a name board.',
        'We arrange door-to-door transfers in a private van or car from Sarajevo, Banja Luka and Split. Tell us your flight and we will be waiting with a name board.',
        "Q2 the getting-here intro did not name the airports",
    ),
    (
        'Croatia, one border crossing. Excellent low-cost connectivity from the UK, Germany and Italy. We cross at Kamensko and the border is usually straightforward.',
        'Croatia, one border crossing. Excellent low-cost connectivity from the UK, Germany and Italy. We cross at Kamensko with our own van, so there is no second vehicle to change into and no transfer you have to arrange yourself.',
        "Q2 the Split card did not say the van crosses the border with the guest",
    ),
    # --- Q6: the real address ---
    (
        '<span data-i18n-key="con_addr_v" data-i18n="con_addr_v">Šipovo, Republika Srpska, Bosnia &amp; Herzegovina<br>2 km downstream of the Pliva springs</span>',
        '<span data-i18n-key="con_addr_v" data-i18n="con_addr_v">Pljeva, Šipovo<br>Bosnia &amp; Herzegovina<br>2 km downstream of the Pliva springs</span>',
        "Q6 the contact address was only 'Šipovo'",
    ),
    (
        '<span data-i18n="foot_sip" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="foot_sip">Šipovo, Republika Srpska, Bosnia &amp; Herzegovina<br>Fly fishing on the Pliva · Open year-round</span>',
        '<span data-i18n="foot_sip" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="foot_sip">Pljeva, Šipovo<br>Bosnia &amp; Herzegovina<br>Fly fishing on the Pliva · Open year-round</span>',
        "Q6 the footer address was only 'Šipovo'",
    ),
    (
        '<span data-i18n="brand_sub" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="brand_sub">Sipovo · Bosnia &amp; Herzegovina</span>',
        '<span data-i18n="brand_sub" data-i18n-de="de" data-i18n-bs="bs" data-i18n-it="it" data-i18n-key="brand_sub">Pljeva · Šipovo · Bosnia &amp; Herzegovina</span>',
        "Q6 the brand strapline did not name Pljeva",
    ),
    # --- Q1: the real inbox ---
    (
        '"email": "bookings@plivariverlodge.com",',
        '"email": "domacinstvosobic@gmail.com",',
        "Q1 the JSON-LD carried the dead placeholder address",
    ),
    (
        '<a href="mailto:bookings@plivariverlodge.com">bookings@plivariverlodge.com</a>',
        '<a href="mailto:domacinstvosobic@gmail.com">domacinstvosobic@gmail.com</a>',
        "Q1 the contact link pointed at the dead placeholder address",
    ),
    # --- Q8: the form must reach Milka by email ---
    (
        'netlify-honeypot="bot-field" data-wa="https://wa.me/38765622760">',
        'netlify-honeypot="bot-field" data-wa="https://wa.me/38765622760" data-email="domacinstvosobic@gmail.com">',
        "Q8 the form needs data-email for the mailto path",
    ),
    (
        'Thank you — WhatsApp has opened with your details ready to send. Hit send there and we will reply within 24 hours.',
        'Thank you — WhatsApp and your email app have opened with your details ready to send. Press send in either one and we will reply within 24 hours.',
        "Q8 the confirmation mentions only WhatsApp",
    ),
    # --- the hosted-week price is gone from the JSON-LD too ---
    (
        '"priceRange": "EUR 70 - EUR 1790 per person",',
        '"priceRange": "EUR 70 - EUR 1390 per person",',
        "Q9 the JSON-LD price range still advertised the invented hosted weeks",
    ),
    (
        '"addressLocality": "Šipovo",',
        '"streetAddress": "Pljeva",\n    "addressLocality": "Šipovo",',
        "Q6 the JSON-LD postal address needs the street",
    ),
]


def main():
    text = HTML.read_text(encoding="utf-8")
    applied = 0
    skipped = 0
    missing = []

    for old, new, why in EDITS:
        if old == new:
            # A no-op pair, kept so the list documents the fact.
            skipped += 1
            continue
        if old not in text:
            missing.append((old, why))
            continue
        text = text.replace(old, new, 1)
        applied += 1

    if missing:
        print("These edits could not be applied - the file is not in the expected state:")
        for old, why in missing:
            print(f"  - {why}")
            print(f"    expected to find: {old[:120]}")
        print("\nNothing was written. Re-clone the repo and start again.")
        return 1

    HTML.write_text(text, encoding="utf-8")
    print(f"index.html: applied {applied} edit(s)" + (f", {skipped} no-op" if skipped else "") + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
