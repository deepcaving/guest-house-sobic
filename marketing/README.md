# Pliva River Lodge — marketing & outreach kit

Everything you need to start filling the 2026/27 season, copy-and-paste ready.
It is all derived from the six planning documents (master plan, competitor
pricing analysis, live competitor prices, content pack, outreach contact list)
and **corrected against the live website**, which is the source of truth.

## What was corrected, and why

The planning PDFs and the website disagreed in three places. The website won,
because the website is what customers actually read and book from.

| Fact | Planning docs said | The site says | Why the site wins |
|---|---|---|---|
| Distance below the spring | 3 km | **2 km** | Corrected deliberately on 25 Oct 2026 against the property itself. The docs are older. |
| Water temperature | 9 °C, or "8–10 °C" | **8 °C** | Same correction. 8 °C is a flat constant — the water comes out of the ground at that temperature year-round. |
| The Pliva Week price | €1,490 | **€1,390** | The site's whole rate card was set deliberately in one commit ("2026 pricing with Nov-Dec season rates"): €1,390 / €1,090 / €830, with its own group-of-two, solo and Nov–Dec tiers. The €1,490 in the docs is the master plan's *recommendation*, never implemented. Advertising €1,490 while the bookable site says €1,390 reads as bait-and-switch. |

If you ever want to move the headline price to €1,490, change it in
[`site-config.json`](../site-config.json) and in `site-facts.md`, then re-run
`python3 marketing/render.py` and rebuild — but do not do it on a live site without a
deliberate decision, because the group-of-two, solo and Nov–Dec tiers all
hang off the headline number.

## Before you use anything: one placeholder to fix

Every file in this folder uses these tokens:

| Token | What it is | Current value |
|---|---|---|
| `{{SITE_URL}}` | the live site | `https://guesthousesobic.netlify.app/` |
| `{{EMAIL}}` | the booking inbox | **not set yet — see below** |
| `{{PHONE}}` | phone / WhatsApp, display form | `+387 65 622 760` |
| `{{PHONE_E164}}` | phone, machine form | `+38765622760` |
| `{{WHATSAPP}}` | WhatsApp link | `https://wa.me/38765622760` |
| `{{HOST}}` | host name | `Milka Smjestaj Šobić` |
| `{{TRIPADVISOR}}` | TripAdvisor listing | see `tripadvisor-setup.md` |

`{{EMAIL}}` is the one still open. The old address
(`bookings@plivariverlodge.com`) is on a domain that does not resolve, so mail
to it goes nowhere — it is currently the one genuinely broken contact route on
the site.

### Master copy and generated copy

The files in this folder are the **master copy** and they keep the `{{TOKENS}}`.
`render.py` reads `site-config.json` and writes a ready-to-paste version of
each one into **`marketing/out/`**.

**Always copy and paste from `marketing/out/`, not from `marketing/`.** The
master keeps the tokens on purpose: when the email address changes you edit
one file and re-render, and every copy file updates at once. If the rendered
files were the source of truth, the tokens would be gone and there would be
nothing left to re-render.

`marketing/out/` is committed to the repository so the files are there to use
without running anything. It is generated output, though — if you change a
fact in `marketing/`, re-run the renderer rather than editing `out/` by hand,
or the next render will overwrite your change.

**When you have the real inbox**, do this and every file updates at once:

```bash
# 1. put the new address in the single source of truth
vim site-config.json          # "email": "your-new-inbox@example.com"
                             # "email_live": true

# 2. also update the website itself (2 places) and the contact section
grep -rn 'bookings@plivariverlodge.com' . --exclude-dir=.git

# 3. regenerate the ready-to-paste copy
python3 marketing/render.py

# 4. rebuild the Carrd single-file version
python3 build_standalone.py
```

Until step 1 is done, every file in `marketing/out/` carries a banner at the
top saying the email is not live yet. The renderer adds that banner for you
based on `"email_live"` in `site-config.json` — you never have to remember to
remove it.

## The files

Each row is the master; the paste-ready version is in `marketing/out/` with
the same name.

| File | What it's for |
|---|---|
| [`site-facts.md`](site-facts.md) | **Read this first.** The single source of truth — every fact, price, distance and number. Every other file is derived from it. |
| [`google-business-profile.md`](google-business-profile.md) | Full GBP setup: description, short description, Q&A, photo order, first 5 posts. |
| [`instagram.md`](instagram.md) | Bio, the 3×3 launch grid, hashtag stacks, Reels and Stories plan. |
| [`facebook.md`](facebook.md) | Page setup, cover photo, About text, pin post, and the Facebook groups playbook. |
| [`cold-dm-templates.md`](cold-dm-templates.md) | 12 ready-to-send messages in English, German and Italian — to guides, to hosted-trip organisers, to magazine editors, to guests. |
| [`blog-november.md`](blog-november.md) | The 600-word first blog post, ready to publish, plus the next four post ideas. |
| [`email-templates.md`](email-templates.md) | Review request, booking confirmation, pre-arrival pack, enquiry reply. |
| [`whatsapp-auto-reply.md`](whatsapp-auto-reply.md) | Away message, 6 quick replies, the enquiry triage flow, the catalogue. |
| [`host-english-card.md`](host-english-card.md) | The laminated A4 card for the kitchen cabinet — the 30 words she needs. |
| [`30-day-calendar.md`](30-day-calendar.md) | Week-by-week launch calendar, week 1 to week 30. |
| [`tripadvisor-setup.md`](tripadvisor-setup.md) | Claiming and rebuilding the TripAdvisor listing. |

## The order to do it in

1. **Set the real email** (above). Everything else is blocked on this.
2. **Claim Google Business Profile.** It is the only free channel that puts
   you in Google Maps for "fly fishing Šipovo" and it is what most people
   actually land on.
3. **Post the 5 GBP posts** — one a day for the first week.
4. **Start the outreach.** 2–3 DMs a week, not 30 in one afternoon. The
   fishing communities ban obvious marketing on sight; the approach in
   `cold-dm-templates.md` is deliberately a person asking a question.
5. **Publish the blog post** and cross-post the link to Reddit r/flyfishing
   and flyfishing.co.uk.
6. **Everything else** — Instagram, Facebook, X, the listing directories —
   follows once the GBP and the DMs are working.

## One thing to keep in mind

The website is live, the enquiry form works, and the phone number is real.
**Right now the only route that reliably reaches a human is WhatsApp and the
phone.** Every copy file in this folder ends with the WhatsApp number for
that reason, and the website's form leads with WhatsApp too. Keep it that way
until the email inbox is live.
