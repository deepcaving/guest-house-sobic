# Pliva River Lodge - Sipovo, Bosnia & Herzegovina

Boutique 7-room riverside lodge on the Pliva River, 2 km below the famous Pliva spring.
Fly fishing, home cooking, wood-fire dining hall, private terrace over the bank.

**Live site:** https://guesthousesobic.netlify.app/

## Structure

| Path | What it is |
|---|---|
| `index.html` | **The live site.** Full version - references `img/`, plays the video, has the language switcher and the enquiry form. |
| `i18n-data.js` | Translation dictionary (EN / DE / BS) - 186 keys. |
| `i18n.js` | The language switcher. Reads `data-i18n-key` attributes, persists the choice in `localStorage`. |
| `form.js` | The enquiry form. Posts to Netlify Forms and opens WhatsApp with the details filled in. |
| `site-config.json` | Phone, email, WhatsApp link and site URL in one place. `build_standalone.py --check` verifies the site still agrees with it. |
| `img/` | All photos + `property-tour.mp4` (the 53-second walkthrough) + `og-image.jpg` (social share card). |
| `favicon.svg` | The wave mark from the header. |
| `build_standalone.py` | Builds the single-file Carrd version. |
| `check_i18n.py` | Validates the dictionary against the HTML - missing keys, missing languages, markup drift. |
| `PlivaRiverLodge-standalone.html` | Single-file build, images embedded as base64, **English only**. **For Carrd.** |
| `sitemap.xml`, `robots.txt`, `site.webmanifest` | Search and install metadata. |
| `404.html` | The not-found page, in the site's own styling. |
| `_headers` | Netlify caching and security headers. |
| `marketing/` | The marketing and outreach kit - every post, DM and email ready to copy-paste. See below. |

`PlivaRiverLodge-index.html` used to be a byte-identical copy of `index.html`. It was removed -
two copies of the same page is a trap. If you need one, `cp index.html PlivaRiverLodge-index.html`.

## The marketing kit

`marketing/` holds the whole go-to-market kit: Google Business Profile setup, the
Instagram grid, the Facebook Page and groups playbook, 12 cold-DM templates in
English, German and Italian, the first blog post, the email templates, the
WhatsApp Business setup, the host's English card, the 30-day calendar and the
TripAdvisor rebuild.

The files in `marketing/` are the **master copy** and keep `{{PLACEHOLDER}}`
tokens. `python3 marketing/render.py` writes a ready-to-paste version of each
one into `marketing/out/` using the values in `site-config.json` - always copy
from there, not from the master. Set `"email_live": true` in
`site-config.json` once the real booking inbox is in place and the warning
banners disappear from the generated files.


## Languages

Three languages ship with the site: **English (default), Deutsch, Bosanski.**

- The header has a globe dropdown: EN / DE / BS.
- The choice is stored in `localStorage` (`prl_lang`) and survives a reload.
- On a first visit the browser language decides: German browsers get German,
  Bosnian/Croatian/Serbian get Bosnian, everyone else gets English.
- **The language is also part of the URL.** `?lang=de` opens the German page
  and `?lang=bs` the Bosnian one, whatever the visitor's browser is set to.
  That is what lets you send a German angler a link that actually shows the
  German page. The address bar updates when the language changes, so copying
  the URL always copies the version on screen.
- **How it works:** the English text stays in the markup, so the page reads
  correctly even if the JavaScript fails to load. Every translatable element
  carries `data-i18n-key="<key>"`; `i18n.js` looks the key up in `window.I18N`
  and writes the translation in. Form placeholders use `data-ph="<key>"`.
- **The Carrd build is English only** - the free tier strips `<script>`, so a
  dropdown would be a dead button. The DE/BS copy lives in `i18n-data.js` and
  is ready to use the moment the site is hosted somewhere that allows JS
  (Netlify, GitHub Pages, Cloudflare Pages).

To change a translation, edit `i18n-data.js` - the keys map to the
`data-i18n-key` attributes in `index.html`.

> When you edit a translation, keep the markup inside the value in step with
> the markup in `index.html`. `i18n.js` writes the dictionary value over the
> element, so a `<b>` that is in the HTML but missing from the dictionary
> disappears the moment the page loads.

Run `python3 check_i18n.py` after any change to the dictionary. It checks that
every key exists, that every language has a translation, that the markup in
each translation matches the English original, and that the English text still
matches the HTML. Those are the four ways this file has broken before.

## The enquiry form

The form in `index.html` is a **Netlify Form** (`data-netlify="true"`, a honeypot
field, and a hidden `form-name` input). With JavaScript off the browser posts it
normally and Netlify stores it. With JavaScript on, `form.js` does two things
at once:

1. POSTs the enquiry to Netlify in the background, so it also lands in the
   Netlify dashboard.
2. Opens WhatsApp with the enquiry already written out.

WhatsApp leads because that is the channel that actually gets answered. The
WhatsApp number, the phone number and the email address all live in
`site-config.json`; `data-wa` on the `<form>` carries the WhatsApp link.

If you move the site off Netlify, the form still works - WhatsApp is the
fallback and the POST just fails quietly in the background.


## Regenerating the Carrd build

From the source folder, run:

```
python3 build_standalone.py
```

Needs Pillow (`pip install Pillow`).

It base64-embeds every image - downscaling and re-compressing each one to the
size it is actually displayed at, so the single file stays around 4 MB instead
of the ~8 MB the raw assets would produce. It swaps the video for its poster,
drops the gallery lightbox links (each photo is embedded once, not twice),
removes the language switcher and every `data-i18n-*` attribute, removes the
executable `<script>` tags (the JSON-LD block is kept - it is inert and still
useful to search engines), inlines the favicon, and replaces the enquiry form
with a static WhatsApp / email / phone call to action.

Options: `--max-width`, `--quality`, and `--check` (verify `index.html`
against `site-config.json` without building).

## Deploying to Netlify

GitHub is already connected. Build settings:

- Branch: `main`
- Base directory: *leave empty*
- Build command: *leave empty*
- **Publish directory: `.`**
- Functions directory: *leave empty*

Netlify serves `index.html` from the repo root automatically. Submissions to
the enquiry form show up under **Forms** in the Netlify dashboard.

**Live URL:** https://guesthousesobic.netlify.app/

### Branches and deploys

Netlify deploys **every** branch, automatically, to its own preview URL
(`deploy-preview-<n>--guesthousesobic.netlify.app`). It does that in the
background and it does not touch your production site.

**Do not switch the production branch in the Netlify UI to publish a branch.**
Changing it makes Netlify treat that branch as production: your `main` deploys
become previews, the real URL starts serving the wrong code, and switching it
back leaves stale deploys behind. Leave the production branch on `main`.

The two things you might actually want:

| Goal | What to do |
|---|---|
| See a branch on a real URL | Let Netlify build the deploy preview and open it from the deploy list. Free, automatic, no settings to change. |
| A permanent second URL for one branch | Create a **second Netlify site** from the same GitHub repo and set *that* site's branch to the branch in question. Now the two sites are independent. |

For this project the cleanest end state is: **merge the branch into `main`**.
One site, one URL, all four languages behind the switcher. A permanent
separate site for one language splits the content, splits the SEO, and gives
guests two different URLs for the same lodge.


## Deploying to Carrd (free)

1. carrd.co -> New Site -> delete default sections
2. Add a **Code** section
3. Paste the entire contents of `PlivaRiverLodge-standalone.html`
4. Set page background to `#122F45`
5. Publish

Note: the Carrd version shows a poster image instead of the video (base64-encoding a 5 MB
video is impractical), and the enquiry form is replaced by WhatsApp / email / phone
buttons. Use the Netlify/GitHub version for the working video and the real form.

## Before publishing - fix these

- [ ] **Set a real booking email.** `bookings@plivariverlodge.com` is on a
      domain that does not resolve, so mail to it is lost. The phone number
      (+387 65 622 760, Milka Smjestaj Sobic) works and WhatsApp works, so
      at least two channels are live - but the email is not.
      Change `"email"` in `site-config.json` and in the two places in
      `index.html` (the contact block and the JSON-LD), then set
      `"email_live": true` and run `python3 marketing/render.py`.
- [x] **The site URL is `https://guesthousesobic.netlify.app/`.** It is set in
      `site-config.json` and mirrored in `og:url`, `og:image`, `twitter:image`,
      the JSON-LD `url`/`image` and the `<link rel="canonical">`.
      `build_standalone.py --check` fails if the two drift apart.
- [ ] **If you buy `plivariverlodge.com` later**, update `site_url` in
      `site-config.json`, the same five places in `index.html`, `sitemap.xml`
      and `robots.txt`, then re-run `python3 build_standalone.py`.
- [x] **There is a `canonical` link**, pointing at the live host. It was
      deliberately left off before, because the production domain did not
      exist and pointing at a dead host de-indexes the real site.

## 2026 pricing

The site's rate card is the single source of truth. The planning documents
recommended €1,490 for The Pliva Week; the site was deliberately set lower in
the "2026 pricing" commit and the whole card was rebuilt around it - the
group-of-two, solo and November-December tiers all hang off the headline
number. The marketing copy in `marketing/` was written to match the site, not
the other way round, so nothing you post contradicts what a guest reads when
they open the link.

| Package | May-Oct | Nov-Dec |
|---|---|---|
| **The Pliva Week** (7 nights / 6 fishing days) | **EUR 1,390** pp | **EUR 1,190** pp |
| **The Companion Week** (7 nights, non-anglers) | **EUR 1,090** pp | **EUR 950** pp |
| **Short Break** (4 nights / 3 fishing days) | **EUR 830** pp | **EUR 730** pp |
| Hosted weeks (named guide) | from EUR 1,790 pp | - |

**Group-of-two and solo rates:** The Pliva Week EUR 1,590 / EUR 2,090 ·
The Companion Week EUR 1,230 / EUR 1,630 · Short Break EUR 930 / EUR 1,230.

**Room-only rates** (per night, breakfast included):
double/twin EUR 85 / single EUR 70 / triple EUR 110 / whole house EUR 900 (16 guests)
Half board EUR 32 pp/day / full board EUR 52 pp/day / equipment rental EUR 22/day

**Charged separately:**
- Pliva fishing licence EUR 50/day (non-resident rate) - **included in the fishing packages**,
  arranged by us; for room-only bookings we buy it for you on arrival
- Tourist tax EUR 2 per person per night (children under 12 free)
- Flights, alcoholic drinks, insurance, tips

### Why the licence is shown separately
LTG holds the fishing rights on the Pliva. Non-resident guests pay **EUR 50/day**
(LTG's own guests pay EUR 20). Every package price above already absorbs it - we show
it because there is no hidden fee.

## Market reference (verified 25 Oct 2026)

| Operator | Price pp | Notes |
|---|---|---|
| Paradise FlyFishing (FR) | EUR 1,790 | 7n/6f, group of 4, all-inclusive |
| Outside Travels (DE) | EUR 1,895 / EUR 2,695 | flights included from EU airports |
| Flyfishing Di Fronzo (CH) | CHF 1,890 | 7n/6f, max 5 |
| Klejch (AT) | from EUR 650 | 4n/3f |
| LTG Pliva (rights holder) | EUR 30/night room, EUR 50/day licence | raw rate card |

The market pays EUR 1,400-1,800 for a 7-night all-inclusive week. Most of
these operators sell the river; the lodge sells the property on the bank.

## Safety note

The Pliva is a spring creek at **8 °C all year**. No swimming outside the property.
Life vests mandatory for everyone on the water. Wetsuits for any immersion. Rafting is
summer only, age 10+, with adult supervision.

Catch and release. Travel insurance recommended.
