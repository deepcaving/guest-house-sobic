# Enquiry email — how it works and how to switch it on

## What the guest sees

The guest fills in the enquiry form and presses **Send enquiry**. The form
does three things, in this order:

1. **Sends the enquiry by email, from the server.** It lands in Milka's inbox
   (`milkasobic25@gmail.com`) with you blind-copied on it. The guest does
   nothing beyond pressing the button — no mail app, no WhatsApp, no
   "press send" step.
2. **Keeps a copy in Netlify Forms**, so the enquiry also shows up in the
   Netlify dashboard and nothing is ever lost.
3. **Falls back to WhatsApp and the guest's own mail app** if the email
   service is down or has not been configured yet.

With JavaScript switched off, the form still posts to Netlify Forms as a
normal Netlify Form, so the enquiry is captured either way.

## Why it works this way

A Netlify Function is a short-lived serverless function. It cannot act as a
conventional mail server: there is no long-running process to keep a
connection open.

**On outbound SMTP:** Netlify's Free plan is *not* the obstacle. This was
measured from the live Netlify runtime on 11 Nov 2026, with a probe function:

| Port | Result |
|---|---|
| 25 | **blocked** (timeout) |
| 465 | **open** (64 ms) |
| 587 | **open** (69 ms) |

Port 25 is blocked because Netlify Functions run on AWS Lambda, and AWS blocks
25 on every plan — it is not a Netlify restriction. Ports 465 and 587 work
fine on the Free plan. A full SMTP session was then completed from the same
runtime: TLS handshake → `220 smtp.zohomail.com SMTP Server ready` → EHLO →
`250-smtp.zohomail.com Hello`.

The belief that "SMTP on Netlify needs Pro" comes from other hosts: **Railway**
turns SMTP off below Pro, and **Render** blocks outbound 25/465/587 on its
free tier. Neither applies here.

SMTP on Zoho still has one practical problem: it needs an **app-specific
password**, which has to be generated in the Zoho web interface. That is why
the Zoho **Mail API** is the primary transport — it needs no SMTP password
and no verified domain.

## The three transports, in order

1. **The Zoho Mail API** (HTTPS, OAuth 2.0) — primary.
2. **SMTP** (port 465, implicit TLS) — fallback.
3. **The Resend HTTP API** — fallback, needs a verified sending domain.

Each one is tried only if the previous one failed or is not configured. If
none is configured, the function logs the enquiry and returns a "not
configured" status, and the browser falls back to WhatsApp — **the enquiry is
never lost**.

## Setting it up

### Option A — the Zoho Mail API (recommended)

This sends from the mailbox the lodge already owns
(`guesthousesobic@blink2ask.com`), so the mail arrives exactly as if Milka
had sent it from Zoho webmail. **No domain to register, no DNS records, no
DKIM, no SMTP password.**

One-time setup, in the [Zoho API console](https://api-console.zoho.com):

1. **Add Client** → **Server-based Application**. Fill in:
   - **Client Name**: `Pliva River Lodge` (anything readable)
   - **Homepage URL**: `https://guesthousesobic.netlify.app`
   - **Authorized Redirect URIs**: `http://localhost` — then press the **+**
     to add it

   ("Self Client" is quicker and needs no redirect URI, but Server-based is
   what the steps below assume.)

2. Copy the **Client ID** and **Client Secret** that Zoho shows you.

3. Get the refresh token. The helper script does the whole thing — it prints
   the authorisation URL, and exchanges the code for you:

   ```bash
   ./tools/zoho-token.sh <client_id> <client_secret> us
   ```

   The region matters. **This account is on the US/global data centre**
   (`accounts.zoho.com`) — proven by asking each data centre about the
   client: `.com` answers `invalid_code` (it knows the client, only the
   code was wrong) while every other region answers `invalid_client`
   (it does not know the client at all).

   Use `eu` only for a European account, `in` for India, `au` for Australia,
   `jp` for Japan, `ca` for Canada, `uk` for the UK. A token minted in the
   wrong region is refused with the same unhelpful `invalid_client`.

   The script prints the four variables to paste into Netlify.

   **What the script does, step by step:**

   1. It prints an authorisation URL.
   2. You open that URL in a browser and click **Authorize**.
   3. Zoho redirects you to `http://localhost/?code=...`. **That page will
      fail to load — that is expected**, there is no server on your own
      machine. The code is in the address bar.
   4. Paste the **whole address bar line** back into the terminal (the script
      also accepts just the code). It exchanges it, finds your account id,
      and prints the variables to paste into Netlify.

   Steps 1 and 4 are the script; steps 2 and 3 are you, and they happen once
   in the whole life of the setup.

   **What it does under the hood**, if you would rather do it by hand:

   ```bash
   # 1. open this in a browser and approve it
   https://accounts.zoho.eu/oauth/v2/auth?scope=ZohoMail.messages.CREATE,ZohoMail.accounts.READ&client_id=YOUR_CLIENT_ID&response_type=code&access_type=offline&redirect_uri=http://localhost

   # 2. Zoho redirects you to http://localhost?code=XXXX
   #    (the page will fail to load - that is expected, copy the code)

   # 3. exchange it
   curl -X POST "https://accounts.zoho.eu/oauth/v2/token" \
     -d "grant_type=authorization_code" \
     -d "code=THE_CODE" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=http://localhost"
   ```

   The reply contains a `refresh_token`. **It does not expire**, so nothing
   needs rotating.

   **The scopes** are `ZohoMail.messages.CREATE` (to send) and
   `ZohoMail.accounts.READ` (to look up the account id). Both are needed:
   the send endpoint itself only wants CREATE, but the account id lookup
   wants READ, and the id is fetched at runtime when it is not set.

4. The **account id** can be left unset — the function fetches it. To find it
   by hand: `GET https://mail.zoho.com/api/accounts` with the access token.

Then set these in Netlify (Site configuration → Environment variables):

| Variable | Value |
|---|---|
| `ZOHO_CLIENT_ID` | from the API console |
| `ZOHO_CLIENT_SECRET` | from the API console |
| `ZOHO_REFRESH_TOKEN` | the long-lived refresh token |
| `ZOHO_ACCOUNT_ID` | optional — fetched at runtime if absent |
| `ZOHO_REGION` | `us` (default) or `eu` |

> **The region matters.** A European Zoho account lives on
> `accounts.zoho.eu` / `mail.zoho.eu`, not `.com`. A token minted in the
> wrong region is rejected with `invalid_client`. The function says so
> explicitly when that happens. **This particular account is on the
> US/global data centre**, so use `us`.

**Zoho's limits** (free account): 50–500 external emails per hour on a
rolling basis, 100 recipients per message, and 30 API calls per minute. A
lodge taking a handful of enquiries a day is nowhere near any of those.

### Option B — SMTP

Needs a Zoho **app password**: Zoho Mail → Settings → Mailboxes → the
mailbox → Edit → App passwords → Generate. The account password is refused
by Zoho from an unrecognised host.

```bash
SMTP_HOST=smtp.zoho.com
SMTP_PORT=465
SMTP_USER=guesthousesobic@blink2ask.com
SMTP_PASSWORD=your-zoho-app-password
SMTP_FROM_EMAIL=guesthousesobic@blink2ask.com
SMTP_SECURE=ssl
SMTP_FROM_NAME=Pliva River Lodge
```

| Variable | Meaning |
|---|---|
| `SMTP_HOST` | the SMTP server, e.g. `smtp.zoho.com` |
| `SMTP_PORT` | `465` for implicit TLS, `587` for STARTTLS |
| `SMTP_USER` | the mailbox to log in as |
| `SMTP_PASSWORD` | the mailbox password, or a Zoho **app password** |
| `SMTP_FROM_EMAIL` | the From address |
| `SMTP_FROM_NAME` | the display name on the From line |
| `SMTP_SECURE` | `ssl` (implicit TLS) or `starttls` |

**Why a hand-written client?** Netlify Functions cannot use a normal SMTP
library: most of them open a long-lived plain socket, which is blocked. The
client in `netlify/functions/smtp.mjs` speaks SMTP directly over a TLS
socket, which works because the TLS handshake and the SMTP session are the
same connection. It handles both `AUTH PLAIN` and `AUTH LOGIN`, dot-stuffs
the message body, and sets `Reply-To` to the guest.

### Option C — Resend

The original transport. It works, but it needs a sending domain that is
registered and verified with Resend, so it sits behind the other two.

### The sending address for Resend — use a domain you own

**A `*.netlify.app` address cannot be used as the sender.** Netlify controls the
DNS for the whole `netlify.app` zone, so the TXT, MX and CNAME records that
email providers require cannot be added for a Netlify subdomain. Resend will
reject the send with *"the domain is not verified"*, and no amount of
configuration will change that.

So the sender has to be a domain you own. The best candidate is already in
this project: **`plivariverlodge.com`**, which currently does not resolve at
all - nobody owns it, so it is free to register.

Once you own it:

1. **Register the domain** (any registrar - Namecheap, Cloudflare, Porkbun;
   roughly EUR 10-15 a year for a `.com`).
2. **Point it at Netlify**: add `plivariverlodge.com` to the site under
   **Domain management → Add custom domain**. Netlify gives you the nameservers
   or the records to set at the registrar, and issues the SSL certificate.
3. **Verify the domain at Resend**: **Domains → Add Domain →**
   `plivariverlodge.com`, pick the region closest to your guests (Europe),
   and add the DNS records Resend gives you.
4. **Set the sender** to match: `MAIL_FROM = Pliva River Lodge <bookings@plivariverlodge.com>`.

The sender should be a subdomain of the domain you own - Resend recommends it
for deliverability, and it keeps a future marketing mailer separate. So
`bookings@plivariverlodge.com` is the right shape, and the DNS records then go
on `plivariverlodge.com` itself, which you control.

**Until this is done the form still works.** It falls back to WhatsApp and the
guest's own mail app, and the guest is never left without a way to reach the
lodge. Only the confirmation email by email is unavailable.

### Set the environment variables in Netlify

Go to **Site configuration → Environment variables** in the Netlify UI (or
`netlify env:set` from the CLI). Tick the **Functions** scope, and give the
variables a value for **Production** *and* for **Branch deploys** if you want
the branch previews to send mail too.

For the Zoho Mail API (option A):

```bash
netlify env:set ZOHO_CLIENT_ID "1000.xxxxxxxxxxxxxxxxxx"
netlify env:set ZOHO_CLIENT_SECRET "xxxx"
netlify env:set ZOHO_REFRESH_TOKEN "1000.xxxxxxxxxxxxxxxxxxxxxxx"
netlify env:set ZOHO_REGION "eu"
netlify env:set MAIL_TO "milkasobic25@gmail.com"
netlify env:set MAIL_BCC "francesco.capuzzo@zoho.com"
```

**None of these secrets go into the repository.** They live only in Netlify's
environment settings, which are not committed to Git. The test suite checks
that no key material has leaked into the source.

### Redeploy

Environment variables are read at call time, but a new deploy makes the
change visible everywhere at once:

```bash
netlify deploy --prod
```

### Test it

Submit the form on the live site and check:

- Milka's inbox receives the email, with you in **Bcc** — so your address is
  not visible to her and is not exposed if she forwards the enquiry on.
- The email's **Reply-To** is the guest, so pressing reply reaches them.
- The mail arrives **from `guesthousesobic@blink2ask.com`**, not from a
  random transactional sender.
- The enquiry also appears under **Forms** in the Netlify dashboard.

If the provider is not configured, the form still succeeds — it falls back
to WhatsApp and the guest's mail app, and says so.

### Environment variable reference

| Variable | Purpose | Default when unset |
|---|---|---|
| `ZOHO_CLIENT_ID` | Zoho API console client id | none — the function returns `503` and the form falls back |
| `ZOHO_CLIENT_SECRET` | Zoho API console client secret | as above |
| `ZOHO_REFRESH_TOKEN` | The long-lived OAuth refresh token | as above |
| `ZOHO_ACCOUNT_ID` | The numeric Zoho account id | fetched at runtime with `GET /api/accounts` |
| `ZOHO_REGION` | `us` (default), `eu`, `in`, `au`, `jp`, `ca`, `uk` | `us` |
| `ZOHO_FROM_EMAIL` | The From address on a Zoho API send | the mailbox's own address |
| `ZOHO_FROM_NAME` | The display name on the From line | none |
| `SMTP_HOST` + `SMTP_USER` + `SMTP_PASSWORD` | The SMTP mailbox | none — the function returns `503` and the form falls back |
| `SMTP_PORT` | SMTP port | `465` |
| `SMTP_FROM_EMAIL` | The From address on an SMTP send | `SMTP_USER` is not assumed — set it explicitly |
| `SMTP_FROM_NAME` | The display name on the From line | none |
| `SMTP_SECURE` | `ssl` or `starttls` | `ssl` |
| `RESEND_API_KEY` | Auth token for the Resend API | none — the function returns `503` and the form falls back |
| `MAIL_TO` | Who receives the enquiry | `milkasobic25@gmail.com` |
| `MAIL_BCC` | Who is blind-copied on the enquiry | `francesco.capuzzo@zoho.com` |
| `MAIL_FROM` | The verified sender shown to Milka (Resend only) | `Pliva River Lodge <bookings@plivariverlodge.com>` |
| `MAIL_FROM_FALLBACK` | Plain sender address, used if `MAIL_FROM` is unset | none |

## What the function rejects

| Situation | Result |
|---|---|
| `GET` or any method other than `POST` | `405 Method not allowed` |
| Malformed JSON | `400 Bad JSON` |
| Missing name or email | `400 Name and email are required` |
| Honeypot field filled in (a bot) | `200`, nothing sent |
| No transport configured at all | `503`, nothing sent, form falls back |
| The provider rejects the message | `502`, form falls back |
| The provider is unreachable | `502`, form falls back |

The honeypot is a field hidden from guests with the label *"Leave this field
empty"*. Real people never see it and never fill it in; most bots fill in
every field they find.

## Testing it locally

```bash
ZOHO_CLIENT_ID="cid" ZOHO_CLIENT_SECRET="sec" ZOHO_REFRESH_TOKEN="rt" \
  MAIL_BCC="you@example.com" \
  node --experimental-vm-modules netlify/functions/enquiry.mjs
```

Or use `netlify dev`, which runs the function locally with your environment
variables and serves the site with the form pointing at it.

## Changing the email provider

Each transport lives in its own file, so swapping one does not touch the
others:

| Transport | File | Credentials |
|---|---|---|
| Zoho Mail API | `netlify/functions/zoho.mjs` | `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN` |
| SMTP | `netlify/functions/smtp.mjs` | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` |
| Resend | inside `enquiry.mjs` | `RESEND_API_KEY` |

The function's contract with the front end does not change, so `form.js` and
the site stay as they are. To add a fourth provider, add a module with a
`send...()` function and call it from `enquiry.mjs` in the same place the
others are called.

## What the email contains

The enquiry form has two ways of asking how many people are coming, and the
email always says which one the guest used:

| Field | Meaning |
|---|---|
| `people_mode` | `fishing` (the guest ticked Fly fishing) or `booking` |
| `people` | the headline number: the anglers, or the total people |
| `people_label` | the guest's own wording, e.g. "2 adults, 1 child, 1 room" |
| `adults` / `children` / `rooms` | the occupancy counts (booking mode only) |

The email body then reads:

```
Trip type: Fly fishing
People: 2 anglers
Occupancy: 2 anglers
```

or

```
Trip type: General stay
Adults: 2
Children: 1
Rooms: 1
Total people: 3
Occupancy: 2 adults, 1 child, 1 room
```

`reply_to` is always the guest, so pressing reply in Milka's inbox reaches
them. The collaborator is blind-copied, never copied - Milka can forward an
enquiry to a guide or a supplier without exposing that address.
