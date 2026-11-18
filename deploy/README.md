# Pliva River Lodge on our own server

The site is now on Netlify (`guesthousesobic.netlify.app`). This folder is
everything needed to put it on a domain of our own, on the server we
already have.

**The short answer on time:** the certificate takes **minutes**. The whole
move is **half a day**, and most of that is not nginx - it is the enquiry
form, because Netlify runs it as a serverless function and a plain server
does not.

## What is actually on Netlify

| Piece | What it is | What it becomes here |
|---|---|---|
| `index.html`, `img/`, the video | plain static files, no build step | the same files, served by nginx |
| `/_headers` | the security headers and the cache rules | an nginx snippet (in `nginx.conf`) ✓ |
| `/.netlify/functions/enquiry` | a serverless function that sends the enquiry by email | a small Node service (`server.mjs`) ✓ |
| `/.netlify/functions/whatsapp-click` | a serverless function that records every WhatsApp click | the same service ✓ |
| Netlify Forms (the backup copy) | the forms inbox in the Netlify dashboard | a JSON file on the server ✓ |

The two functions are written against the standard `Request`/`Response`,
so they do not change at all - `server.mjs` only has to hand them what
Netlify would have handed them.

## The timeline

| Step | Time | Who |
|---|---|---|
| Buy the domain | 5 minutes | Faris |
| DNS: an A record for the domain and a CNAME for `www` | 5 minutes to set, 5-60 minutes to propagate (48 h worst case) | Faris |
| **The certificate** (certbot + Let's Encrypt) | **1-3 minutes** | one command |
| nginx: the files, the headers, HTTP to HTTPS | 30 minutes | the deploy script does most of it |
| The enquiry service: install, the mail secrets, the test | 1-2 hours | `deploy.sh` + `server.mjs` do most of it |
| The mailbox on the new domain, with SPF, DKIM and DMARC | 1 hour | Zoho, with Milka |
| **Total** | **half a day** | |

**The certificate is not the work.** Once the DNS points at the machine and
port 80 is open, `certbot certonly` issues a valid certificate in seconds,
and the browser's "not secure" label goes with it. If Cloudflare's proxy
is in front, use the DNS challenge instead - it works with the proxy on.

## What it costs us to run it ourselves

- The server is ours, so the site goes down when the server does. Netlify's
  edge never does.
- The deploy is no longer a push: it is `rsync` plus a reload.
- The branch previews (`feat--guesthousesobic.netlify.app`) go away.
- We gain: the domain, the email on our own domain, and no Netlify bill.

## The order of work

1. **Buy the domain.** A `.com` is the simplest. A `.ba` domain can only
   be registered by an entity in Bosnia and Herzegovina - worth knowing
   before we spend the money.
2. **Point the DNS at the server** - an A record for the domain and a CNAME
   for `www`. Keep the Netlify site live until the new one is proven.
3. **Run the deploy script** on the server:

   ```bash
   sudo ./deploy/deploy.sh your-domain.example
   ```

   It copies the site into `/var/www/pliva`, installs the service, asks
   certbot for the certificate and enables the nginx site.
4. **Put the mail secrets** in `/etc/pliva-site/env` (the script creates
   the file with the names). They are the same variables Netlify holds:
   `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
   `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`, `ZOHO_CLIENT_ID`,
   `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`, `ZOHO_ACCOUNT_ID`,
   `ZOHO_REGION`, `RESEND_API_KEY`.
5. **Test one enquiry end to end** - it must arrive in Milka's inbox and
   appear in `/var/lib/pliva-site/enquiries.ndjson`.
6. **Only then** point the old Netlify address at the new one, and put
   the domain on the site (the canonical link, the og:url and the JSON-LD
   `url` in `index.html`).

## What the domain fixes while we are here

- **The dead-domain email.** `bookings@plivariverlodge.com` sits on a
  domain with no DNS, so the booking address on the old site could never
  work. On a real domain it is a real mailbox.
- **The DKIM gap.** The mail now goes out as our own domain with SPF,
  DKIM and DMARC, instead of an alias on `netyou.me` with no DKIM at all.
- **"This website is not secure".** Gone with the certificate.

## The one thing that changes on the page

Nothing has to. The page already posts to `/.netlify/functions/enquiry`
and to `/.netlify/functions/whatsapp-click`, and the nginx config keeps
those paths. The only edit the site itself needs is the canonical address
and the og:url once the domain is live - one place in `index.html`
(step 6 above).
