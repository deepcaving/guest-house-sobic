# plivariverlodge.com — the setup, step by step

The domain is bought. This is the order of operations, and every command
you have to type.

**The short version:** DNS first (it is the only step that has to wait),
then the server, then the certificate (seconds, once DNS points), then
the address inside the site, then the email records, and finally the
forwarding to Milka's Gmail.

---

## Step 1 — DNS at the registrar (you, 15 minutes)

Open the DNS zone for `plivariverlodge.com` at whoever you bought it
from. Add these records.

### For the website

| Type | Name | Value | Notes |
|---|---|---|---|
| A | `@` | the IP of your server | the bare domain |
| CNAME | `www` | `plivariverlodge.com` | so www works too |

**If your DNS is behind Cloudflare's orange cloud, turn it off (grey
cloud) for now.** The certificate in step 3 proves who you are over plain
HTTP, and a proxy in front of it breaks that proof. Turn the proxy on
again afterwards if you want it — or use the DNS challenge instead
(step 3 says how).

### For the email (Zoho)

| Type | Name | Value | Notes |
|---|---|---|---|
| MX | `@` | `mx.zoho.com` — priority 10 | Zoho's mail server |
| MX | `@` | `mx2.zoho.com` — priority 20 | the second one |
| MX | `@` | `mx3.zoho.com` — priority 50 | the third one |
| TXT | `@` | `v=spf1 include:zohomail.com ~all` | SPF: only Zoho may send as this domain |
| TXT or CNAME | **the exact DKIM host Zoho gives you** | the long `v=DKIM1; …` value | DKIM — copy both parts exactly from the Zoho console |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:contact@plivariverlodge.com` | start permissive; tighten later |

**Take the MX and DKIM values from the Zoho console, not from here.**
Zoho's own documentation says the MX priorities and the DKIM selector
name differ between data centres and setups, and the authoritative list
is under **Admin > Mail Settings > Tools and Configurations > MX** and on
the domain's setup page. The values above are the usual ones for a
zoho.com (global) account — the same ones your netyou.me domain already
uses — but copy what your console shows.

**The DKIM record must be published AND switched on in Zoho.** Publishing
the TXT record alone leaves the signature inert — this is the trap that
made the mail from `netyou.me` arrive unsigned. Do both:

1. In Zoho: **Admin > Domains > Add a domain** → `plivariverlodge.com`
   → Zoho shows you the exact MX, SPF and DKIM records → add them in DNS.
2. Zoho verifies them (a few minutes, sometimes an hour).
3. In Zoho: **Admin > Domains > the domain > Mailboxes/Aliases** → create
   the alias **`contact@plivariverlodge.com`**, and point it at Milka's
   Gmail (`milkasobic25@gmail.com`) — that is the address the enquiries
   will arrive in.
4. Zoho shows you the DKIM record for the domain (the host and the long
   value) → publish it in DNS → then **enable the signature for that
   alias** in Zoho. Both halves, in that order, or the mail goes out
   unsigned and Gmail will not let you send as the address.

---

## Step 2 — the server: clone, then one command

**Yes, clone it there.** The repository is public, so it needs no token:

```bash
sudo git clone -b feat/own-server-deploy \
  https://github.com/deepcaving/guest-house-sobic.git /var/www/plivariverlodge
cd /var/www/plivariverlodge
sudo ./deploy/deploy.sh plivariverlodge.com
```

**Every git command on this clone needs `sudo`.** The clone belongs to
root, so a plain `git pull` answers *"cannot open '.git/FETCH_HEAD':
Permission denied"* ✓. The deploy is therefore:

```bash
cd /var/www/plivariverlodge && sudo git pull
```

and the script also runs with sudo (it writes to /etc and /opt) ✓.

(The branch is named because that is where this deployment kit lives
today. Once the three branches are merged into `main`, clone `main` —
or on the server: `git checkout main && git pull`.)

**The clone IS the web root.** nginx serves the repository straight from
`/var/www/plivariverlodge`, so from now on the whole deploy is:

```bash
cd /var/www/plivariverlodge && sudo git pull
```

No copying, no rsync, nothing to drift. The nginx configuration denies
`/.git` so the repository is never readable from the web.

**Which branch?** `main` is what the site is today, and the branch you
clone above carries the same site content plus this kit — so the first
thing the server serves is exactly what is live now. The gallery (84
photographs) and the licence correction live on two more branches. Say
the word and I merge all three into `main`; then the server checks out
`main` and carries everything.

**Two things to know about that script:**

- **The mail secrets.** It creates `/etc/pliva-site/env` (root-only) with
  the variable names in it. Fill it in before the form can send anything:

  ```
  SMTP_HOST=smtppro.zoho.com
  SMTP_PORT=465
  SMTP_SECURE=ssl
  SMTP_USER=francesco.capuzzo@zoho.com
  SMTP_PASSWORD=your Zoho app password
  SMTP_FROM_EMAIL=contact@plivariverlodge.com
  SMTP_FROM_NAME=Pliva River Lodge
  ```

  `SMTP_USER` must be the account that owns the app password (an alias
  cannot authenticate — a wrong one gives `535`). `SMTP_FROM_EMAIL` is
  the alias, which is exactly what Zoho allows once the domain is
  verified on the account.

  **Leave the `ZOHO_*` variables out of that file.** The Zoho Mail API
  is tried first, and this plan cannot send to an outside address at all
  — it answers with an empty 404. The SMTP transport is the one that
  works, and it is the one that can send as `contact@plivariverlodge.com`.

- **It does not touch the other site on that box.** The nginx file it
  writes is a separate `server_name` block, so the service already
  running there keeps its own configuration.
- **The secrets do not come with the clone.** The `.env` file is never
  committed, so the mail secrets live only in `/etc/pliva-site/env`
  (root-only) and the certificate only in `/etc/letsencrypt`.

After the script, the service must be up:

```bash
systemctl status pliva-site
tail -f /var/log/nginx/access.log
```

---

## Step 3 — the certificate (seconds)

The script already did it. Check:

```bash
curl -I https://plivariverlodge.com/
```

You are looking for `HTTP/2 200` and **no certificate warning**. If
certbot refused, it was almost always the DNS not pointing here yet:

```bash
dig +short plivariverlodge.com
sudo certbot certonly --webroot -w /var/www/plivariverlodge \
  -d plivariverlodge.com -d www.plivariverlodge.com \
  --non-interactive --agree-tos -m postmaster@plivariverlodge.com
sudo nginx -t && sudo systemctl reload nginx
```

If you put the Cloudflare proxy back on and the certificate will not
issue, use the DNS challenge instead (it works with the proxy on):

```bash
sudo certbot certonly --dns-cloudflare \
  -d plivariverlodge.com -d www.plivariverlodge.com \
  --non-interactive --agree-tos -m postmaster@plivariverlodge.com
```

Renewal is automatic — check it is armed:

```bash
sudo systemctl status certbot.timer
```

---

## Step 4 — point the site at the new address (after it is live)

Only once `https://plivariverlodge.com/` actually answers:

```bash
./deploy/set-domain.sh plivariverlodge.com
```

It rewrites the canonical link, `og:url`, `og:image`, `twitter:image`,
the JSON-LD, `robots.txt`, `sitemap.xml` and `site-config.json`, and
rebuilds the standalone file. Then push it — that is what puts the new
address in front of Google.

---

## Step 5 — the enquiry form, end to end

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","dates":"12-19 December"}' \
  http://127.0.0.1:8080/.netlify/functions/enquiry
```

It should answer `{"ok":true,...,"transport":"smtp"}` ✓ (use 8090 if the
script moved it there).

The form posts to `/.netlify/functions/enquiry`; the nginx configuration
keeps that path and sends it to the service on port 8080 ✓ (or 8090, if
8080 was already busy on the box — the script says which it used ✓).
So the page
does not change — only the server behind it does.

Test it with a real message:

1. Fill in the enquiry form on the live site and send it.
2. It must arrive in **Milka's Gmail** (`milkasobic25@gmail.com`) with
   the sender **`contact@plivariverlodge.com`** ✓.
3. It must also appear in the backup file on the server:

   ```bash
   tail -2 /var/lib/pliva-site/enquiries.ndjson
   ```

   That is the copy Netlify used to keep in its forms inbox. It is now a
   file on the server, so nothing is lost if the mail server is down.

If the mail does not arrive, check the service log — it names the reason
(Zoho host, credentials, a missing alias):

```bash
journalctl -u pliva-site -n 50 --no-pager
```

---

## Step 6 — let guests write without seeing her Gmail

Later, when Milka's Gmail is set up to send as the alias:

1. In Gmail: **Settings > Accounts > Add another email address** →
   add `contact@plivariverlodge.com` → "Send mail as" → **Send through
   your SMTP server (smtppro.zoho.com)** → port **465**, TLS → username
   `francesco.capuzzo@zoho.com`, password = the Zoho **app password**
   (not her Gmail password).
2. Gmail sends a confirmation to `contact@plivariverlodge.com` — it goes
   to Milka's Gmail through the alias, she clicks the link ✓.
3. Set it as the default "Send mail from" ✓.

**The DKIM record from step 1 is what makes this work.** With it
published and the signature enabled in Zoho, mail sent through Zoho's
SMTP is signed for the domain, and Gmail will not add "via
guesthousesobic.netlify.app" or "via zoho.com" to the From line — so
the guest sees `contact@plivariverlodge.com` and nothing else ✓.

---

## Step 7 — let the old address point at the new one

Keep `guesthousesobic.netlify.app` alive for now — it is the fallback if
the server ever goes down. When you are happy, add a redirect in the
Netlify dashboard (or a `_redirects` file in the repository):

```
/*  https://plivariverlodge.com/:splat  301
```

**Do this last**, so there is never a moment when both addresses serve
the site and Google sees two copies.

---

## Step 8 — every later change

```bash
cd /var/www/plivariverlodge && sudo git pull
```

That is the deploy for the website. Two things live outside the
repository and are not changed by a pull:

- **the mail secrets** — `/etc/pliva-site/env`;
- **the small service** — if `netlify/functions/` changes in a future
  commit, copy it across and restart:

  ```bash
  sudo cp /var/www/plivariverlodge/netlify/functions/*.mjs /opt/pliva-site/netlify/functions/
  sudo cp /var/www/plivariverlodge/deploy/server.mjs /opt/pliva-site/deploy/server.mjs
  sudo systemctl restart pliva-site
  ```

  (The service lives at `/opt/pliva-site/deploy/server.mjs` so the layout
  under `/opt` mirrors the repository — that is what lets the import
  inside it find the functions ✓.)

  (re-running `./deploy/deploy.sh` does both).

---

## The order, in one line

DNS → server → certificate → the address inside the site → the form test
→ Gmail sending as the alias → the Netlify redirect.
