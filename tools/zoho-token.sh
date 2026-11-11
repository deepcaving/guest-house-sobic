#!/usr/bin/env bash
# Get a Zoho Mail API refresh token - the only manual step in the email setup.
#
# It prints the authorisation URL, waits for you to paste the code Zoho
# redirects you with, and exchanges it for a refresh token.
#
# Usage:
#   ./tools/zoho-token.sh <client_id> <client_secret> [region]
#
# region: us (default) | eu | in | au | jp | ca | uk
#
# Use "eu" for a European Zoho account. A token minted in the wrong region
# is rejected with "invalid_client", and the error does not say why.

set -euo pipefail

CLIENT_ID="${1:-}"
CLIENT_SECRET="${2:-}"
REGION="${3:-us}"

# The secret can be left off the command line and typed at the prompt
# instead. That is the better way: a secret typed as an argument is saved
# in your shell history, and the shell history is exactly the kind of
# thing that ends up in a screenshot or a chat transcript.
# A version stamp, so it is obvious at a glance whether the script on disk
# is the current one. An old copy prints STEP 1 twice and never asks for
# the secret - that is the giveaway.
VERSION="2026-11-11.2"

if [ -z "$CLIENT_ID" ]; then
  echo "usage: $0 <client_id> [region]      # the secret is prompted for" >&2
  echo "       $0 <client_id> us" >&2
  echo "       (helper version ${VERSION})" >&2
  exit 2
fi

if [ -z "$CLIENT_SECRET" ]; then
  echo "Client secret (it will not be echoed, and it stays out of your shell history):"
  read -r -s -p "> " CLIENT_SECRET
  echo
  if [ -z "$CLIENT_SECRET" ]; then
    echo "no client secret given" >&2
    exit 1
  fi
fi

echo "Pliva River Lodge - Zoho token helper, version ${VERSION}"
echo

case "$REGION" in
  us) ACCOUNTS="accounts.zoho.com"; MAIL="mail.zoho.com" ;;
  eu) ACCOUNTS="accounts.zoho.eu"; MAIL="mail.zoho.eu" ;;
  in) ACCOUNTS="accounts.zoho.in"; MAIL="mail.zoho.in" ;;
  au) ACCOUNTS="accounts.zoho.com.au"; MAIL="mail.zoho.com.au" ;;
  jp) ACCOUNTS="accounts.zoho.jp"; MAIL="mail.zoho.jp" ;;
  ca) ACCOUNTS="accounts.zohocloud.ca"; MAIL="mail.zohocloud.ca" ;;
  uk) ACCOUNTS="accounts.zoho.uk"; MAIL="mail.zoho.uk" ;;
  *) echo "unknown region: $REGION" >&2; exit 2 ;;
esac

SCOPES="ZohoMail.messages.CREATE,ZohoMail.accounts.READ"
REDIRECT="http://localhost"

echo
echo "STEP 1 - open this URL in your browser and approve the app:"
echo
echo "https://${ACCOUNTS}/oauth/v2/auth?scope=${SCOPES}&client_id=${CLIENT_ID}&response_type=code&access_type=offline&prompt=consent&redirect_uri=${REDIRECT}"
echo
echo "Zoho redirects you to ${REDIRECT}?code=XXXX"
echo "The page will say it cannot be reached - that is expected."
echo
echo "Copy the WHOLE address bar line and paste it below."
echo "You can paste either the full URL or just the code - both work."
echo

# Accept either the full redirect URL or just the code. Selecting a
# 60-character code out of a long address bar is where people get stuck.
read -r -p "Paste the URL or the code here: " PASTE

CODE="${PASTE}"
case "$PASTE" in
  *code=*) CODE="${PASTE##*[?&]code=}" ;;
esac
# Drop anything that came after the code (a &state=... parameter, say).
CODE="${CODE%%&*}"
CODE="$(printf '%s' "$CODE" | tr -d '[:space:]')"

if [ -z "$CODE" ]; then
  echo "no code given" >&2
  exit 1
fi

echo
echo "Got the code. Exchanging it for tokens..."
echo

RESPONSE=$(curl -s -X POST "https://${ACCOUNTS}/oauth/v2/token" \
  -d "code=${CODE}" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "redirect_uri=${REDIRECT}" \
  -d "grant_type=authorization_code")

ACCESS=$(printf '%s' "$RESPONSE" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
REFRESH=$(printf '%s' "$RESPONSE" | sed -n 's/.*"refresh_token":"\([^"]*\)".*/\1/p')

if [ -z "$ACCESS" ] || [ -z "$REFRESH" ]; then
  echo "The exchange failed:"
  echo "$RESPONSE"
  echo
  case "$RESPONSE" in
    *invalid_client_secret*)
      echo "=> The CLIENT SECRET is wrong."
      echo "   Zoho does not accept it for this client. Either it was typed"
      echo "   incorrectly, or it was rotated in the API console since then."
      echo "   Copy it again from api-console.zoho.com -> the client -> Client"
      echo "   Secret, and paste it at the prompt above."
      ;;
    *invalid_client*)
      echo "=> The CLIENT ID or the REGION is wrong."
      echo "   A token minted in another data centre is refused the same way."
      echo "   Run tools/zoho-region.sh ${CLIENT_ID} to find the right one."
      ;;
    *invalid_code*)
      echo "=> The CODE is wrong, not the secret."
      echo "   The code lasts two minutes and can be used only once. Open the"
      echo "   authorisation URL again, approve it, and paste the new code"
      echo "   straight away."
      ;;
    *)
      echo "=> Check the client id, the secret, and that the redirect URI in"
      echo "   the Zoho console is exactly http://localhost"
      ;;
  esac
  exit 1
fi

echo "OK. Tokens acquired."
echo

# Prove the refresh token actually works BEFORE anyone pastes it into
# Netlify. A refresh token that cannot exchange for an access token is
# useless, and finding that out here is far better than finding it out
# from a 502 in production.
echo "Checking that the refresh token works..."
VERIFY=$(curl -s -X POST "https://${ACCOUNTS}/oauth/v2/token" \
  -d "grant_type=refresh_token" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "refresh_token=${REFRESH}")
if printf '%s' "$VERIFY" | grep -q '"access_token"'; then
  echo "  yes - it exchanges for a fresh access token."
else
  echo "  NO - the refresh token does NOT work:"
  echo "  ${VERIFY}"
  echo
  echo "Do not put this token in Netlify. Make a new one."
  exit 1
fi
echo

ACCOUNTS_JSON=$(curl -s "https://${MAIL}/api/accounts" \
  -H "Authorization: Zoho-oauthtoken ${ACCESS}")
ACCOUNT_ID=$(printf '%s' "$ACCOUNTS_JSON" | sed -n 's/.*"accountId":"\([^"]*\)".*/\1/p')
MAILBOX=$(printf '%s' "$ACCOUNTS_JSON" | sed -n 's/.*"primaryEmailAddress":"\([^"]*\)".*/\1/p')

echo "Mailbox   : ${MAILBOX:-<not found>}"
echo "Account id: ${ACCOUNT_ID:-<not found>}"
echo
echo "Now set these four variables in Netlify"
echo "(Site configuration -> Environment variables -> Functions scope, and"
echo " tick Production):"
echo
echo "  ZOHO_CLIENT_ID      = ${CLIENT_ID}"
echo "  ZOHO_CLIENT_SECRET  = ${CLIENT_SECRET}"
echo "  ZOHO_REFRESH_TOKEN  = ${REFRESH}"
echo "  ZOHO_REGION         = ${REGION}"
if [ -n "$ACCOUNT_ID" ]; then
  echo "  ZOHO_ACCOUNT_ID     = ${ACCOUNT_ID}"
fi
echo
echo "The refresh token does not expire, so this is a one-time job."
