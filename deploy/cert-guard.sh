#!/usr/bin/env bash
# Make every certificate on this box renew itself, and reload nginx after.
#
#   sudo ./deploy/cert-guard.sh
#
# What a Let's Encrypt certificate does: it is good for 90 days and then it
# is gone. The renewal is what keeps the site from showing "not secure" -
# certbot's timer checks twice a day and renews anything that is within
# 30 days of expiring. Three things have to be true for that to work:
#
#   1. the timer is running;
#   2. the certificate can still prove who you is (the webroot path has
#      to exist, or DNS has to be reachable);
#   3. nginx is reloaded afterwards, or the site keeps serving the old
#      certificate.
#
# This script checks all three for EVERY certificate on the machine, and
# then proves it with a dry-run renewal.

set -uo pipefail

HOOK_DIR=/etc/letsencrypt/renewal-hooks/deploy
HOOK="$HOOK_DIR/reload-nginx.sh"

echo "=== 1. certbot and its timer ==="
if ! command -v certbot >/dev/null 2>&1; then
  echo "certbot is not installed - installing it"
  apt-get update -qq >/dev/null 2>&1 || true
  apt-get install -y certbot >/dev/null 2>&1 || true
fi
if ! command -v certbot >/dev/null 2>&1; then
  echo "ERROR: certbot could not be installed." >&2
  exit 1
fi
certbot --version

# The timer is what renews without anybody asking.
if systemctl list-unit-files certbot.timer 2>/dev/null | grep -q "certbot.timer"; then
  systemctl enable --now certbot.timer
  echo "certbot.timer: $(systemctl is-active certbot.timer) (it checks twice a day)"
  systemctl list-timers certbot.timer --no-pager 2>/dev/null | head -3
else
  echo "WARNING: this certbot has no timer." >&2
  echo "         Without it nothing renews by itself. Put these in the crontab:" >&2
  echo "           0 3 * * * certbot renew --quiet" >&2
  echo "           30 3 * * * certbot renew --quiet" >&2
fi

echo
echo "=== 2. the hook that reloads nginx after a renewal ==="
install -d -m 755 "$HOOK_DIR"
cat > "$HOOK" <<'HOOK'
#!/usr/bin/env bash
# After certbot renews a certificate, nginx is still holding the old one
# in memory. Reload it, or the site keeps serving the expired file.
echo "cert-guard: reloading nginx after the renewal of $RENEWED_DOMAINS"
if ! nginx -t; then
  echo "cert-guard: the nginx configuration is broken - not reloading" >&2
  exit 1
fi
systemctl reload nginx
HOOK
chmod 755 "$HOOK"
chown root:root "$HOOK"
echo "installed $HOOK"

echo
echo "=== 3. every certificate on this machine ==="
certbot certificates 2>&1 | sed 's/^/  /'

echo
echo "  how each one renews:"
for conf in /etc/letsencrypt/renewal/*.conf; do
  [ -e "$conf" ] || continue
  name="$(basename "$conf" .conf)"
  auth="$(grep -m1 '^authenticator' "$conf" | cut -d= -f2)"
  webroot="$(grep -m1 '^webroot_path' "$conf" | cut -d= -f2)"
  if [ "$auth" = "webroot" ]; then
    if [ -n "$webroot" ] && [ -d "$webroot" ]; then
      echo "    $name: webroot $webroot  ✓ the folder is there"
    else
      echo "    $name: webroot $webroot  ✗ THE FOLDER IS MISSING - this renewal will fail"
    fi
  else
    echo "    $name: $auth  (nothing to check on disk)"
  fi
done

echo
echo "=== 4. the dry run - it proves the renewals work without changing anything ==="
DRY=$(certbot renew --dry-run 2>&1)
echo "$DRY" | tail -30

OK_COUNT=$(echo "$DRY" | grep -c "fullchain.pem (success)")
BAD_COUNT=$(echo "$DRY" | grep -c "fullchain.pem (failure)")
echo
echo "--- the result ---"
echo "  renewals that work: $OK_COUNT"
echo "  renewals that fail:  $BAD_COUNT"
if [ "$BAD_COUNT" -gt 0 ]; then
  echo
  echo "  A certificate whose renewal fails will EXPIRE and stay expired." >&2
  echo "  Each failure above names its reason. The commonest one is:" >&2
  echo "    'The nginx plugin is not working' - a broken nginx configuration" >&2
  echo "    stops certbot before it can renew anything. Fix nginx first:" >&2
  echo "      sudo nginx -t" >&2
  echo "    then run this script again." >&2
fi

echo
echo "Check it any time with:  sudo certbot certificates"
echo "                     and:  systemctl list-timers certbot.timer"
