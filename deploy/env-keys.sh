#!/usr/bin/env bash
# Show which variables the server has, with the secret ones masked.
#
#   sudo ./deploy/env-keys.sh
#
# The values of the harmless ones are shown - a host, a port, an address.
# The values of the secrets are not: it prints "set" instead, so the
# output can be pasted into a chat without giving anything away.

set -uo pipefail

ENV_FILE="${ENV_FILE:-/etc/pliva-site/env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "there is no $ENV_FILE on this machine" >&2
  exit 64
fi

echo "=== $ENV_FILE ==="
echo
while IFS= read -r line; do
  case "$line" in
    ""|\#*) continue ;;
  esac
  NAME="${line%%=*}"
  VALUE="${line#*=}"
  if printf '%s' "$NAME" | grep -qiE 'PASSWORD|SECRET|TOKEN|KEY'; then
    if [ -n "$VALUE" ]; then
      printf '  %-22s set (%d characters)\n' "$NAME" "${#VALUE}"
    else
      printf '  %-22s EMPTY\n' "$NAME"
    fi
  else
    printf '  %-22s %s\n' "$NAME" "$VALUE"
  fi
done < "$ENV_FILE"
echo
echo "The secrets are never printed. To change one:"
echo "  sudo ./deploy/set-env.sh NAME"
