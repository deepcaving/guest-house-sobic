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
connection open, and outbound SMTP is not available. The standard way to send
email from one is to hand the message to a **transactional email API** over
HTTPS — that is what `netlify/functions/enquiry.mjs` does.

The API call is plain HTTP, so if you would rather use Postmark, SendGrid,
Mailgun or another provider, only the request body in the function changes.

## Setting it up

### 1. The sending address - use a domain you own

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

### 2. Create an account with the email provider

Resend is the simplest to set up and is what the function is written against:

- Sign up at [resend.com](https://resend.com).
- Add your sending domain (or use the Netlify subdomain).
- Create an API key under **API Keys → Create API key**.

### 3. Set the environment variables in Netlify

Go to **Site configuration → Environment variables** in the Netlify UI (or
`netlify env:set` from the CLI). Add:

| Variable | Value | Required |
|---|---|---|
| `RESEND_API_KEY` | Your API key | **yes** |
| `MAIL_TO` | `milkasobic25@gmail.com` | no — this is the default |
| `MAIL_BCC` | `francesco.capuzzo@zoho.com` | no — this is the default |
| `MAIL_FROM` | `Pliva River Lodge <bookings@plivariverlodge.com>` | no — this is the default |

Example:

```bash
netlify env:set RESEND_API_KEY "re_xxxxxxxxxxxxxxxx"
netlify env:set MAIL_TO "milkasobic25@gmail.com"
netlify env:set MAIL_BCC "francesco.capuzzo@zoho.com"
netlify env:set MAIL_FROM "Pliva River Lodge <bookings@plivariverlodge.com>"
```

**The API key never goes into the repository.** It lives only in Netlify's
environment settings, which are not committed to Git. The test suite checks
that no key material has leaked into the source.

### 4. Redeploy

Environment variables are read at deploy time, so a new deploy is needed
after changing them:

```bash
netlify deploy --prod
```

### 5. Test it

Submit the form on the live site and check:

- Milka's inbox receives the email, with you in **Bcc** — so your address is
  not visible to her and is not exposed if she forwards the enquiry on.
- The email's **Reply-To** is the guest, so pressing reply reaches them.
- The enquiry also appears under **Forms** in the Netlify dashboard.

If the provider is not configured, the form still succeeds — it falls back
to WhatsApp and the guest's mail app, and says so.

## Two transports: SMTP and Resend

The function can send by **SMTP** (a normal mailbox) or by the **Resend HTTP
API**. It uses SMTP when SMTP is configured, and falls back to Resend when it
is not.

### SMTP (Zoho)

```
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

**Zoho needs an app password, not the account password.** In Zoho Mail:
Settings -> Mailboxes -> the mailbox -> Edit -> App passwords -> Generate.
The generated password is shown once. If the server answers
`535 Authentication Failed`, the password is wrong or the mailbox has no app
password yet.

### Environment variable reference

| Variable | Purpose | Default when unset |
|---|---|---|
| `RESEND_API_KEY` | Auth token for the email API | none — the function returns `503` and the form falls back |
| `SMTP_HOST` + `SMTP_USER` + `SMTP_PASSWORD` | The SMTP mailbox | none — the function returns `503` and the form falls back |
| `SMTP_PORT` | SMTP port | `465` |
| `SMTP_FROM_EMAIL` | The From address on an SMTP send | `SMTP_USER` is not assumed — set it explicitly |
| `SMTP_FROM_NAME` | The display name on the From line | none |
| `SMTP_SECURE` | `ssl` or `starttls` | `ssl` |
| `MAIL_TO` | Who receives the enquiry | `milkasobic25@gmail.com` |
| `MAIL_BCC` | Who is blind-copied on the enquiry | `francesco.capuzzo@zoho.com` |
| `MAIL_FROM` | The verified sender shown to Milka | `Pliva River Lodge <bookings@plivariverlodge.com>` |
| `MAIL_FROM_FALLBACK` | Plain sender address, used if `MAIL_FROM` is unset | none |

## What the function rejects

| Situation | Result |
|---|---|
| `GET` or any method other than `POST` | `405 Method not allowed` |
| Malformed JSON | `400 Bad JSON` |
| Missing name or email | `400 Name and email are required` |
| Honeypot field filled in (a bot) | `200`, nothing sent |
| No `RESEND_API_KEY` | `503`, nothing sent, form falls back |
| The provider rejects the message | `502`, form falls back |
| The provider is unreachable | `502`, form falls back |

The honeypot is a field hidden from guests with the label *"Leave this field
empty"*. Real people never see it and never fill it in; most bots fill in
every field they find.

## Testing it locally

```bash
RESEND_API_KEY="re_test" MAIL_BCC="you@example.com" \
  node --experimental-vm-modules netlify/functions/enquiry.mjs
```

Or use `netlify dev`, which runs the function locally with your environment
variables and serves the site with the form pointing at it.

## Changing the email provider

Only the request inside `netlify/functions/enquiry.mjs` needs to change. The
endpoint, the payload shape and the response handling are all in one place:

```js
const RESEND_ENDPOINT = "https://api.resend.com/emails";
```

Swap in the other provider's endpoint and body format, and rename
`RESEND_API_KEY` to whatever the provider calls it. The function's contract
with the front end does not change, so `form.js` and the site stay as they
are.

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
