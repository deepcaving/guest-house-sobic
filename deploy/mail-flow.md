# The mail flow of plivariverlodge.com

**Who the addresses are**

| Address | What it is |
|---|---|
| `contact@plivariverlodge.com` | the address of the lodge — the one guests write to and the one guests must see in the `From` line |
| `milkasobic25@gmail.com` | Milka's own inbox — where enquiries are read and answers are written |
| `guesthousesobic@netyou.me` | the collaborator's alias — blind-copied on every enquiry, never copied |
| `francesco.capuzzo@zoho.com` | the Zoho mailbox that owns the app password, and the login name for SMTP |

---

## The four hops

```
1. the guest fills in the form on the site
        │
        ▼
2. the server sends ONE email
        from   contact@plivariverlodge.com
        to     milkasobic25@gmail.com          (Milka reads it)
        bcc    guesthousesobic@netyou.me       (the collaborator, blind)
        reply-to  the guest's own address
        │
        ▼
3. a guest writes to contact@plivariverlodge.com
        │
        ▼
4. Milka answers, and the guest sees
        from   contact@plivariverlodge.com
```

Hop 2 happens on the server. Hops 3 and 4 happen through **Gmail's third-party
address**, which is why the incoming server below matters.

---

## The exact settings

### Gmail: add contact@plivariverlodge.com as a third-party address

Gmail → ⚙️ Settings → *See all settings* → **Accounts** → *Add another email
address* → **Add a third-party email address**.

| Field | Value |
|---|---|
| Username | `contact@plivariverlodge.com` |
| Password | the Zoho **app password** for that mailbox |
| **Incoming** server | `imap.zoho.com` |
| Incoming port | `993` |
| Incoming encryption | `SSL` |
| **Outgoing** server | `smtppro.zoho.com` |
| Outgoing port | `465` |
| Outgoing encryption | `SSL` |
| Outgoing username | `francesco.capuzzo@zoho.com` |
| Outgoing password | the same Zoho app password |

**The incoming server is Zoho's, not Gmail's.** The address belongs to the
Zoho account, so that is where Gmail must fetch the mail from. `imap.gmail.com`
would ask Gmail for mail addressed to a Zoho domain, which of course it does
not have.

Gmail then sends a verification mail to `contact@plivariverlodge.com`; it
arrives in the inbox Gmail has just connected, and the code confirms it.

### The server: /etc/pliva-site/env

```
SMTP_HOST=smtppro.zoho.com
SMTP_PORT=465
SMTP_SECURE=ssl
SMTP_USER=francesco.capuzzo@zoho.com
SMTP_PASSWORD=<the app password>
SMTP_FROM_EMAIL=contact@plivariverlodge.com
SMTP_FROM_NAME=Pliva River Lodge
MAIL_TO=milkasobic25@gmail.com
MAIL_BCC=guesthousesobic@netyou.me
```

Change a value with:

```bash
sudo ./deploy/set-env.sh MAIL_BCC      # asks for the value, hidden
sudo ./deploy/env-keys.sh              # shows what is set, secrets masked
```

---

## Three things Zoho insists on

**1. SMTP wants an APP password, not the account password.**
`535 5.7.8 Authentication Failed` is what Zoho answers when the regular
account password is used — the same answer it gives for a wrong password.
The fix is a separate password, twelve characters long, shown once:

> Zoho Mail → Settings → Mailboxes → the mailbox → Edit → **App Passwords** →
> Generate

The length is a useful check: `env-keys.sh` prints how many characters each
secret has, and an app password is **exactly twelve**.

**2. The address must be a real mailbox, not an alias.**
Gmail logs into the incoming server with the address it is adding. An alias
on another mailbox has no password of its own and cannot log in, so
`contact@plivariverlodge.com` has to be a mailbox of its own:

> Zoho Admin → Users → Add User → `contact@plivariverlodge.com`

**3. DKIM has to be switched on.**
The DNS record is published (`zmail._domainkey.plivariverlodge.com`), but a
published record does nothing until the signature is enabled:

> Zoho Admin → Domains → plivariverlodge.com → **DKIM** → Verify / Enable

Without it, a reply that claims to be from the lodge's domain but carries no
signature is exactly what a mail filter rejects.

---

## The host depends on the kind of account

| Host | For |
|---|---|
| `smtppro.zoho.com` | a **paid** account on a custom domain — this one |
| `smtp.zoho.com` | a personal account, or a free organisation account |
| `imap.zoho.com` | both, for incoming mail |

Asking the wrong one is refused with the very same `535`, which is why it
looks like a password problem. The transport tries the sibling host by
itself when the login is refused.

---

## What each failure means

| What you see | What it is |
|---|---|
| `535 5.7.8 Authentication Failed` | the wrong kind of password (use an app password), or the wrong host |
| `550 5.7.1 Sender is not allowed to relay emails` | the From address is not one the mailbox may send as |
| `404` with an empty body, from the Zoho API | the free plan cannot send to an outside address through the API — use SMTP |
| `Connection refused` on port 25 | port 25 is blocked by the host (AWS and most providers block it); use 465 or 587 |
| `Could not bind TCP port 80` | certbot's standalone method wants port 80 for itself while nginx holds it |

---

## The tests

The form, end to end, from anywhere:

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","dates":"12-19 December"}' \
  https://plivariverlodge.com/.netlify/functions/enquiry
```

The answer must contain `"transport":"smtp"`. `"transport":"zoho-api"` means
the API was tried first — it only works on a paid plan. An error names the
transport that failed.

On the server itself:

```bash
sudo journalctl -u pliva-site -n 30 --no-pager
sudo tail -n 3 /var/lib/pliva-site/enquiries.ndjson
```
