#!/usr/bin/env python3
"""Turn the marketing copy into ready-to-paste files.

    python3 marketing/render.py           # regenerate marketing/out/
    python3 marketing/render.py --check   # report any leftover placeholder
    python3 marketing/render.py --list    # show the values that will be used

How this works
--------------
The files in marketing/ are the MASTER copy and they keep the {{TOKENS}}.
This script reads site-config.json and writes a ready-to-paste version of
each one into marketing/out/.

The master keeps the tokens on purpose: when the email address changes, you
edit site-config.json, re-run this script, and every copy file updates at
once. If the rendered files were the source, the tokens would be gone and
there would be nothing left to re-render.

Always copy and paste from marketing/out/ - not from marketing/.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OUT = ROOT / "out"
CONFIG = REPO / "site-config.json"

TARGET_SUFFIXES = (".md", ".txt")

BANNER = """> **⚠️ BEFORE YOU USE THIS FILE**
> The booking email in it is **not live yet** — `{email}` sits on a domain that
> does not resolve, so anything sent there is lost.
>
> Set the real inbox in `site-config.json`, set `"email_live": true`, then run
> `python3 marketing/render.py` to regenerate this file. Until then, send
> everything through WhatsApp: **{phone}**.

"""


def values():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    site_url = cfg["site_url"].rstrip("/")
    return cfg, {
        "SITE_URL": site_url,
        "EMAIL": cfg["email"],
        "PHONE": cfg["phone_display"],
        "PHONE_E164": cfg["phone_e164"],
        "WHATSAPP": cfg["whatsapp"],
        "HOST": cfg["host"],
        "LOCATION": cfg["location"],
        "TRIPADVISOR": (
            "https://www.tripadvisor.com/Hotel_Review-g2319287-d7383736-"
            "Reviews-Guest_House_Sobic-Sipovo_Republika_Srpska.html"
        ),
    }


def masters():
    for p in sorted(ROOT.glob("*")):
        if p.is_file() and p.suffix in TARGET_SUFFIXES and p.name != "README.md":
            yield p


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="only report leftover placeholders")
    ap.add_argument("--list", action="store_true", help="print the values and exit")
    args = ap.parse_args()

    cfg, vals = values()

    if args.list:
        for k, v in vals.items():
            print(f"  {{{{{k}}}}} = {v}")
        print(f"  email_live = {cfg.get('email_live', False)}")
        return 0

    token_re = re.compile(r"\{\{([A-Z_]+)\}\}")

    if args.check:
        bad = False
        total = 0
        for p in masters():
            found = sorted(set(token_re.findall(p.read_text(encoding="utf-8"))))
            if found:
                bad = True
                total += 1
                unknown = [t for t in found if t not in vals]
                print(f"  {p.relative_to(REPO)}: {', '.join(found)}"
                      + (f"   <- UNKNOWN: {', '.join(unknown)}" if unknown else ""))
        if bad:
            print(f"\n{total} file(s) still carry placeholders - that is expected in the")
            print("master copy. They are filled in at render time. Any token marked")
            print("UNKNOWN is a typo and will not be replaced.")
            return 1
        print("No leftover placeholders in the master copy.")
        return 0

    OUT.mkdir(exist_ok=True)
    banner = "" if cfg.get("email_live", False) else BANNER.format(
        email=cfg["email"], phone=cfg["phone_display"])

    written = []
    for p in masters():
        original = p.read_text(encoding="utf-8")

        def sub(m):
            key = m.group(1)
            if key not in vals:
                print(f"  ! unknown token {{{{{key}}}}} in {p.name}", file=sys.stderr)
                return m.group(0)
            return vals[key]

        new = token_re.sub(sub, original)
        # The banner goes below the H1 so it is the first thing read, not above
        # the title where markdown would swallow it.
        if banner and not new.startswith("> **⚠️"):
            new = re.sub(r"^(# .*)\n", r"\1\n\n" + banner, new, count=1)
            if banner not in new:
                new = banner + new
        (OUT / p.name).write_text(new, encoding="utf-8")
        written.append(p.name)

    print(f"Wrote {len(written)} file(s) to {OUT.relative_to(REPO)}/:")
    for n in written:
        print(f"  {n}")
    if not cfg.get("email_live", False):
        print("\n  ⚠️  Each file carries a banner: the booking email is not live yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
