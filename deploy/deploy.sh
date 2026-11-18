#!/usr/bin/env bash
# Put Pliva River Lodge on this server: the files, the service, the
# certificate.
#
#   sudo ./deploy/deploy.sh <your.domain>
#
# Run it once the DNS already points at this machine. It:
#   1. serves the clone straight from the web root (no copying)
#   2. installs the small service behind the enquiry form
#   3. asks certbot for the certificate (this is the "not secure" fix)
#   4. enables the nginx site and reloads it
#
# Everything it does can be undone: the site is still on Netlify, and the
# old address keeps working.

set -euo pipefail

DOMAIN="${1:-}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STORE_DIR=/var/lib/pliva-site
APP_DIR=/opt/pliva-site

if [ -z "$DOMAIN" ]; then
  echo "usage: $0 <your.domain>" >&2
  exit 64
fi

# --- 0. the things that must be true before anything else ------------------

if [ ! -f "$REPO_DIR/index.html" ]; then
  echo "ERROR: no index.html in $REPO_DIR - is this the clone?" >&2
  exit 1
fi

# Does the domain point here yet? getent is always there; dig often is not.
if ! getent hosts "$DOMAIN" >/dev/null 2>&1; then
  echo "WARNING: $DOMAIN does not resolve from here yet. The certificate"
  echo "         needs the DNS to point at this machine (host $(hostname -I 2>/dev/null | awk '{print $1}'))."
  echo "         Everything else below still works; run it again once it does."
fi

# The service needs node 18 or newer (it uses the fetch API).
NODE_BIN="$(command -v node || true)"
if [ -z "$NODE_BIN" ]; then
  echo "--- node is not installed ---"
  apt-get update -qq >/dev/null 2>&1 || true
  apt-get install -y nodejs >/dev/null 2>&1 || true
  NODE_BIN="$(command -v node || true)"
fi
if [ -z "$NODE_BIN" ]; then
  echo "ERROR: node is not installed and could not be installed." >&2
  echo "       Install node 18 or newer and run this again." >&2
  exit 1
fi
NODE_MAJOR="$("$NODE_BIN" -p 'process.versions.node.split(".")[0]')"
if [ "$NODE_MAJOR" -lt 18 ]; then
  echo "ERROR: node $NODE_MAJOR is too old - the service needs 18 or newer." >&2
  exit 1
fi
echo "node $("$NODE_BIN" -v) at $NODE_BIN"

# --- 1. the site files -----------------------------------------------------
# The clone IS the web root: nginx serves it straight from the repository,
# so "git pull" is the whole deploy. Nothing is copied and nothing is
# left behind to drift.
echo "--- 1. the site files ---"
echo "  serving $REPO_DIR"
chmod -R a+rX "$REPO_DIR"

# --- 2. the service behind the enquiry form -------------------------------
echo "--- 2. the service behind the enquiry form ---"
# The service runs as www-data, so both its folder and the folder it
# writes the backup into must belong to www-data.
install -d -o www-data -g www-data -m 750 "$STORE_DIR"
install -d -m 755 "$APP_DIR"
install -d -m 755 "$APP_DIR/netlify/functions"
install -m 644 "$REPO_DIR/deploy/server.mjs" "$APP_DIR/server.mjs"
cp "$REPO_DIR"/netlify/functions/*.mjs "$APP_DIR/netlify/functions/"

cat > /etc/systemd/system/pliva-site.service <<UNIT
[Unit]
Description=Pliva River Lodge - enquiry form service
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment=PORT=8080
Environment=ENQUIRY_STORE=$STORE_DIR/enquiries.ndjson
EnvironmentFile=-/etc/pliva-site/env
ExecStart=$NODE_BIN $APP_DIR/server.mjs
Restart=always
RestartSec=3
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
UNIT

# The mail secrets live here, in one file. The service reads it as
# www-data, so it is readable by the group and by nobody else.
install -d -o root -g www-data -m 750 /etc/pliva-site
if [ ! -f /etc/pliva-site/env ]; then
  echo "# Copy the Netlify environment variables here, one NAME=value per line." > /etc/pliva-site/env
  echo "# SMTP_HOST=smtppro.zoho.com" >> /etc/pliva-site/env
  echo "# SMTP_PORT=465" >> /etc/pliva-site/env
  echo "# SMTP_SECURE=ssl" >> /etc/pliva-site/env
  echo "# SMTP_USER=the account that owns the app password" >> /etc/pliva-site/env
  echo "# SMTP_PASSWORD=the Zoho app password" >> /etc/pliva-site/env
  echo "# SMTP_FROM_EMAIL=contact@plivariverlodge.com" >> /etc/pliva-site/env
  echo "# SMTP_FROM_NAME=Pliva River Lodge" >> /etc/pliva-site/env
  echo "#" >> /etc/pliva-site/env
  echo "# Leave the ZOHO_* variables OUT. The Zoho Mail API is tried first and" >> /etc/pliva-site/env
  echo "# this plan cannot send to an outside address at all - it answers with an" >> /etc/pliva-site/env
  echo "# empty 404. The SMTP transport below is the one that works." >> /etc/pliva-site/env
fi
chown root:www-data /etc/pliva-site/env
chmod 640 /etc/pliva-site/env

systemctl daemon-reload
systemctl enable --now pliva-site
systemctl reload pliva-site || systemctl restart pliva-site
sleep 1
if ! systemctl is-active --quiet pliva-site; then
  echo "ERROR: the service did not start. Look at the log:" >&2
  echo "       journalctl -u pliva-site -n 30 --no-pager" >&2
  exit 1
fi

# --- 3. the certificate ----------------------------------------------------
echo "--- 3. the certificate ---"
apt-get install -y certbot >/dev/null 2>&1 || true
certbot certonly --webroot -w "$REPO_DIR" \
  -d "$DOMAIN" -d "www.$DOMAIN" \
  --non-interactive --agree-tos -m "postmaster@$DOMAIN" \
  || echo "certbot did not issue a certificate - check the DNS and port 80"

# --- 4. nginx --------------------------------------------------------------
echo "--- 4. nginx ---"
sed -e "s/pliva\.example/$DOMAIN/g" -e "s#/var/www/plivariverlodge#$REPO_DIR#g" \
  "$REPO_DIR/deploy/nginx.conf" > /etc/nginx/sites-available/pliva-riverside
ln -sf /etc/nginx/sites-available/pliva-riverside /etc/nginx/sites-enabled/pliva-riverside
nginx -t && systemctl reload nginx

echo
echo "Done. Check:"
echo "  https://$DOMAIN/"
echo "  systemctl status pliva-site"
echo "  tail -f /var/log/nginx/access.log"
echo
echo "The mail secrets are in /etc/pliva-site/env - fill them in, then:"
echo "  systemctl restart pliva-site"
echo
echo "From now on the deploy is:"
echo "  cd $REPO_DIR && git pull"
