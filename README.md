# Pliva River Lodge - Sipovo, Bosnia & Herzegovina

Boutique 7-room riverside lodge on the Pliva River, 3 km below the famous Pliva spring.
Fly fishing, home cooking, wood-fire dining hall, private terrace over the bank.

## Structure

| Path | What it is |
|---|---|
| `index.html` | **The live site.** Full version - references `img/`, plays the video, has the language switcher. |
| `i18n-data.js` | Translation dictionary (EN / DE / BS) - 155 keys. Generated file. |
| `i18n.js` | The language switcher. Reads `data-i18n-key` attributes, persists the choice in `localStorage`. |
| `img/` | All photos + `property-tour.mp4` (the 53-second walkthrough) + `angler-pliva.jpg` |
| `PlivaRiverLodge-standalone.html` | Single-file build, images embedded as base64, **English only**. **For Carrd.** |
| `PlivaRiverLodge-index.html` | Copy of `index.html` for convenience |

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

## Regenerating the Carrd build

From the source folder, run `python3 build_standalone.py`. It base64-embeds
every image, swaps the video for its poster, removes the language switcher and
all `<script>` tags, then writes `PlivaRiverLodge-standalone.html`.

## Deploying to Netlify

GitHub is already connected. Build settings:

- Branch: `main`
- Base directory: *leave empty*
- Build command: *leave empty*
- **Publish directory: `.`**
- Functions directory: *leave empty*

Netlify serves `index.html` from the repo root automatically.

## Deploying to Carrd (free)

1. carrd.co -> New Site -> delete default sections
2. Add a **Code** section
3. Paste the entire contents of `PlivaRiverLodge-standalone.html`
4. Set page background to `#122F45`
5. Publish

Note: the Carrd version shows a poster image instead of the video (base64-encoding a 5 MB
video is impractical). Use the Netlify/GitHub version for the working video.

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

## Before publishing - fill these in

Search `index.html` and `PlivaRiverLodge-standalone.html` for:

- `bookings@plivariverlodge.com` -> a real inbox you control
- The phone number is already set to **+387 65 622 760** (Milka Smjestaj Sobic)
- The enquiry form is a **visual placeholder** - it does not send. Replace it with a
  WhatsApp button (best converting), Formspree, or Netlify Forms.

### Enabling Netlify Forms
In `index.html` change the form tag to:
```html
<form name="enquiry" method="POST" data-netlify="true" netlify-honeypot="bot-field">
```
add `<input type="hidden" name="form-name" value="enquiry">`, add a honeypot field
`<p style="display:none"><label>Leave blank: <input name="bot-field"></label></p>`,
and remove the placeholder note. Then redeploy - Netlify detects the form on the
next build and submissions appear in the dashboard.

## Market reference (verified 25 Oct 2026)

| Operator | Price pp | Notes |
|---|---|---|
| Paradise FlyFishing (FR) | EUR 1,790 | 7n/6f, group of 4, all-inclusive |
| Outside Travels (SE) | EUR 1,895 / EUR 2,695 | flights included from EU |
| Flyfishing Di Fronzo (CH) | CHF 1,890 | 7n/6f, max 5 |
| Klejch (AT) | from EUR 650 | 4n/3f |
| LTG Pliva (rights holder) | EUR 30/night room, EUR 50/day licence | raw rate card |

## Safety note

The Pliva is a spring creek at **8-10 C all year**. No swimming outside the property.
Life vests mandatory for everyone on the water. Wetsuits for any immersion. Rafting is
summer only, age 10+, with adult supervision.

Catch and release. Travel insurance recommended.
