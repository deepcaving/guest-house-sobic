#!/usr/bin/env python3
"""Check the translation dictionary against index.html.

    python3 check_i18n.py            # report problems
    python3 check_i18n.py --strict   # exit non-zero if anything is wrong

Five things it checks, all of which have bitten this site before:

  1. every key used in the HTML exists in the dictionary
  2. every key in the dictionary is used somewhere in the HTML
  3. every key has a translation in every language
  4. the markup in a translation matches the markup in the English original
     (a <b> that is in the HTML but missing from the dictionary disappears
     the moment i18n.js runs)
  5. the English dictionary value still matches the text in the HTML
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
DICT = ROOT / "i18n-data.js"

LANGS = ["en", "de", "bs"]
# Languages that must exist in the dictionary, read from i18n.js so the two
# files cannot drift apart.
LANGS_RE = re.compile(r"var\s+LANGS\s*=\s*\[([^\]]*)\]")


def fail(msg, problems):
    problems.append(msg)


def tags(html):
    """The tag names in a string, in order. <b> and <br> are what matter."""
    return [m.group(1).lower() for m in re.finditer(r"<\s*([a-z0-9]+)", html or "")]


def load_dict():
    raw = DICT.read_text(encoding="utf-8")
    body = raw[raw.index("{") : raw.rindex("}") + 1]
    return json.loads(body)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any problem")
    args = ap.parse_args()

    html = HTML.read_text(encoding="utf-8")
    data = load_dict()
    problems = []

    # Which languages does the switcher actually offer?
    js = (ROOT / "i18n.js").read_text(encoding="utf-8")
    m = LANGS_RE.search(js)
    if not m:
        fail("could not find the LANGS list in i18n.js", problems)
        langs = LANGS
    else:
        langs = re.findall(r"['\"]([a-z]{2})['\"]", m.group(1))
        if not langs:
            fail("could not parse the LANGS list in i18n.js", problems)
            langs = LANGS

    # ---- collect what the HTML uses -------------------------------------
    used = {}       # key -> element inner html
    for m in re.finditer(
        r"<([a-z0-9]+)\b([^>]*\bdata-i18n-key=\"([^\"]+)\"[^>]*)>(.*?)</\1>",
        html, re.S | re.I,
    ):
        used[m.group(3)] = m.group(4)

    placeholder_keys = set(re.findall(r'\bdata-ph="([^"]+)"', html))

    # ---- 1. missing keys -------------------------------------------------
    for key in sorted(used):
        if key not in data:
            fail(f"key '{key}' is used in the HTML but is not in the dictionary", problems)

    for key in sorted(placeholder_keys):
        if key not in data:
            fail(f"placeholder key '{key}' is used in the HTML but is not in the dictionary", problems)

    # ---- 2. unused keys --------------------------------------------------
    referenced = set(used) | placeholder_keys
    for key in sorted(set(data) - referenced):
        fail(f"key '{key}' is in the dictionary but nothing uses it", problems)

    # ---- 3. missing languages -------------------------------------------
    for key in sorted(referenced):
        entry = data.get(key)
        if not entry:
            continue
        for lang in langs:
            if lang not in entry:
                fail(f"key '{key}' has no '{lang}' translation", problems)

    # ---- 4. markup parity ------------------------------------------------
    for key in sorted(referenced):
        entry = data.get(key)
        if not entry:
            continue
        base = entry.get("en")
        if base is None:
            continue
        base_tags = tags(base)
        for lang in langs:
            if lang == "en" or lang not in entry:
                continue
            got = tags(entry[lang])
            if got != base_tags:
                fail(
                    f"key '{key}' ({lang}): markup differs from English - "
                    f"English has {base_tags}, {lang} has {got}. "
                    f"i18n.js writes the dictionary value over the element, so a "
                    f"missing <b> or <br> disappears at runtime.",
                    problems,
                )

    # ---- 5. English value still matches the HTML ------------------------
    for key, inner in sorted(used.items()):
        entry = data.get(key)
        if not entry or "en" not in entry:
            continue
        dict_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", entry["en"])).strip()
        html_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner)).strip()
        if dict_text and html_text and dict_text != html_text:
            fail(
                f"key '{key}': the English dictionary value no longer matches the "
                f"text in index.html.\n"
                f"      HTML: {html_text[:110]!r}\n"
                f"      dict: {dict_text[:110]!r}",
                problems,
            )

    print(f"languages : {', '.join(langs)}")
    print(f"keys      : {len(data)} in the dictionary, {len(referenced)} referenced")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for p in problems:
            print(f"  - {p}")
        if args.strict:
            return 1
    else:
        print("\nOK - every key is present, translated, and the markup matches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
