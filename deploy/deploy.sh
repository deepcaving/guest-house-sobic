#!/usr/bin/env bash
# Put Pliva River Lodge on this server: the files, the service, the
# certificate.
#
#   sudo ./deploy/deploy.sh <your.domain>
#
# Run it once the DNS already points at this machine. It:
#   1. copies the site into /var/www/pliva
#   2. installs the small service behind the enquiry form
#   3. asks certbot for the certificate (this is the "not secure" fix)
#   4. enables the nginx site and reloads it
#
# Everything it does can be undone: the site is still on Netlify, and the
# old address keeps working.

set -euo pipefail

DOMAIN="${1:-}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_DIR=/var/www/pliva
STORE_DIR=/var/lib/pliva-site

if [ -z "$DOMAIN" ]; then
  echo "usage: sudo $0 <your.domain>" >&2
  exit 64
fi

if ! dig +short "$DOMAIN" | grep -q .; then
  echo "WARNING: $DOMAIN does not resolve from here yet. The certificate"
  echo "         needs the DNS to point at this machine (host $(hostname -I | awk '{print $1}'))."
  echo "         Run it again once it does."
fi

echo "--- 1. the site files ---"
install -d -m 755 "$SITE_DIR"
rsync -a --delete \
  --exclude '.git' --exclude 'deploy' --exclude 'docs' --exclude 'tools' \
  --exclude 'test*' --exclude '*.md' \
  "$REPO_DIR"/ "$SITE_DIR"/
chown -R www-data:www-data "$SITE_DIR"

echo "--- 2. the service behind the enquiry form ---"
install -d -m 755 "$STORE_DIR"
install -m 644 "$REPO_DIR/deploy/server.mjs" /opt/pliva-site/server.mjs
mkdir -p /opt/pliva-site/netlify/functions
cp "$REPO_DIR"/netlify/functions/*.mjs /opt/pliva-site/netlify/functions/
cat > /etc/systemd/system/pliva-site.service <<UNIT
[Unit]
Description=Pliva River Lodge - enquiry form service
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/pliva-site
Environment=PORT=8080
Environment=ENQUIRY_STORE=$STORE_DIR/enquiries.ndjson
EnvironmentFile=-/etc/pliva-site/env
ExecStart=/usr/bin/node /opt/pliva-site/server.mjs
Restart=always
RestartSec=3
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
UNIT

# The mail secrets live here, in one file, root-only.
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
  chmod 600 /etc/pliva-site/env
fi
systemctl daemon-reload
systemctl enable --now pliva-site
systemctl reload pliva-site || systemctl restart pliva-site

echo "--- 3. the certificate ---"
apt-get install -y certbot >/dev/null 2>&1 || true
certbot certonly --webroot -w "$SITE_DIR" \
  -d "$DOMAIN" -d "www.$DOMAIN" \
  --non-interactive --agree-tos -m "postmaster@$DOMAIN" \
  || echo "certbot did not issue a certificate - check the DNS and port 80"

echo "--- 4. nginx ---"
sed "s/pliva\.example/$DOMAIN/g" "$REPO_DIR/deploy/nginx.conf" > /etc/nginx/sites-available/pliva-riverside
ln -sf /etc/nginx/sites-available/pliva-riverside /etc/nginx/sites-enabled/pliva-riverside
nginx -t && systemctl reload nginx

echo
echo "Done. Check:"
echo "  https://$DOMAIN/"
echo "  systemctl status pliva-site"
echo "  tail -f /var/log/nginx/access.log"
