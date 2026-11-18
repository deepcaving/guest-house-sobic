#!/usr/bin/env bash
# Point the site at its own domain.
#
#   ./deploy/set-domain.sh plivariverlodge.com
#
# Run this AFTER the domain is live and serving the site - not before.
# Until then the canonical link must keep pointing at the address that
# actually answers.
#
# It rewrites the address in the four places it lives:
#   site-config.json   the single source of truth
#   index.html         canonical, og:url, og:image, twitter:image, JSON-LD
#   robots.txt         the sitemap line
#   sitemap.xml        the page address
# and rebuilds the standalone file, which carries the address too.

set -euo pipefail

DOMAIN="${1:-}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -z "$DOMAIN" ]; then
  echo "usage: $0 <your.domain>" >&2
  exit 64
fi

if [ ! -f "$REPO_DIR/index.html" ]; then
  echo "run this from inside the repository" >&2
  exit 64
fi

OLD="https://guesthousesobic.netlify.app/"
NEW="https://${DOMAIN}/"

echo "--- the address ---"
grep -n "site_url" "$REPO_DIR/site-config.json"
echo "  from $OLD"
echo "  to   $NEW"

python3 - "$REPO_DIR" "$OLD" "$NEW" <<'PY'
import sys
from pathlib import Path
root, old, new = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
for name in ("site-config.json", "index.html", "robots.txt", "sitemap.xml"):
    path = root / name
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        print(f"  {name}: updated")
    else:
        print(f"  {name}: nothing to change")
PY

echo "--- the standalone file (it carries the address too) ---"
( cd "$REPO_DIR" && python3 build_standalone.py >/dev/null && echo "  rebuilt" )

echo
echo "Done. Check that the site answers on the new address:"
echo "  curl -I https://${DOMAIN}/"
echo "  grep -c ${DOMAIN} ${REPO_DIR}/index.html"
