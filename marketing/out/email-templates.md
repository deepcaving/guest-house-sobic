# Email templates

> **⚠️ BEFORE YOU USE THIS FILE**
> The booking email in it is **not live yet** — `bookings@plivariverlodge.com` sits on a domain that
> does not resolve, so anything sent there is lost.
>
> Set the real inbox in `site-config.json`, set `"email_live": true`, then run
> `python3 marketing/render.py` to regenerate this file. Until then, send
> everything through WhatsApp: **+387 65 622 760**.


Four emails. Send them from a personal address she actually reads — a Gmail
is better than a business address nobody opens. When the real inbox is set,
put it in `site-config.json` and re-run `./render.sh` so every template picks
it up.

---

## 1. The review request — the highest-ROI email in this folder

Send to 3–5 past Booking.com guests. One review moves a Maps listing more
than a month of posting.

**Subject:** Quick favour? A review for Pliva River Lodge

> Hi [name],
>
> You stayed with us at Šobić on the Pliva back in [month/year], and I hope you
> had a great trip.
>
> We're rebuilding our online presence after stepping back from Booking.com,
> and your review would genuinely help a small family-run lodge get discovered
> by other anglers and travellers who'd love the Pliva as much as you did.
>
> It takes two minutes:
> https://www.tripadvisor.com/Hotel_Review-g2319287-d7383736-Reviews-Guest_House_Sobic-Sipovo_Republika_Srpska.html
>
> A few words about the river, the food or the terrace would mean most. We
> read every one.
>
> Thank you so much.
>
> Milka Smjestaj Šobić
> Pliva River Lodge · +387 65 622 760 · https://guesthousesobic.netlify.app

**The one rule:** ask once. If they don't reply, don't ask again. One polite
follow-up at most, a week later.

---

## 2. The booking confirmation

Send the moment the deposit clears, not when the guest asks.

**Subject:** Confirmed — Pliva River Lodge, [dates]

> Hi [name],
>
> You're confirmed at Pliva River Lodge from [arrival] to [departure].
>
> **What you've booked**
> • [package name] — [nights] nights, [n] days guided fishing
> • [n] guests, [room type]
> • Full board: breakfast, packed lunch on the water, dinner
> • Guided fishing with [guide name], English-speaking
> • The Pliva fishing licence (€50/day non-resident rate) — arranged by us
> • Round-trip airport transfer from [airport]
> • €[total] in total, €[deposit] paid, balance of €[balance] on arrival
>
> **Getting here**
> From [airport] it is about [drive time] door to door. Tell us your flight
> number and we will be waiting with a name board. If you would rather drive
> yourself, there is free secure parking on site.
>
> **On arrival**
> Check-in from 14:00. Dinner is at 19:00, and if you have a preference for
> fish or meat, tell us a day ahead and the cook will plan around it.
>
> **Please read — the river**
> The Pliva is a spring creek at 8 °C year-round. It is too cold to swim in
> and it can cause cold-water shock in under a minute. Life vests are worn at
> all times on the guided days. A wetsuit and buoyancy aid are essential for
> wading — we provide both. Catch and release is mandatory on the Pliva.
> Light rafting is summer only, for guests aged 10 and over, with adult
> supervision.
>
> **The licence**
> The fishing licence is €50 per day for non-resident guests and is already
> included in your package. There is nothing extra to pay for it.
>
> If anything changes, just reply to this email or message us on WhatsApp
> +387 65 622 760 — we answer every message within 24 hours.
>
> We look forward to having you on the water.
>
> Milka Smjestaj Šobić
> Pliva River Lodge, Šipovo, Republika Srpska, Bosnia & Herzegovina
> +387 65 622 760 · https://guesthousesobic.netlify.app

---

## 3. The pre-arrival pack

Send 7 days before arrival. It cuts the number of WhatsApp questions to
almost nothing and it is the email people remember.

**Subject:** Before you arrive — Pliva River Lodge, [dates]

> Hi [name],
>
> You are with us in a few days, so here is everything you need in one place.
>
> **Getting to us**
> [Airport] → Šipovo, about [X] hours door to door. We will be at arrivals
> with a name board. Your driver's number is [name, number].
>
> **What to bring**
> • Waders and a wetsuit if you have them — we can lend rods, reels and
>   waders at €22/day, and we advise telling us your sizes a few days ahead
>   so we can have them ready
> • Wellingtons or boots you don't mind wetting
> • A warm mid-layer for the morning sessions and a rain shell
> • Flies if you have favourites; the local flies are free
>
> **Money**
> Cards are accepted, but bring some cash for the market in Šipovo and for
> drinks. Prices are in EUR.
>
> **The fishing**
> The licence is €50/day for non-resident guests and is already in your
> package. Catch and release only. The upper Pliva is open year-round; the
> Jajce beat runs March to September. Expect the Pliva to be knee- to
> thigh-deep over gravel, with a steady current — long leaders, small flies,
> and a steady retrieve. Our guide will talk you through it on day one.
>
> **Meals**
> Breakfast is served on the terrace when the weather allows. Dinner is at
> 19:00 and it is generous. Tell us about allergies, and tell us a day ahead
> if you would like us to cook a Pliva trout.
>
> **One request**
> If you are coming in autumn, bring a warm jacket. The mornings on the
> Pliva are 4–8 °C, and the fire is lit in the dining hall by seven.
>
> See you on Sunday.
>
> Milka Smjestaj Šobić · +387 65 622 760 · https://guesthousesobic.netlify.app

---

## 4. The enquiry reply — for when someone writes from the website

**Subject:** Re: your enquiry — Pliva River Lodge

> Hi [name],
>
> Thanks for your message, and welcome.
>
> To check dates and give you the right price, could you tell me:
>
> 1. Your preferred dates (and how flexible you are)
> 2. How many people, and how many of them are fishing
> 3. Which airport you are flying into — Sarajevo, Banja Luka or Split?
> 4. Whether you would like a guided week or just the lodge and the table
>
> While you think about it, here is the short version:
>
> • **The Pliva Week** — 7 nights, 6 days guided fishing, full board, the
>   licence, and the airport transfer from Sarajevo. €1,390 per person for a
>   group of four, €1,590 for two, €2,090 for one. In November and December
>   it is €1,190 per person.
> • **The Companion Week** — the same seven nights for whoever is not fishing.
>   €1,090 per person, €950 in November and December.
> • **Short Break** — 4 nights, 3 fishing days, half board. €830 per person.
> • **Hosted weeks** with a named guide, from €1,790 per person.
>
> Room-only is €85 a night for a double with breakfast.
>
> The full details are here: https://guesthousesobic.netlify.app
>
> If it is easier, message me on WhatsApp +387 65 622 760 — that is usually the
> fastest way to get an answer and I do not mind photos of the house in
> between.
>
> Milka Smjestaj Šobić

---

## Which emails to send, and when

| When | Email | To |
|---|---|---|
| Day 1–5 of launch | review request | 3–5 past guests, one at a time, not as a BCC |
| On booking | booking confirmation | every guest, same day the deposit clears |
| 7 days before arrival | pre-arrival pack | every guest |
| On enquiry | enquiry reply | within 24 hours, always |
| After the stay | review request | 3–5 days after departure, while they're still talking about it |
