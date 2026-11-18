#!/usr/bin/env bash
# Add, change or remove a variable in the server's secrets file.
#
#   sudo ./deploy/set-env.sh MAIL_BCC
#   sudo ./deploy/set-env.sh MAIL_BCC=guesthousesobic@netyou.me
#   sudo ./deploy/set-env.sh --delete ZOHO_CLIENT_SECRET
#
# A value typed at the prompt never appears in the shell history, and a
# value that looks like a secret is typed with the keyboard hidden.
# The file is backed up, the permissions are fixed, the service is
# restarted, and the result is printed with the values masked.

set -uo pipefail

ENV_FILE="${ENV_FILE:-/etc/pliva-site/env}"
SERVICE="${SERVICE:-pliva-site}"

if [ "$(id -u)" -ne 0 ]; then
  echo "run it with sudo" >&2
  exit 64
fi

if [ $# -lt 1 ]; then
  echo "usage: $0 <NAME> | <NAME=value> | --delete <NAME>" >&2
  exit 64
fi

# --- what are we changing? ------------------------------------------------
DELETE=0
ARG="$1"
case "$ARG" in
  --delete) DELETE=1; ARG="${2:-}"; [ -n "$ARG" ] || { echo "which name?" >&2; exit 64; } ;;
  --delete=*) DELETE=1; ARG="${ARG#--delete=}" ;;
esac

NAME="$ARG"
VALUE=""
HAVE_VALUE=0
case "$ARG" in
  *=*) NAME="${ARG%%=*}"; VALUE="${ARG#*=}"; HAVE_VALUE=1 ;;
esac

if ! printf '%s' "$NAME" | grep -qE '^[A-Za-z_][A-Za-z0-9_]*$'; then
  echo "'$NAME' is not a valid variable name" >&2
  exit 64
fi

SECRET=0
printf '%s' "$NAME" | grep -qiE 'PASSWORD|SECRET|TOKEN|KEY' && SECRET=1

if [ "$DELETE" -eq 0 ] && [ "$HAVE_VALUE" -eq 0 ]; then
  echo "--- $NAME ---"
  if [ "$SECRET" -eq 1 ]; then
    read -r -s -p "the value (nothing shows): " VALUE
    echo
  else
    read -r -p "the value: " VALUE
  fi
  [ -n "$VALUE" ] || { echo "no value given - nothing changed" >&2; exit 64; }
fi

# --- the file -------------------------------------------------------------
[ -f "$ENV_FILE" ] || { : > "$ENV_FILE"; }
cp -a "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"

TMP=$(mktemp)
if [ "$DELETE" -eq 1 ]; then
  grep -v "^${NAME}=" "$ENV_FILE" > "$TMP" || true
  echo "removed $NAME"
else
  if grep -q "^${NAME}=" "$ENV_FILE"; then
    awk -v n="$NAME" -v v="$VALUE" 'BEGIN{FS=OFS="="} $1==n{print n "=" v; next} {print}' "$ENV_FILE" > "$TMP"
    echo "changed $NAME"
  else
    cat "$ENV_FILE" > "$TMP"
    [ -s "$TMP" ] && [ "$(tail -c1 "$TMP" | wc -l)" -eq 0 ] && printf '\n' >> "$TMP"
    printf '%s=%s\n' "$NAME" "$VALUE" >> "$TMP"
    echo "added $NAME"
  fi
fi
mv "$TMP" "$ENV_FILE"

chown root:www-data "$ENV_FILE"
chmod 640 "$ENV_FILE"

# --- the service ----------------------------------------------------------
if command -v systemctl >/dev/null 2>&1; then
  systemctl restart "$SERVICE"
  sleep 1
  if systemctl is-active --quiet "$SERVICE"; then
    echo "the service is running"
  else
    echo "the service did not start - here is what it said:" >&2
    journalctl -u "$SERVICE" -n 20 --no-pager >&2
  fi
else
  echo "no systemctl here - the file was written, restart the service yourself"
fi

echo
"$(dirname "$0")/env-keys.sh"
