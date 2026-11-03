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

### 1. Verify the sending address

The default sender is **`Pliva River Lodge <bookings@guesthousesobic.netlify.app>`** —
the Netlify domain, so the guest sees the lodge and not a shared sandbox
address. It needs no DNS setup, because the domain already exists.

You still have to **verify it with the email provider** before the provider
will send mail from it. In Resend, that is: **Domains → Add Domain →**
`guesthousesobic.netlify.app`, then add the DNS records it gives you. Netlify
owns the DNS for that subdomain, so the records go in Netlify's
**Domain settings → DNS → Add a record**.

If you would rather send from your own domain, set `MAIL_FROM` to it instead
and verify that one — deliverability is usually better on a domain with
proper SPF and DKIM set up, which you get once the provider has added them.

**If the sender is not verified, the provider rejects the message** and the
form falls back to WhatsApp and the guest's mail app. Nothing is lost, but
the guest does not get the confirmation email.

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
| `MAIL_FROM` | `Pliva River Lodge <bookings@guesthousesobic.netlify.app>` | no — this is the default |

Example:

```bash
netlify env:set RESEND_API_KEY "re_xxxxxxxxxxxxxxxx"
netlify env:set MAIL_TO "milkasobic25@gmail.com"
netlify env:set MAIL_BCC "francesco.capuzzo@zoho.com"
netlify env:set MAIL_FROM "Pliva River Lodge <bookings@guesthousesobic.netlify.app>"
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

## Environment variable reference

| Variable | Purpose | Default when unset |
|---|---|---|
| `RESEND_API_KEY` | Auth token for the email API | none — the function returns `503` and the form falls back |
| `MAIL_TO` | Who receives the enquiry | `milkasobic25@gmail.com` |
| `MAIL_BCC` | Who is blind-copied on the enquiry | `francesco.capuzzo@zoho.com` |
| `MAIL_FROM` | The verified sender shown to Milka | `Pliva River Lodge <bookings@guesthousesobic.netlify.app>` |
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
