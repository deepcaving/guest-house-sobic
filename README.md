# Pliva River Lodge - Sipovo, Bosnia & Herzegovina

Boutique 7-room riverside lodge on the Pliva River, 2 km below the famous Pliva spring.
Fly fishing, home cooking, wood-fire dining hall, private terrace over the bank.

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
| `PlivaRiverLodge-standalone.html` | Single-file build, images embedded as base64, **English only**. **For Carrd.** |

`PlivaRiverLodge-index.html` used to be a byte-identical copy of `index.html`. It was removed -
two copies of the same page is a trap. If you need one, `cp index.html PlivaRiverLodge-index.html`.

## Languages

Three languages ship with the site: **English (default), Deutsch, Bosanski.**

- The header has a globe dropdown: EN / DE / BS.
- The choice is stored in `localStorage` (`prl_lang`) and survives a reload.
- On a first visit the browser language decides: German browsers get German,
  Bosnian/Croatian/Serbian get Bosnian, everyone else gets English.
- **How it works:** the English text stays in the markup, so the page reads
  correctly even if the JavaScript fails to load. Every translatable element
  carries `data-i18n-key="<key>"`; `i18n.js` looks the key up in `window.I18N`
  and writes the translation in.
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

- [ ] **Register `plivariverlodge.com` or change the address everywhere.**
      The domain does not currently resolve (NXDOMAIN), so
      `bookings@plivariverlodge.com` is undeliverable and the `og:url` and
      the JSON-LD `url` point at a host that does not exist. The phone number
      (+387 65 622 760, Milka Smjestaj Sobic) works, so at least one channel
      is live - but the email is not.
- [ ] If you publish somewhere other than `plivariverlodge.com`, update
      `og:url`, `og:image`, the JSON-LD `url`/`image`, and `site-config.json`.
- [ ] There is **no `canonical` link** on purpose. Add one only once the
      production domain is live and stable - pointing it at a domain that
      does not exist yet would de-index the real site.

## 2026 pricing

| Package | May-Oct | Nov-Dec |
|---|---|---|
| **The Pliva Week** (7 nights / 6 fishing days) | **EUR 1,390** pp | **EUR 1,190** pp |
| **The Companion Week** (7 nights, non-anglers) | **EUR 1,090** pp | **EUR 950** pp |
| **Short Break** (4 nights / 3 fishing days) | **EUR 830** pp | **EUR 730** pp |
| Hosted weeks (named guide) | from EUR 1,790 pp | - |

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
| Outside Travels (SE) | EUR 1,895 / EUR 2,695 | flights included from EU |
| Flyfishing Di Fronzo (CH) | CHF 1,890 | 7n/6f, max 5 |
| Klejch (AT) | from EUR 650 | 4n/3f |
| LTG Pliva (rights holder) | EUR 30/night room, EUR 50/day licence | raw rate card |

## Safety note

The Pliva is a spring creek at **8 °C all year**. No swimming outside the property.
Life vests mandatory for everyone on the water. Wetsuits for any immersion. Rafting is
summer only, age 10+, with adult supervision.

Catch and release. Travel insurance recommended.
