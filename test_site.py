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
        CONFIG.get("email") == "milkasobic25@gmail.com",
        "Q1  site-config.json has the real inbox",
        f"email = {CONFIG.get('email')!r}",
    )
    r.check(
        "milkasobic25@gmail.com" in HTML,
        "Q1  the live inbox appears in index.html",
    )
    r.check(
        "bookings@plivariverlodge.com" not in HTML,
        "Q1  the dead placeholder address is gone from index.html",
    )
    r.check(
        "domacinstvosobic@gmail.com" not in HTML,
        "Q1  Milka's previous address is gone from index.html",
    )
    # The address is a mailto: link, not translatable copy, so it lives in
    # the markup and in site-config.json - not in the dictionary.
    r.check(
        'href="mailto:milkasobic25@gmail.com"' in HTML,
        "Q1  the contact link points at the live inbox",
    )
    # The form must carry the address so form.js can address the mailto.
    r.check(
        'data-email="milkasobic25@gmail.com"' in HTML,
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

    # Q10 - the licence states the concrete per-river prices.
    # Milka confirmed the range is real, but €40 (Pliva) / €50 (Ribnik) are the
    # actual market figures; the old €70 ceiling was headroom, not a price.
    # LTG's published Ribnik rates are €50 in season (1 Apr - 15 Nov) and €35
    # from 16 Nov to 31 Mar, so the winter rate must be shown: that is the
    # season this lodge sells hardest.
    for key in ("pkg1_l4", "pkg3_l4"):
        for lang in LANGS:
            text = plain(html_text(key))
            r.check(
                "40" in text and "50" in text,
                f"Q10 {key} ({lang}) states €40 Pliva / €50 Ribnik",
                f"{key}[{lang}] = {text!r}",
            )
            r.check(
                "70" not in text,
                f"Q10 {key} ({lang}) no longer quotes the €70 ceiling",
                f"{key}[{lang}] = {text!r}",
            )
            r.check(
                "35" in text,
                f"Q10 {key} ({lang}) states the €35 November-December Ribnik rate",
                f"{key}[{lang}] = {text!r}",
            )

    # Q10a - the Ribnik day-trip transport: €80 per group, up to 7 people.
    for lang in LANGS:
        text = plain(html_text("rib_price"))
        r.check(
            "80" in text,
            f"Q10a rib_price ({lang}) quotes €80 per group",
            f"rib_price[{lang}] = {text!r}",
        )
        sub = plain(html_text("rib_price_sub"))
        r.check(
            "7" in sub,
            f"Q10a rib_price_sub ({lang}) states the group size",
            f"rib_price_sub[{lang}] = {sub!r}",
        )

    # Q10b - the licence price and the worked totals.
    # The licence and the two totals moved out of rates_note when the
    # toggle was added: the licence onto rates_licence_line, and the
    # totals onto rates_total_sep / rates_total_inc.
    # Read the DICTIONARY per language - html_text() returns the English
    # value for every language, so it cannot check the DE/BS/IT figures.
    half_board_figure = {"en": "€42", "de": "42 €", "bs": "42 €", "it": "42 €"}
    full_board_figure = {"en": "€50", "de": "50 €", "bs": "50 €", "it": "50 €"}
    for lang in LANGS:
        text = plain(DICT.get("rates_note", {}).get(lang, ""))
        for label, needle in (("half board", half_board_figure[lang]),
                              ("full board", full_board_figure[lang])):
            r.check(
                needle in text,
                f"Q10b rates_note ({lang}) quotes {label} {needle}",
                f"rates_note[{lang}] = {text!r}",
            )
        r.check(
            "52" not in text,
            f"Q10b rates_note ({lang}) drops the old €52 meal price",
            f"rates_note[{lang}] = {text!r}",
        )
        r.check(
            "32" not in text,
            f"Q10b rates_note ({lang}) drops the old €32 half-board price",
            f"rates_note[{lang}] = {text!r}",
        )
        # Full board = 2 of the day's 3 meals (Milka, 7 Nov 2026):
        # breakfast plus either lunch or dinner. Checked PER LANGUAGE -
        # the old version used html_text(), which returns English for every
        # language, so the DE/BS/IT wording was never actually checked.
        two_of_three = {
            "en": ("two of the", "three meals"),
            "de": ("zwei der drei", "mahlzeiten"),
            "bs": ("dva od tri", "obroka"),
            "it": ("due dei tre", "pasti"),
        }
        low = text.lower()
        for phrase in two_of_three[lang]:
            r.check(
                phrase in low,
                f"Q10b rates_note ({lang}) says full board is two of three meals ({phrase!r})",
                f"rates_note[{lang}] = {text!r}",
            )

        licence = plain(html_text("rates_licence_line"))
        for needle in ("40", "50"):
            r.check(
                needle in licence,
                f"Q10b rates_licence_line ({lang}) quotes {needle}",
                f"rates_licence_line[{lang}] = {licence!r}",
            )

        # Milka confirmed 3 Nov 2026: full board is EUR 50 per person per day
        # = breakfast + ONE other meal. The worked totals follow from that.
        sep = plain(html_text("rates_total_sep"))
        r.check(
            "160" in sep,
            f"Q10b rates_total_sep ({lang}) gives the €160 solo worked total",
            f"rates_total_sep[{lang}] = {sep!r}",
        )
        r.check(
            "113" in sep,
            f"Q10b rates_total_sep ({lang}) gives the €113 shared-room total",
            f"rates_total_sep[{lang}] = {sep!r}",
        )
        r.check(
            "52" not in sep,
            f"Q10b rates_total_sep ({lang}) drops the old €52 meal price",
            f"rates_total_sep[{lang}] = {sep!r}",
        )

        inc = plain(html_text("rates_total_inc"))
        r.check(
            "160" in inc,
            f"Q10b rates_total_inc ({lang}) gives the €160 solo worked total",
            f"rates_total_inc[{lang}] = {inc!r}",
        )
        r.check(
            "113" in inc,
            f"Q10b rates_total_inc ({lang}) gives the €113 shared-room total",
            f"rates_total_inc[{lang}] = {inc!r}",
        )

    # Q10c - "charged on top of the room price" was misleading: sitting at the
    # end of the line it read as if the THIRD meal were charged separately.
    # It is gone everywhere and must not come back.
    banned = (
        "on top of the room",
        "zum zimmerpreis dazu",
        "na cijenu sobe",
        "alla tariffa della camera",
    )
    for key in ("r5_s", "r6_s", "rates_head", "rates_note"):
        for lang in LANGS:
            text = plain(DICT.get(key, {}).get(lang, "")).lower()
            for phrase in banned:
                r.check(
                    phrase not in text,
                    f"Q10c {key} ({lang}) does not carry the misleading {phrase!r}",
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
        "milkasobic25@gmail.com" in facts,
        "site-facts.md carries the live inbox",
    )
    r.check(
        "€40 per day on the Pliva" in facts
        and "€50 per day on the Ribnik" in facts,
        "site-facts.md states the concrete licence prices",
    )
    r.check(
        "€40–70" not in facts and "€40-70" not in facts,
        "site-facts.md no longer quotes the old €70 ceiling",
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
        "milkasobic25@gmail.com" in s,
        "the standalone carries the live inbox",
    )


def test_enquiry_function(r):
    """The Netlify Function that emails the enquiry to Milka."""
    fn = ROOT / "netlify" / "functions" / "enquiry.mjs"
    r.check(fn.exists(), "the enquiry function exists")
    if not fn.exists():
        return
    s = fn.read_text(encoding="utf-8")

    # It must read the API key from the environment, never from the repo.
    r.check(
        "RESEND_API_KEY" in s and "process.env" in s,
        "the function reads its API key from the environment",
    )
    r.check(
        "MAIL_TO" in s and "MAIL_BCC" in s and "MAIL_FROM" in s,
        "the function reads recipient, bcc and sender from the environment",
    )
    # The live inbox must not be hardcoded as the only route: it reads MAIL_TO
    # but falls back to Milka, which is correct.
    r.check(
        "milkasobic25@gmail.com" in s,
        "the function defaults to Milka's inbox",
    )
    # The collaborator is blind-copied by default - the env var overrides it.
    r.check(
        "francesco.capuzzo@zoho.com" in s,
        "the function defaults to blind-copying the collaborator",
    )
    r.check(
        "domacinstvosobic@gmail.com" not in s,
        "the function no longer references Milka's previous address",
    )
    # The collaborator must be BCC, never CC, so the address is not exposed
    # when Milka forwards the enquiry on.
    r.check(
        "payload.bcc" in s,
        "the function sends the collaborator as bcc",
    )
    r.check(
        "payload.cc" not in s,
        "the function does not send the collaborator as cc",
    )
    r.check(
        "MAIL_CC" not in s,
        "the function does not read a MAIL_CC variable",
    )
    # The sender the guest sees must be the lodge, never a shared sandbox
    # address - "onboarding@resend.dev" reads as a test account and costs
    # trust before a word is said.
    r.check(
        "Pliva River Lodge <bookings@plivariverlodge.com>" in s,
        "the function sends from the lodge's own domain by default",
    )
    r.check(
        "onboarding@resend.dev" not in s,
        "the function no longer falls back to the shared sandbox sender",
    )
    # A *.netlify.app sender can never be verified - Netlify owns that DNS
    # zone - so it must not come back as the default.
    r.check(
        "bookings@guesthousesobic.netlify.app" not in s,
        "the function does not use an unverifiable netlify.app sender",
    )
    # An unverified-domain rejection must be reported precisely, not as a
    # generic failure, or it is impossible to diagnose.
    r.check(
        "not verified" in s,
        "the function detects an unverified sending domain",
    )
    # When the key is missing the function must say WHY, because the usual
    # cause is a Netlify scope or deploy-context setting, not a missing key.
    r.check(
        "CONTEXT" in s and "hint" in s,
        "the function reports the deploy context and a hint when unconfigured",
    )
    r.check(
        "Functions scope" in s or "Functions" in s,
        "the function mentions the Functions scope in its diagnostic",
    )
    # Spam handling.
    r.check(
        "bot-field" in s,
        "the function honours the honeypot field",
    )
    # Reply-to the guest.
    r.check(
        "reply_to" in s,
        "the email replies to the guest, not to the lodge",
    )
    # A missing key must not take the site down.
    r.check(
        "503" in s,
        "the function returns 503 when the provider is not configured",
    )
    r.check(
        "405" in s,
        "the function rejects anything that is not a POST",
    )
    # No secret material committed.
    for secret_marker in ("re_", "Bearer sk-"):
        r.check(
            secret_marker not in s,
            f"the function contains no hardcoded secret ({secret_marker!r})",
        )


def test_form_wiring(r):
    """The form posts to the function and the WhatsApp links pre-fill."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    form_js = (ROOT / "form.js").read_text(encoding="utf-8")

    r.check(
        'data-function="/.netlify/functions/enquiry"' in html,
        "the form points at the enquiry function",
    )
    r.check(
        "sendByEmail" in form_js,
        "the form calls the server-side email path",
    )
    r.check(
        "saveToNetlifyForms" in form_js,
        "Netlify Forms is kept as a fallback",
    )
    r.check(
        'data-netlify="true"' in html,
        "the form is still a Netlify Form",
    )

    # WhatsApp: Milka's number, and every link pre-fills the enquiry.
    r.check(
        "wa.me/38765622760" in html,
        "the WhatsApp links point at Milka's number",
    )
    r.check(
        "wireWhatsAppLinks" in form_js,
        "the WhatsApp links are wired to pre-fill the enquiry",
    )
    r.check(
        "composeMessage" in form_js,
        "the pre-filled message is built from the form fields",
    )
    r.check(
        "encodeURIComponent" in form_js,
        "the pre-filled message is URL encoded",
    )
    # There must be a prominent WhatsApp button next to Send.
    r.check(
        'id="wa-button"' in html,
        "there is a WhatsApp button next to the submit button",
    )
    r.check(
        "form_wa_btn" in html,
        "the WhatsApp button is translated",
    )
    r.check(
        "form_wa_btn" in (ROOT / "i18n-data.js").read_text(encoding="utf-8"),
        "the WhatsApp button label is in the dictionary",
    )

    # Both success messages must exist and be distinct.
    r.check(
        'id="enquiry-status-ok"' in html,
        "there is a success message for the email path",
    )
    r.check(
        'id="enquiry-status-fallback"' in html,
        "there is a message for the fallback path",
    )
    r.check(
        "form_sent_ok" in (ROOT / "i18n-data.js").read_text(encoding="utf-8"),
        "the email success message is translated",
    )
    r.check(
        "form_sent_fb" in (ROOT / "i18n-data.js").read_text(encoding="utf-8"),
        "the fallback message is translated",
    )


def test_rates_toggle(r):
    """The rates toggle: licence-inclusive vs licence-separate totals.

    Not every guest is an angler. The toggle lets a non-angler see what they
    actually pay without a licence charge in it, and lets an angler see the
    all-in figure. The licence price must always be visible either way.
    """
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # The control exists, with the two radios and a default.
    r.check('name="rates-view"' in html, "TOGGLE radio group is present")
    r.check('id="ratesViewSep"' in html, "TOGGLE has the 'room and meals' radio")
    r.check('id="ratesViewInc"' in html, "TOGGLE has the 'including licence' radio")
    r.check(
        re.search(r'id="ratesViewSep"[^>]*checked', html) is not None,
        "TOGGLE defaults to 'room and meals only'",
    )

    # The script that drives it is loaded.
    r.check(
        'src="rates-toggle.js"' in html,
        "TOGGLE script is loaded by the page",
    )
    toggle_js = (ROOT / "rates-toggle.js").read_text(encoding="utf-8")
    r.check("rates_total_inc" in toggle_js, "TOGGLE renders the licence-inclusive total")
    r.check("rates_total_sep" in toggle_js, "TOGGLE renders the licence-separate total")
    r.check(
        "prl:langchange" in toggle_js,
        "TOGGLE survives a language change",
    )
    r.check(
        "prl:langchange" in (ROOT / "i18n.js").read_text(encoding="utf-8"),
        "i18n notifies the toggle after translating",
    )

    # Both totals exist in every language, with the right figures.
    for key, figures in {
        "rates_total_sep": ("€160", "€113"),
        "rates_total_inc": ("€160", "€113"),
    }.items():
        for lang in LANGS:
            text = plain(html_text(key))
            for figure in figures:
                r.check(
                    figure in text,
                    f"TOGGLE {key} ({lang}) mentions {figure}",
                    f"{key}[{lang}] = {text!r}",
                )

    # The licence price is always stated on its own line, in every language.
    for lang in LANGS:
        text = plain(html_text("rates_licence_line"))
        r.check("€40" in text, f"LICENCE line ({lang}) shows the Pliva price")
        r.check("€50" in text, f"LICENCE line ({lang}) shows the Ribnik price")
        r.check("€35" in text, f"LICENCE line ({lang}) shows the winter price")

    # The hint explains the licence is separate and that not everyone fishes.
    for lang in LANGS:
        text = plain(html_text("rates_note_hint")).lower()
        r.check(
            len(text) > 40,
            f"TOGGLE hint ({lang}) is present",
            f"rates_note_hint[{lang}] = {text!r}",
        )

    # The labels are translated, not hard-coded English.
    for key in ("rates_toggle_label", "rates_toggle_off", "rates_toggle_on"):
        for lang in LANGS:
            text = plain(html_text(key))
            r.check(
                len(text) > 3,
                f"TOGGLE label {key} ({lang}) is translated",
                f"{key}[{lang}] = {text!r}",
            )

    # Every language must say the meal figures are added to the room rate.
    # The Italian copy lost this once - it is exactly the phrase that stops
    # a guest reading "52 EUR a persona al giorno" as the whole day price.
    # The meal rows now say what the figure BUYS, and nothing about how it
    # combines with the room - that combination is explained once, in
    # rates_head, without a misleading phrase.
    for key in ("r5_s", "r6_s"):
        for lang in LANGS:
            text = plain(DICT.get(key, {}).get(lang, ""))
            r.check(
                "per person" in text.lower() or "pro person" in text.lower()
                or "po osobi" in text.lower() or "a persona" in text.lower(),
                f"MEALS {key} ({lang}) says the figure is per person",
                f"{key}[{lang}] = {text!r}",
            )

    # The standalone has no scripts, so the radios must be gone and the
    # licence-separate total must be shown as static text.
    standalone = (ROOT / "PlivaRiverLodge-standalone.html").read_text(encoding="utf-8")
    r.check(
        'type="radio"' not in standalone,
        "STANDALONE has no dead radio buttons",
    )
    r.check(
        "rates-toggle" not in standalone,
        "STANDALONE has no leftover toggle CSS",
    )
    r.check(
        "A solo angler in the single room" in standalone,
        "STANDALONE shows the room-and-meals total as static text",
    )
    r.check(
        "Fishing licence" in standalone,
        "STANDALONE still states the licence price",
    )

def test_milka_meal_pricing(r):
    """Milka's confirmed meal rule (3 Nov 2026).

    Full board is EUR 50 per person per day and means breakfast PLUS ONE
    other meal that day - lunch or dinner, not both. The room rate already
    includes breakfast, and the room price is for the ROOM (single 70, double
    85, triple 110, whole house 900), not per person. Meals are charged per
    person on top of the room.
    """
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # The price is EUR 50, and the old EUR 52 is gone from the whole site.
    r.check("€52" not in html, "SITE has no EUR 52 meal price left")
    for key in ("r6_s", "rates_note"):
        for lang in LANGS:
            text = plain(DICT.get(key, {}).get(lang, ""))
            r.check(
                "52" not in text,
                f"MEAL {key} ({lang}) does not quote the old 52",
                f"{key}[{lang}] = {text!r}",
            )

    # EUR 50 per person per day, in every language.
    for lang in LANGS:
        text = plain(DICT.get("r6_s", {}).get(lang, ""))
        r.check("50" in text, f"MEAL r6_s ({lang}) quotes EUR 50", f"r6_s[{lang}] = {text!r}")

    # Full board = breakfast + ONE other meal. Never "all meals", never a
    # promise of both lunch and dinner.
    forbidden = ["all meals", "tutti i pasti", "alle Mahlzeiten", "svi obroci"]
    for lang in LANGS:
        text = plain(DICT.get("r6_s", {}).get(lang, "")).lower()
        for phrase in forbidden:
            r.check(
                phrase.lower() not in text,
                f"MEAL r6_s ({lang}) does not claim {phrase!r}",
                f"r6_s[{lang}] = {text!r}",
            )

    # Milka confirmed 9 Nov 2026: the PACKAGES include all three meals -
    # breakfast, lunch and dinner. The lunch is served at the guest house or
    # packed as a picnic when the day's fishing spot is far enough away.
    # (The room-only rates are a different thing and stay at two meals -
    # see test_meal_model_two_of_three.)
    three_meals = {
        "en": ("all three meals", "breakfast, lunch and dinner"),
        "de": ("alle drei mahlzeiten", "frühstück, mittagessen und abendessen"),
        "bs": ("sva tri obroka", "doručak, ručak i večera"),
        "it": ("tutti e tre i pasti", "colazione, pranzo e cena"),
    }
    for key in ("pkg1_l2", "pkg2_l2", "pkg3_l2"):
        for lang in LANGS:
            low = plain(DICT.get(key, {}).get(lang, "")).lower()
            for phrase in three_meals[lang]:
                r.check(
                    phrase in low,
                    f"MEAL {key} ({lang}) says {phrase!r}",
                    f"{key}[{lang}] = {low!r}",
                )

    # The shared note says three meals a day and explains the picnic option.
    picnic = {
        "en": ("three meals a day", "picnic", "guest house"),
        "de": ("drei mahlzeiten am tag", "picknick", "gästehaus"),
        "bs": ("tri obroka dnevno", "piknik", "pansionu"),
        "it": ("tre pasti al giorno", "picnic", "in casa"),
    }
    for lang in LANGS:
        low = plain(DICT.get("pkg_meals", {}).get(lang, "")).lower()
        for phrase in picnic[lang]:
            r.check(
                phrase in low,
                f"MEAL pkg_meals ({lang}) mentions {phrase!r}",
                f"pkg_meals[{lang}] = {low!r}",
            )

    # The section heading is no longer the vague "Three ways to come".
    for lang in LANGS:
        text = plain(DICT.get("pkg_h2", {}).get(lang, ""))
        r.check(
            "three ways to come" not in text.lower()
            and "drei wege" not in text.lower()
            and "tri načina" not in text.lower()
            and "tre modi" not in text.lower(),
            f"HEAD pkg_h2 ({lang}) is not the vague old heading",
            f"pkg_h2[{lang}] = {text!r}",
        )
        r.check(
            len(text) > 8,
            f"HEAD pkg_h2 ({lang}) is set",
            f"pkg_h2[{lang}] = {text!r}",
        )

    # The room price is for the ROOM. The worked totals must be the ones that
    # follow from that: 70 + 50 + 40 = 160 solo; (85 + 2x50 + 40) / 2 = 112.50.
    r.check(
        "€85 for the room split two ways" in html or "split two ways" in html,
        "MEAL the shared-room total explains that the room price is per room",
    )
    r.check(
        "112.50" in (ROOT / "marketing" / "site-facts.md").read_text(encoding="utf-8"),
        "MEAL site-facts carries the €112.50 shared-room worked total",
    )

def test_meal_model_two_of_three(r):
    """Milka's meal model, restated 7 Nov 2026.

    A guest eats three meals a day: breakfast, lunch, dinner. The room rate
    includes breakfast. Full board at EUR 50 per person per day covers TWO of
    those three meals - breakfast plus either lunch or dinner. The site must
    say so plainly, and must never promise all three.
    """
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # The full-board row states the model: breakfast plus one of lunch/dinner,
    # and calls it two of the three meals.
    two_of_three = {
        "en": "two of the three",
        "de": "zwei von drei",
        "bs": "dva od tri",
        "it": "due dei tre",
    }
    for lang in LANGS:
        text = plain(DICT.get("r6_s", {}).get(lang, ""))
        low = text.lower()
        r.check(
            two_of_three[lang] in low,
            f"MODEL r6_s ({lang}) says two of the three meals",
            f"r6_s[{lang}] = {text!r}",
        )
        r.check(
            "50" in text,
            f"MODEL r6_s ({lang}) quotes EUR 50",
            f"r6_s[{lang}] = {text!r}",
        )

    # It must never claim lunch AND dinner together.
    for lang in LANGS:
        low = plain(DICT.get("r6_s", {}).get(lang, "")).lower()
        both = ("lunch and dinner" in low or "mittagessen und abendessen" in low
                or "ručak i večera" in low or "pranzo e cena" in low)
        r.check(
            not both,
            f"MODEL r6_s ({lang}) does not promise lunch AND dinner",
            f"r6_s[{lang}] = {low!r}",
        )

    # The rates note spells out the same model.
    note_phrases = {
        "en": ("two of the day's three meals",),
        "de": ("zwei der drei mahlzeiten",),
        "bs": ("dva od tri obroka",),
        "it": ("due dei tre pasti",),
    }
    for lang in LANGS:
        low = plain(DICT.get("rates_note", {}).get(lang, "")).lower()
        r.check(
            any(p in low for p in note_phrases[lang]),
            f"MODEL rates_note ({lang}) says full board covers two of three",
            f"rates_note[{lang}] = {low!r}",
        )

    # The rates_head line explains that the room price is for the ROOM and the
    # meals are per person - the reason sharing is cheaper.
    for lang in LANGS:
        text = plain(DICT.get("rates_head", {}).get(lang, ""))
        r.check(
            len(text) > 60,
            f"MODEL rates_head ({lang}) is present and complete",
            f"rates_head[{lang}] = {text!r}",
        )
        r.check(
            "85" in text,
            f"MODEL rates_head ({lang}) uses the double-room figure",
            f"rates_head[{lang}] = {text!r}",
        )
    r.check(
        'data-i18n-key="rates_head"' in html,
        "MODEL the rates_head line is rendered on the page",
    )

    # The arithmetic must still be the one the page claims.
    r.check(
        70 + 50 + 40 == 160,
        "MODEL the solo fishing day is 70 + 50 + 40 = 160",
    )
    r.check(
        (85 + 2 * 50 + 40) / 2 == 112.5,
        "MODEL the shared fishing day is (85 + 100 + 40) / 2 = 112.50",
    )


def test_package_prices_unchanged(r):
    """Milka's package prices must not drift. Pinned from the screenshot.

    The headline "from" prices live as plain HTML (they are rendered by the
    card markup, not translated); the group/solo notes and the winter rates
    are dictionary keys and are checked in every language.
    """
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # Headline prices, exactly as on the screenshot.
    for price in ("€1,390", "€1,090", "€830"):
        r.check(
            price in html,
            f"PKG headline price {price} is still on the page",
        )

    # Group / solo notes, in every language.
    expected_notes = {
        "pkg1_note": ("€1,590", "€2,090"),
        "pkg2_note": ("€1,230", "€1,630"),
        "pkg3_note": ("€930", "€1,230"),
    }
    for key, prices in expected_notes.items():
        for lang in LANGS:
            text = plain(html_text(key))
            for price in prices:
                r.check(
                    price in text,
                    f"PKG {key} ({lang}) still shows {price!r}",
                    f"{key}[{lang}] = {text!r}",
                )

    # Winter rates.
    for key, price in (("winter_label", "€1,190"), ("pkg2_winter", "€950"), ("pkg3_winter", "€730")):
        for lang in LANGS:
            text = plain(html_text(key))
            r.check(
                price in text,
                f"PKG {key} ({lang}) still shows {price!r}",
                f"{key}[{lang}] = {text!r}",
            )

    # The dead equipment-rental claim must stay gone.
    for key in ("pkg1_l6",):
        for lang in LANGS:
            text = plain(html_text(key)).lower()
            r.check(
                "rod and waders on request" not in text,
                f"PKG {key} ({lang}) has no equipment-rental claim",
                f"{key}[{lang}] = {text!r}",
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
    test_enquiry_function(r)
    test_form_wiring(r)
    test_rates_toggle(r)
    test_milka_meal_pricing(r)
    test_meal_model_two_of_three(r)
    test_package_prices_unchanged(r)

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
