#!/usr/bin/env bash
# Take one site off this machine for good.
#
#   sudo ./deploy/drop-site.sh translatero.cc
#
# It:
#   1. moves every nginx file that mentions the domain out of the way
#      (into /etc/nginx/backups/<domain>/ - nothing is deleted, so it can
#      be put back);
#   2. revokes the certificate, so Let's Encrypt stops honouring it;
#   3. deletes the certificate and its renewal, so certbot stops trying;
#   4. reloads nginx and checks that it is happy.
#
# The domain itself has to be dropped at the registrar - this script
# cannot do that.

set -uo pipefail

DOMAIN="${1:-}"
BACKUP=/etc/nginx/backups

if [ -z "$DOMAIN" ]; then
  echo "usage: $0 <domain>" >&2
  exit 64
fi

echo "=== taking $DOMAIN off this machine ==="

echo
echo "--- 1. the nginx configuration ---"
mkdir -p "$BACKUP/$DOMAIN"
for dir in /etc/nginx/sites-enabled /etc/nginx/sites-available /etc/nginx/conf.d; do
  [ -d "$dir" ] || continue
  for f in "$dir"/*; do
    [ -f "$f" ] || continue
    if grep -qi -- "$DOMAIN" "$f" 2>/dev/null; then
      base="$(basename "$f")"
      mv "$f" "$BACKUP/$DOMAIN/${base}.$(date +%Y%m%d%H%M%S)"
      echo "  moved $f"
    fi
  done
done

echo
echo "--- 2. the certificate ---"
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  certbot revoke --cert-path "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" \
    --reason cessationofoperation --non-interactive \
    || echo "  WARNING: the revocation did not complete - carry on, the delete below still works"
  certbot delete --cert-name "$DOMAIN" --non-interactive \
    || echo "  WARNING: the certificate could not be deleted"
else
  echo "  no certificate for $DOMAIN on this machine"
fi

echo
echo "--- 3. nginx ---"
if nginx -t; then
  systemctl reload nginx
  echo "  nginx is happy and has been reloaded"
else
  echo "  WARNING: nginx is not happy - look at the error above" >&2
fi

echo
echo "Done. $DOMAIN is off this machine."
echo "Remember: the domain itself still has to be dropped at the registrar."
echo "The files are not deleted - they are in $BACKUP/$DOMAIN/"
