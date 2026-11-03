#!/usr/bin/env python3
"""Tests for the facts Milka confirmed, and for the things that have to
stay true across all four languages.

    python3 test_site.py          # report
    python3 test_site.py --strict # exit 1 on any failure

Why this file exists
--------------------
On 3 Nov 2026 Milka answered eleven questions about the site. Two of her
answers removed claims the site was making (we do NOT hire out fishing
equipment; the guides speak English, not five languages) and one replaced a
price with a range. Those are exactly the kind of facts that rot: someone
edits a paragraph, the wrong claim comes back, and the site starts telling
guests something the host does not offer.

So the confirmed facts are pinned here as tests. If a later edit breaks one
of them, the test fails instead of the mistake going live.

Run it before every deploy:

    python3 check_i18n.py --strict && python3 test_site.py --strict
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CONFIG = json.loads((ROOT / "site-config.json").read_text(encoding="utf-8"))
DICT_RAW = (ROOT / "i18n-data.js").read_text(encoding="utf-8")
DICT = json.loads(DICT_RAW[DICT_RAW.index("{") : DICT_RAW.rindex("}") + 1])
MARKETING = ROOT / "marketing"

LANGS = ["en", "de", "bs", "it"]


def html_text(key):
    """The English text of an i18n key, as the site will render it."""
    return DICT.get(key, {}).get("en", "")


def plain(text):
    """Strip tags so a claim can be matched on its words alone."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


class Result:
    def __init__(self):
        self.failures = []
        self.passes = 0

    def check(self, ok, label, detail=""):
        if ok:
            self.passes += 1
            print(f"  ok   {label}")
        else:
            self.failures.append(f"{label}" + (f"\n         {detail}" if detail else ""))
            print(f"  FAIL {label}")
            if detail:
                print(f"         {detail}")
        return ok


# ---------------------------------------------------------------------------
# 1. Milka's answers, as they must appear on the site
# ---------------------------------------------------------------------------

def test_milka_facts(r):
    print("\nMilka's confirmed answers (3 Nov 2026)")

    # Q1 - the real inbox, and she answers it herself.
    r.check(
        CONFIG.get("email_live") is True,
        "Q1  email_live is true in site-config.json",
        f"email_live = {CONFIG.get('email_live')!r}",
    )
    r.check(
        CONFIG.get("email") == "domacinstvosobic@gmail.com",
        "Q1  site-config.json has the real inbox",
        f"email = {CONFIG.get('email')!r}",
    )
    r.check(
        "domacinstvosobic@gmail.com" in HTML,
        "Q1  the live inbox appears in index.html",
    )
    r.check(
        "bookings@plivariverlodge.com" not in HTML,
        "Q1  the dead placeholder address is gone from index.html",
    )
    # The address is a mailto: link, not translatable copy, so it lives in
    # the markup and in site-config.json - not in the dictionary.
    r.check(
        'href="mailto:domacinstvosobic@gmail.com"' in HTML,
        "Q1  the contact link points at the live inbox",
    )
    # The form must carry the address so form.js can address the mailto.
    r.check(
        'data-email="domacinstvosobic@gmail.com"' in HTML,
        "Q8  the enquiry form carries data-email for the mailto path",
    )
    r.check(
        'data-netlify="true"' in HTML and 'name="enquiry"' in HTML,
        "Q8  the enquiry form is still Netlify-native",
    )

    # Q2 + Q4 - all three airports, arranged with the lodge.
    for lang in LANGS:
        text = plain(html_text("r7_s"))
        for airport in ("Sarajevo", "Banja Luka", "Split"):
            r.check(
                airport in text,
                f"Q2  r7_s ({lang}) names {airport}",
                f"r7_s[{lang}] = {text!r}",
            )
        r.check(
            "on request" not in text.lower(),
            f"Q2  r7_s ({lang}) no longer says 'on request'",
            f"r7_s[{lang}] = {text!r}",
        )

    # Q3 - the room-only prices are approved, so they must NOT have moved.
    r.check(
        "€85" in HTML and "€70" in HTML and "€110" in HTML and "€900" in HTML,
        "Q3  the approved room-only prices are still on the site",
    )

    # Q5 - NO equipment rental. This is the one that must never come back.
    for key in ("r8_b", "r8_s", "angl_l3", "pkg1_l6"):
        for lang in LANGS:
            text = plain(html_text(key)).lower()
            r.check(
                "equipment rental" not in text
                and "22 per day" not in text
                and "22 € per day" not in text,
                f"Q5  {key} ({lang}) makes no equipment-rental claim",
                f"{key}[{lang}] = {plain(html_text(key))!r}",
            )
    for lang in LANGS:
        text = plain(html_text("r8_b")).lower()
        r.check(
            "equipment" not in text,
            f"Q5  r8_b ({lang}) is not the equipment row",
            f"r8_b[{lang}] = {plain(html_text(key))!r}",
        )

    # Q6 - the real address is Pljeva.
    r.check(
        "Pljeva" in HTML,
        "Q6  index.html names Pljeva",
    )
    r.check(
        CONFIG.get("location", "").startswith("Pljeva"),
        "Q6  site-config.json location starts with Pljeva",
        f"location = {CONFIG.get('location')!r}",
    )
    for key in ("brand_sub", "con_addr_v", "foot_sip"):
        for lang in LANGS:
            r.check(
                "Pljeva" in html_text(key),
                f"Q6  {key} ({lang}) names Pljeva",
                f"{key}[{lang}] = {html_text(key)!r}",
            )

    # Q7 - check-in and check-out times.
    for lang in LANGS:
        text = plain(html_text("con_co_v"))
        r.check(
            "11:00" in text and "10:00" in text,
            f"Q7  con_co_v ({lang}) has the confirmed times",
            f"con_co_v[{lang}] = {text!r}",
        )

    # Q9 - guides speak English, EUR 150-200 per day for the group.
    for lang in LANGS:
        text = plain(html_text("pkg_hosted"))
        r.check(
            "150" in text and "200" in text,
            f"Q9  pkg_hosted ({lang}) states the guided-day price",
            f"pkg_hosted[{lang}] = {text!r}",
        )
        r.check(
            "1,790" not in text and "1790" not in text,
            f"Q9  pkg_hosted ({lang}) drops the invented €1,790 hosted weeks",
            f"pkg_hosted[{lang}] = {text!r}",
        )
        lower = text.lower()
        for claim in ("uk", "german", "french", "italian-speaking", "italiano"):
            r.check(
                claim not in lower,
                f"Q9  pkg_hosted ({lang}) no longer claims {claim!r} guides",
                f"pkg_hosted[{lang}] = {text!r}",
            )

    # Q10 - the licence is a range, not a flat rate.
    for key in ("pkg1_l4", "pkg3_l4", "rates_note"):
        for lang in LANGS:
            text = plain(html_text(key))
            r.check(
                "40" in text and "70" in text,
                f"Q10 {key} ({lang}) states the €40–70 range",
                f"{key}[{lang}] = {text!r}",
            )
            r.check(
                "€50 per day" not in text and "50 € po danu" not in text
                and "50 € al giorno" not in text and "€50/Tag" not in text,
                f"Q10 {key} ({lang}) drops the flat €50/day licence",
                f"{key}[{lang}] = {text!r}",
            )

    # Q11 - the tourist tax is included in the packages.
    for lang in LANGS:
        text = plain(html_text("pkg_p"))
        r.check(
            "tourist tax" in text.lower() or "kurtaxe" in text.lower()
            or "boravišna taksa" in text.lower() or "tassa di soggiorno" in text.lower(),
            f"Q11 pkg_p ({lang}) mentions the tourist tax",
            f"pkg_p[{lang}] = {text!r}",
        )
        r.check(
            "paid on arrival" not in text.lower() and "bei ankunft bezahlt" not in text.lower()
            and "plaća se pri dolasku" not in text.lower() and "da pagare all'arrivo" not in text.lower(),
            f"Q11 pkg_p ({lang}) does not say the tax is paid on arrival",
            f"pkg_p[{lang}] = {text!r}",
        )


# ---------------------------------------------------------------------------
# 2. Facts that were corrected earlier and must not drift back
# ---------------------------------------------------------------------------

def test_established_facts(r):
    print("\nEstablished facts")

    # The spring is 2 km away, the water is 8 degrees, and the river is 33 km.
    r.check("2 km" in HTML, "the lodge is 2 km from the spring")
    r.check("8 °C" in HTML, "the water is 8 °C")
    r.check("33 km" in HTML, "the river is 33 km long")
    r.check("8 km" in HTML, "the fly-fishing beat is 8 km")
    # "3 km" as a distance of its own is wrong - but it is a substring of
    # "33 km" (the river's length) and of "8 km", so a naive search always
    # matches. Only a standalone "3 km" would be the old wrong claim.
    r.check(
        not re.search(r"(?<![0-9])3 km", HTML),
        "the old standalone '3 km' claim is gone",
        "found a standalone '3 km' - the spring is 2 km from the lodge",
    )

    # Check-in/check-out must not drift back to 14:00.
    for lang in LANGS:
        text = plain(html_text("con_co_v"))
        r.check(
            "14:00" not in text,
            f"con_co_v ({lang}) does not say 14:00",
            f"con_co_v[{lang}] = {text!r}",
        )

    # The contact details.
    r.check(
        CONFIG.get("phone_e164") == "+38765622760",
        "the phone number is unchanged",
        f"phone_e164 = {CONFIG.get('phone_e164')!r}",
    )


# ---------------------------------------------------------------------------
# 3. Structural checks across all four languages
# ---------------------------------------------------------------------------

def test_i18n_structure(r):
    print("\nLanguage structure")

    r.check(
        len(LANGS) == 4,
        "four languages are configured",
    )
    for key, entry in sorted(DICT.items()):
        missing = [lg for lg in LANGS if lg not in entry]
        r.check(
            not missing,
            f"key {key} has all four languages",
            f"missing: {missing}",
        )
        for lg in LANGS:
            value = entry.get(lg)
            if isinstance(value, str):
                r.check(
                    bool(value.strip()),
                    f"key {key} ({lg}) is not empty",
                )


# ---------------------------------------------------------------------------
# 4. The marketing copy must agree with the site
# ---------------------------------------------------------------------------

def test_marketing_matches_site(r):
    print("\nMarketing copy agrees with the site")

    out = MARKETING / "out"
    if not out.is_dir():
        r.check(False, "marketing/out exists", "run: python3 marketing/render.py")
        return

    rendered = {p.name: p.read_text(encoding="utf-8") for p in sorted(out.glob("*.md"))}

    for name, text in rendered.items():
        r.check(
            "bookings@plivariverlodge.com" not in text,
            f"{name} has no dead placeholder address",
        )
        r.check(
            "Equipment rental" not in text and "€22 per day" not in text,
            f"{name} makes no equipment-rental claim",
        )

    # site-facts.md is the single source of truth, so it must carry the
    # confirmed numbers.
    facts = rendered.get("site-facts.md", "")
    r.check("Pljeva" in facts, "site-facts.md names Pljeva")
    r.check(
        "domacinstvosobic@gmail.com" in facts,
        "site-facts.md carries the live inbox",
    )
    r.check(
        "€40–70" in facts or "€40-70" in facts,
        "site-facts.md states the licence range",
    )
    r.check(
        "€150–200" in facts or "€150-200" in facts,
        "site-facts.md states the guided-day price",
    )

    # The rendered email templates are what actually get sent to guests.
    mail = rendered.get("email-templates.md", "")
    r.check(
        "€22/day" not in mail and "€22 per day" not in mail,
        "email-templates.md offers no equipment rental",
    )
    r.check(
        "14:00" not in mail,
        "email-templates.md has no stale 14:00 check-in",
    )


# ---------------------------------------------------------------------------
# 5. The standalone build
# ---------------------------------------------------------------------------

def test_standalone(r):
    print("\nStandalone build (Carrd)")

    path = ROOT / "PlivaRiverLodge-standalone.html"
    if not path.exists():
        r.check(False, "the standalone file exists", "run: python3 build_standalone.py")
        return

    s = path.read_text(encoding="utf-8")
    r.check(
        not re.search(r'src="img/', s),
        "no external img/ references",
    )
    r.check(
        ".mp4" not in s,
        "no video file references (poster only)",
    )
    r.check(
        "data-i18n" not in s,
        "no translation attributes (it is English only)",
    )
    r.check(
        "langSwitch" not in s,
        "no language switcher",
    )
    scripts = re.findall(r"<script([^>]*)>", s)
    executable = [t for t in scripts if "application/ld+json" not in t]
    r.check(
        not executable,
        "no executable scripts - only the JSON-LD block",
        f"found: {executable}",
    )
    r.check(
        len(re.findall(r'src="data:image/', s)) >= 20,
        "the images are inlined",
    )
    r.check(
        "domacinstvosobic@gmail.com" in s,
        "the standalone carries the live inbox",
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any failure")
    args = ap.parse_args()

    r = Result()
    test_milka_facts(r)
    test_established_facts(r)
    test_i18n_structure(r)
    test_marketing_matches_site(r)
    test_standalone(r)

    print(f"\n{r.passes} passed, {len(r.failures)} failed")
    if r.failures:
        print("\nFAILURES:")
        for f in r.failures:
            print(f"  - {f}")
        if args.strict:
            return 1
    else:
        print("All good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
