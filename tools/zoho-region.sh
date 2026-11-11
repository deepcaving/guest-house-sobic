#!/usr/bin/env bash
# Which Zoho data centre does this client belong to?
#
# Zoho runs the same service in several regions, and a token minted in the
# wrong one is refused with "invalid_client" - an error that says nothing
# about the real cause. This asks every region about the client and shows
# which one recognises it.
#
# Usage:
#   ./tools/zoho-region.sh <client_id>
#
# How it works: each data centre is asked to exchange a deliberately fake
# authorisation code. The region that KNOWS the client answers "invalid_code"
# (the client is fine, the code is not). Every other region answers
# "invalid_client" (it has never heard of this client).
#
# Only the client id is needed. No secret is sent - it is not part of the
# request that produces this distinction.

set -uo pipefail

CLIENT_ID="${1:-}"

if [ -z "$CLIENT_ID" ]; then
  echo "usage: $0 <client_id>" >&2
  exit 2
fi

echo "Asking every Zoho data centre about this client..."
echo

FOUND=""
for region in us eu in au jp ca uk; do
  case "$region" in
    us) host="accounts.zoho.com" ;;
    eu) host="accounts.zoho.eu" ;;
    in) host="accounts.zoho.in" ;;
    au) host="accounts.zoho.com.au" ;;
    jp) host="accounts.zoho.jp" ;;
    ca) host="accounts.zohocloud.ca" ;;
    uk) host="accounts.zoho.uk" ;;
  esac

  ERROR=$(curl -s -m 12 -X POST "https://${host}/oauth/v2/token" \
    -d "grant_type=authorization_code" \
    -d "code=probe" \
    -d "client_id=${CLIENT_ID}" \
    -d "client_secret=probe" \
    -d "redirect_uri=http://localhost" \
    | sed -n 's/.*"error":"\([^"]*\)".*/\1/p')

  printf "  %-28s %s\n" "$host" "${ERROR:-<no error field>}"

  if [ "$ERROR" = "invalid_code" ]; then
    FOUND="$region"
  fi
done

echo
if [ -n "$FOUND" ]; then
  echo "This client belongs to the '$FOUND' data centre."
  echo
  echo "  ./tools/zoho-token.sh <client_id> <client_secret> ${FOUND}"
  echo
  echo "And set ZOHO_REGION=${FOUND} in Netlify."
else
  echo "No data centre recognised this client."
  echo
  echo "That usually means one of:"
  echo "  - the client id has a typo"
  echo "  - the client was just created and has not propagated yet (wait a"
  echo "    minute and run this again)"
  echo "  - the client was deleted"
fi
