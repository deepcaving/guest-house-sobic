# The nginx configuration of plivariverlodge.com

**What this file is.** The site is a git clone at `/var/www/plivariverlodge`
that nginx serves directly. This file explains how the nginx configuration
that serves it works, line by line, and why it is written the way it is.

**Where the configuration lives**

| What | Where |
|---|---|
| The file below | `/etc/nginx/sites-available/pliva-riverside` |
| The link nginx reads | `/etc/nginx/sites-enabled/pliva-riverside` |
| The site itself | `/var/www/plivariverlodge` (the git clone) |
| The certificates | `/etc/letsencrypt/live/plivariverlodge.com/` |
| The small service | `/opt/pliva-site/deploy/server.mjs`, on `127.0.0.1:8090` |
| The mail secrets | `/etc/pliva-site/env` (root:www-data 640) |
| The enquiry records | `/var/lib/pliva-site/enquiries.ndjson` |

**The nginx on this box is 1.24.0** (Ubuntu 24.04). That number decides
two things below.

---

## The three server blocks

### 1. Port 80 — the ACME block

```nginx
server {
    listen 80;
    server_name plivariverlodge.com www.plivariverlodge.com;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/plivariverlodge;
        default_type "text/plain";
    }

    location / {
        return 301 https://plivariverlodge.com$request_uri;
    }
}
```

Everything is sent to HTTPS, **except** the ACME challenge folder. That
exception is what lets the certificate renew without taking the site down.

The `root` must be the **same folder nginx serves the site from** — here
the git clone itself. certbot writes the challenge file into
`/var/www/plivariverlodge/.well-known/acme-challenge/` and asks Let's
Encrypt to fetch it over plain HTTP. If the root pointed anywhere else,
the fetch would 404 and the renewal would fail.

`^~` means "if this path matches, stop looking for a better match" — it
protects the challenge folder from being swallowed by the redirect or by
the regular location blocks.

### 2. Port 443 — the site

```nginx
listen 443 ssl http2;
```

**`http2` goes on the listen line, never as `http2 on;`.** The standalone
`http2 on;` directive only exists from **nginx 1.25.1**; this box runs
1.24.0, so it refused the whole file with:

```
[emerg] unknown directive "http2" in /etc/nginx/sites-enabled/pliva-riverside:34
```

The older form works on every version, so it is the one to use.

```nginx
ssl_certificate     /etc/letsencrypt/live/plivariverlodge.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/plivariverlodge.com/privkey.pem;
```

The certificate covers both `plivariverlodge.com` and `www.plivariverlodge.com`.
`fullchain.pem` includes the intermediate certificate — without it, some
browsers report the site as incomplete.

```nginx
location ~ /\.git {
    deny all;
}
```

The site is a git clone, so the whole repository — history, branches,
config — sits inside the web root. This one rule keeps it unreadable
from the web. **Never remove it, and never serve the clone without it.**

```nginx
location = /index.html { add_header Cache-Control "public, max-age=0, must-revalidate" always; ... }
location /img/ { add_header Cache-Control "public, max-age=31536000, immutable" always; ... }
```

Two different caching rules, and they are both deliberate:

- The page holds the prices and the contact details, so it must never be
  stale — it is re-checked on every visit.
- The photos never change under the same name, so they are kept for a
  year. `immutable` tells the browser not to even ask.

Everything else (the CSS, the JavaScript) falls through to the default
nginx caching, which is fine.

**The security headers** are the ones Netlify used to send from the
`_headers` file, written out in nginx:

| Header | Why |
|---|---|
| `Strict-Transport-Security: max-age=31536000; includeSubDomains` | after the first visit the browser refuses to go back to plain HTTP |
| `X-Content-Type-Options: nosniff` | the browser does not guess content types |
| `X-Frame-Options: SAMEORIGIN` | the site cannot be framed by someone else |
| `Referrer-Policy: strict-origin-when-cross-origin` | a referrer leaves the site only when it goes to another site |
| `Permissions-Policy: geolocation=(), microphone=(), camera=()` | the site asks for none of these |

`always` matters: without it nginx drops the header on error pages, and
error pages are exactly when you want them.

### The two form paths

The page posts to two places, and nginx has to answer both.

```nginx
location /.netlify/functions/ {
    proxy_pass http://127.0.0.1:8090;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

The **enquiry form** itself posts to `/.netlify/functions/enquiry`. The
path still says "netlify" because that is the path the page has always
used, and the page is shared with the Netlify version of the site. nginx
passes it to the small Node service, which sends the email and writes a
second copy to the ndjson file.

`X-Real-IP` is what makes the record worth having: nginx puts the
visitor's real address there, and the service stores it with the
enquiry.

```nginx
location = / {
    error_page 405 = @backend_post;
    if ($request_method = POST) {
        return 405;
    }
    try_files /index.html =404;
}

location @backend_post {
    proxy_pass http://127.0.0.1:8090;
    ...
}
```

The **backup copy** of every form is posted to `/` (the same address
Netlify watched). A GET of `/` must serve the page, so the POST cannot
be handled in the same block with a plain `proxy_pass` — nginx would
send the page's visitor to the service for everybody.

**Why the named location.** The obvious way to write this is:

```nginx
if ($request_method = POST) {
    proxy_pass http://127.0.0.1:8090;
    proxy_set_header Host $host;   # <-- nginx refuses this
}
```

nginx only allows a handful of directives inside `if`, and
`proxy_set_header` is not one of them. The error is:

```
[emerg] "proxy_set_header" directive is not allowed here in
/etc/nginx/sites-enabled/pliva-riverside:95
```

The way out is the `error_page` trick above: the `if` only does
`return 405`, and nginx hands that status to the named location
`@backend_post`, which is a normal location and may use any proxy
directive it likes.

### 3. Port 443 for www

```nginx
server {
    listen 443 ssl http2;
    server_name www.plivariverlodge.com;
    ssl_certificate ... same file ...
    return 301 https://plivariverlodge.com$request_uri;
}
```

`www.plivariverlodge.com` is a CNAME to the bare domain, so it arrives
here. It gets the same certificate (which covers both names) and is
sent to the bare domain — one address, one version of the site, one
canonical URL for the search engines.

---

## The certificate

A Let's Encrypt certificate lives **90 days**. It is renewed
automatically, and the renewal is what stops the site from showing
"not secure" three months from now.

**What has to be true for that to work:**

1. **The timer must run.** `certbot.timer` checks twice a day (it last
   ran at 12:18 UTC on 18 November 2026, next at 02:56).
2. **The renewal method must still work.** This certificate uses the
   **webroot** method: certbot writes a file into
   `/var/www/plivariverlodge/.well-known/acme-challenge/` and Let's
   Encrypt fetches it over port 80. That needs the ACME location above
   to point at the right folder.
3. **nginx must reload afterwards**, or the new certificate is on disk
   but the server keeps serving the old one. The hook
   `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh` does that
   after every renewal.

**Why the other certificates on this box had been failing for months.**
Six of them had expired — `aicoder.click`, `blink2ask.com` (twice),
`notion-prod-img.netyou.me`, `ntpl.cc`, `translatero.cc`. Two separate
causes:

- **Five of them used the nginx plugin.** That plugin runs `nginx -t`
  before it renews anything. While the pliva configuration was broken,
  `nginx -t` failed, so certbot refused to renew **anything at all** —
  not just the certificate it was working on. One broken file on the
  box had silently stopped the renewal of every other site on it.
- **Two of them used the standalone method** (`aicoder.click` and
  `blink2ask.com-0001`). That method starts its own web server on port
  80 — which nginx already holds. The error is
  *"Could not bind TCP port 80 because it is already in use by another
  process"*. It can never work while nginx runs, so it has to be
  switched to the nginx plugin:

  ```bash
  sudo certbot certonly --nginx -d aicoder.click --cert-name aicoder.click --expand \
      --non-interactive --agree-tos -m you@example.com
  ```

**The tools**

| Command | What it does |
|---|---|
| `sudo ./deploy/cert-guard.sh` | lists every certificate, how it renews, whether the folder it needs is there, and runs a dry-run renewal that proves it |
| `sudo certbot certificates` | the short version: what is valid, what is expired |
| `sudo certbot renew` | renews everything that is due (an expired certificate is due) |
| `systemctl list-timers certbot.timer` | shows that the timer is armed |
| `sudo ./deploy/drop-site.sh <domain>` | takes a site off the machine for good |

**The dry run is the honest test.** `certbot renew --dry-run` asks
Let's Encrypt's staging server for a certificate, so it proves the whole
path works without touching the live certificates. The guard counts the
results and says plainly how many succeeded and how many failed.

---

## Taking a site off the machine

```bash
sudo ./deploy/drop-site.sh translatero.cc
```

It moves every nginx file that mentions the domain into
`/etc/nginx/backups/<domain>/` (**nothing is deleted**), revokes the
certificate so Let's Encrypt stops honouring it, deletes the
certificate and its renewal so certbot stops trying, and reloads nginx.

The domain itself still has to be dropped at the registrar — the script
cannot do that.

---

## The traps on this box, in one list

1. **`http2 on;` does not exist before nginx 1.25.1.** Put http2 on the
   `listen` line.
2. **`proxy_set_header` is not allowed inside `if`.** Use a named
   location with `error_page`.
3. **A broken nginx configuration stops every certbot renewal on the
   box**, not just the one being renewed, when the nginx plugin is in
   use. Run `sudo nginx -t` first whenever you change nginx.
4. **The standalone method cannot renew while nginx is running.** Use
   the nginx plugin or the webroot method instead.
5. **nginx loads every file in `sites-enabled`, whatever its name.**
   A `.backup` file left there is still a configuration file.
6. **The web root is a git clone.** `deny all` on `/.git` is not
   optional.
7. **The service runs as `www-data`** and the secrets are
   `root:www-data 640` — a secret file that is `600 root` cannot be
   read by the service, and the service dies at startup.
8. **`sudo` resets `PATH`.** Use the full path to a program after a
   `sudo`, or keep the command in one `sudo` call.
9. **certbot writes to `/var/log/letsencrypt`** — every certbot command
   needs `sudo`, or it fails with a permission error on the lock file.
10. **The deploy publishes whatever branch is checked out.** `sudo git
    pull` on the server is the deploy; make sure the branch is the one
    you want to publish.
