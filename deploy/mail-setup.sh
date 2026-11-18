#!/usr/bin/env bash
# Fill in the mail secrets for the enquiry form, restart the service and
# send one test enquiry.
#
#   sudo ./deploy/mail-setup.sh
#
# The password is asked for with the keyboard hidden and is written
# straight to the file - it never appears in the terminal, in the shell
# history or in this script.

set -uo pipefail

ENV_FILE=/etc/pliva-site/env
APP_DIR=/var/www/plivariverlodge
PORT=8090
RECORDS=/var/lib/pliva-site/enquiries.ndjson

if [ "$(id -u)" -ne 0 ]; then
  echo "run it with sudo" >&2
  exit 64
fi

echo "=== the mail secrets for the enquiry form ==="
echo
echo "The password is a Zoho APP password, not the account password."
echo "  Zoho Mail -> the mailbox -> Settings -> App Passwords -> generate"
echo "  (it is 12 characters, no symbols, and each one can be used once)"
echo

read -r -p "SMTP_USER (the account that owns the app password): " SMTP_USER
read -r -s -p "SMTP_PASSWORD (the app password, nothing shows): " SMTP_PASSWORD
echo
read -r -p "SMTP_FROM_EMAIL [contact@plivariverlodge.com]: " SMTP_FROM_EMAIL
SMTP_FROM_EMAIL="${SMTP_FROM_EMAIL:-contact@plivariverlodge.com}"
read -r -p "SMTP_FROM_NAME [Pliva River Lodge]: " SMTP_FROM_NAME
SMTP_FROM_NAME="${SMTP_FROM_NAME:-Pliva River Lodge}"

if [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
  echo "the user and the password are both needed" >&2
  exit 64
fi

echo
echo "--- writing $ENV_FILE ---"
[ -f "$ENV_FILE" ] && cp -a "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"

cat > "$ENV_FILE" <<ENVFILE
# The mail secrets for the enquiry form. Written by deploy/mail-setup.sh.
# The service reads this file as www-data.
SMTP_HOST=smtppro.zoho.com
SMTP_PORT=465
SMTP_SECURE=ssl
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD
SMTP_FROM_EMAIL=$SMTP_FROM_EMAIL
SMTP_FROM_NAME=$SMTP_FROM_NAME
# Leave the ZOHO_* variables OUT. The Zoho Mail API is tried first and this
# plan cannot send to an outside address at all - it answers with an empty
# 404. The SMTP transport below is the one that works.
ENVFILE

chown root:www-data "$ENV_FILE"
chmod 640 "$ENV_FILE"
echo "  written (root:www-data 640)"

echo
echo "--- restarting the service ---"
systemctl restart pliva-site
sleep 2
if systemctl is-active --quiet pliva-site; then
  echo "  the service is running"
else
  echo "  the service did not start. Here is what it said:" >&2
  journalctl -u pliva-site -n 25 --no-pager >&2
  exit 1
fi

echo
echo "--- one test enquiry, straight to the service ---"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name":"Test Enquiry","email":"test@example.com","dates":"12-19 December","message":"A test from the setup script."}' \
  "http://127.0.0.1:${PORT}/.netlify/functions/enquiry"
echo
echo

echo "--- what was recorded ---"
if [ -f "$RECORDS" ]; then
  tail -n 2 "$RECORDS"
else
  echo "  (no records file yet)"
fi

cat <<'END'

=== what to look at now ===

1. Milka's Gmail (milkasobic25@gmail.com) must have a message from
   contact@plivariverlodge.com with the subject the site sends.
   The collaborator is BCC, so Francesco is on it blind.

2. DKIM. The record is published in DNS, but the signature has to be
   switched on in Zoho, or Gmail will refuse to send as the address:
      Zoho Mail -> Domains -> plivariverlodge.com -> DKIM -> Verify / Enable
   To be sure it is on, open the received message in Gmail, choose
   "Show original" and look for a line starting
       DKIM-Signature: ... d=plivariverlodge.com

3. If the answer above said "smtp" - the mail went out.
   If it said something else, the transport is named in the answer.
END
