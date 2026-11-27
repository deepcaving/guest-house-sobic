# Visitor counting — how many people, and where they came from

**What is on the site now:** the **Umami Cloud** tracker, on the free Hobby
plan — 100,000 events a month, one website, six months of history. It sets
**no cookie**, it collects **no personal data**, and it needs **no cookie
banner**. The snippet sits in `index.html`:

```html
<script defer src="https://cloud.umami.is/script.js" data-website-id="e0da6e27-85e2-4260-9922-2b9dd8c77da5"></script>
```

**Where to look:** <https://cloud.umami.is> — log in with the account you
created, open the website **Pliva River Lodge**, and the dashboard is
there. The live map, the visitors over time, the referring sites, the
countries, the browsers, and the URL parameters.

**The one honest difference:** with Umami Cloud the visit data goes to
Umami's servers, not to this box. It is still anonymous and still
cookie-free, but it is not the same as keeping it at home. If that
matters to you, the **self-hosted** option is at the bottom of this page
and `deploy/analytics-install.sh` puts Umami on this machine, bound to
`127.0.0.1`, where the dashboard is not on the internet at all.

---

## The four options, honestly

| | Cost | Cookie / banner | Where the data goes | Tells you which group sent the visitor |
|---|---|---|---|---|
| **Umami on this box** (recommended) | free forever | none | this server | yes, with the tags in the tracker |
| Google Analytics | free | cookie + consent banner | Google | only if you tag every link, and GA groups Facebook into one bucket |
| Cloudflare Web Analytics | free | none | Cloudflare | no — and it needs the DNS moved to Cloudflare |
| Statcounter | free | cookie | Statcounter | no |

**Google Analytics** is free and it works on any host — it is a line of
script and a login. But three things make it the wrong choice for this
site:

1. **It needs a cookie banner.** Google sends the visitor's IP, a
   device fingerprint and their browsing to Google. Under the EU rules you
   then need a consent dialog and a "reject all" that really works, on a
   page that is trying to sell a fishing trip. Most visitors will refuse,
   and then you count almost nothing.
2. **The data leaves the country.** The people you are advertising to are
   in Germany, France, Italy, the Netherlands and the UK.
3. **It answers the wrong question.** GA will tell you "42 visits from
   Facebook". It will not tell you that 31 of them came from *The Fly
   Fishing Group* and 9 from *Pesca a mosca a Ribnik* — unless every
   post carries its own tagged link, and even then GA buckets the social
   networks together unless you build the campaign report yourself.

**Cloudflare Web Analytics** is the tidiest of the free ones (no cookie,
no banner) but it only works if the domain runs through Cloudflare's
proxy. The DNS for this domain is at Spaceship, and moving it means moving
the MX, SPF, DKIM and DMARC records too — while the mail is the one
channel that has to work. Not worth it for a counter.

**Statcounter** is one line of script and no work at all, but the visitor's
IP goes to a company in Dublin and it sets a cookie.

**Umami on this box** has none of those problems:

* free, open source, no limits that matter for a lodge;
* no cookie, no banner, no consent — it counts a visit, not a person;
* the visitor's IP is hashed and dropped, and nothing is written to the
  visitor's own computer;
* the dashboard is on this machine only — it is not on the internet and
  there is no password for a stranger to try;
* the tracker is served from **this** domain, so an ad blocker that
  matches analytics hostnames cannot see it.

---

## What you get on the dashboard

* **Visitors and page views**, by day and by hour — is anybody looking at
  all, and at what time?
* **Referrers** — the sites that sent the visitor. This is the "from
  where" question, answered.
* **URL parameters** — the `utm_campaign` tag out of the posting link.
  This is the precise answer: *this* group, *this* post.
* **Countries, browsers, devices, operating systems.**
* **The live map** — where the visitors are right now.
* **A list of the pages** that are read.

---

## The self-hosted option (if you want the data to stay here)

On the server, from the clone:

```bash
cd /var/www/plivariverlodge
sudo ./deploy/deploy.sh plivariverlodge.com      # installs the two nginx lines
sudo ./deploy/analytics-install.sh plivariverlodge.com
```

The installer:

1. installs Docker if it is not there, then Umami and PostgreSQL in it;
2. binds both to `127.0.0.1` — **the dashboard is not on the internet**;
3. creates the website and takes its id;
4. writes `/var/www/plivariverlodge/analytics.js` — the file the page
   loads, with that id in it.

Nothing is secret in the repository: the file with the id is written onto
the server, not committed.

**To switch from Cloud to your own box**, three things change: the snippet
in `index.html` becomes `<script src="/analytics.js" defer></script>`, the
nginx template gets the two `location` blocks back (they are in the
history of this file), and the installer writes the id. Say the word and
it is done in one commit.

### Opening the dashboard

The dashboard is only on this machine, so you open it through a tunnel:

```bash
ssh -L 3000:127.0.0.1:3000 root@185.241.151.86
```

then open **http://localhost:3000** in the browser. The first time:
`admin` / `umami` — **change that password at once**, from the account
menu in the top right.

If you want the dashboard on a real address instead, add an A record
`stats` → `185.241.151.86` at Spaceship and ask for a certificate; the
installer does not do it on purpose, because a dashboard with a password
on it is a thing that gets found.

---

## The part that makes it useful: the tagged link

The tracker workbook has a **POSTING LINK** column that builds the address
for each place:

```
https://plivariverlodge.com/?utm_source=facebook&utm_medium=social&utm_campaign=the-fly-fishing-group&utm_content=en
```

* `utm_campaign` — **which place**. It is the target's name, lower case
  and dashed, made by a formula, so the same place always gets the same
  tag.
* `utm_content` — **which language** of the post.
* `utm_source` — the channel: `facebook`, `instagram`, or the name of the
  channel for everything else.

Copy that link into the post. Then the dashboard tells you that *The Fly
Fishing Group* brought 31 visitors and *Pesca a mosca a Ribnik* brought 9,
instead of "42 from Facebook".

The same link goes into the DM, the email and the advertisement, so every
reply can be traced back to the place that produced it.

---

## What it does not do, and does not need to do

* It does not count people. It counts visits. A person who opens five
  pages is one visitor, five page views.
* It does not identify anybody, and it cannot: there is no cookie and no
  identifier, so the same visitor from the same address is "the same
  visit" only in the loosest sense.
* It does not tell you who wrote in. That is what the enquiry form and
  the WhatsApp record already do — the tracker tells you **where they
  came from**, the form tells you **what they wanted**.
* It does not replace the WhatsApp click record. Use both: the click
  record says who pressed the button, the tracker says how many people
  got as far as the page.

---

## The files

| | |
|---|---|
| `deploy/analytics-install.sh` | the installer — run it with sudo on the server |
| `deploy/nginx.conf` | the two `location` blocks that serve `/stats.js` and `/api/send` |
| `index.html` | one line that loads `/analytics.js` |
| `/var/www/plivariverlodge/analytics.js` | written by the installer, not committed |
| `/opt/umami/` | the container, its database and its `.env` (mode 600) |

## If it does not count anything

1. `curl -sI https://plivariverlodge.com/stats.js` — if this is not 200,
   the nginx part is not installed (run `deploy.sh`).
2. `curl -s https://plivariverlodge.com/analytics.js` — if this is a 404,
   the installer has not been run.
3. `cd /opt/umami && docker compose ps` — the app and the database must
   both be up.
4. `curl -s http://127.0.0.1:3000/api/heartbeat` — the answer must be
   `ok`.
5. Umami counts a visit only after the page has been open for a moment.
   Visit the site yourself and wait ten seconds before you look.
