# Getting enquiries emailed to Milka

The enquiry form on the site does three things when a guest presses
**Send enquiry**:

1. **Posts to Netlify Forms** in the background, so the enquiry is stored and
   visible in the Netlify dashboard.
2. **Opens WhatsApp** with the enquiry already written out.
3. **Opens the guest's email app** with the enquiry already written out,
   addressed to `domacinstvosobic@gmail.com`.

Step 3 is what Milka asked for, and it works with no configuration at all —
the guest just presses send in their own mail app. It also means the guest's
details never pass through a third-party server.

There is one more thing worth switching on, because it means an enquiry
arrives in Milka's inbox **even if the guest closes the tab** before their
mail app finishes loading.

---

## Turn on the email notification (one click in the Netlify UI)

Netlify Forms can email the site owner every time a form is submitted. This
is set in the Netlify dashboard, not in the repository, so it has to be done
once by hand.

1. Open the Netlify dashboard and pick the site
   (`guesthousesobic.netlify.app`).
2. Go to **Forms**.
3. Find the form named **`enquiry`** and click its **Settings** (or the
   notification bell icon next to it).
4. Click **Add notification** → **Email notification**.
5. Fill in:
   - **Subject**: `New enquiry — {{name}}`
   - **To**: `domacinstvosobic@gmail.com`
6. Click **Add notification**.

That is it. From then on every submission lands in Milka's inbox as well as
in the Netlify dashboard.

### What the notification email looks like

Netlify sends the submitted fields. The form collects:

| Field | Name in the email |
|---|---|
| Your name | `name` |
| Email | `email` |
| Preferred dates | `dates` |
| How many people | `people` |
| Arriving via | `airport` |
| Anything we should know | `message` |

The subject line uses `{{name}}`, which Netlify replaces with the guest's
name, so the inbox is readable at a glance.

---

## One caveat about branch deploys

**Branch deploys of this site share the production Forms inbox.** That means
if you test the form on a branch-deploy URL, the test enquiry lands in
Milka's real inbox along with the real ones.

That is fine for a single deliberate test — and worth doing once, to prove the
whole chain works end to end. It is not fine for repeated testing.

If you need to test the form repeatedly, use a **separate Netlify site**:

- Netlify dashboard → **Add new site** → **Import an existing project**
- Point it at the same GitHub repository
- Pick a different branch, e.g. `feat/milka-updates-2026-11-02`
- Set its own form notification to a **test address**, not Milka's

That site gets its own URL and its own Forms inbox, so nothing can reach
production by accident.

---

## Checking what came in

- **Netlify dashboard → Forms** shows every submission, with the fields.
- **Milka's Gmail** receives the notification email from step 1 above.
- The guest also has the WhatsApp thread if they chose that route.

All three channels carry exactly the same information, because
`form.js` builds the message once and reuses it.

---

## If the notification does not arrive

1. Check the form is detected: **Forms** in the Netlify dashboard should list
   a form called `enquiry`. If it is missing, the `data-netlify="true"`
   attribute on the `<form>` tag was removed — check `index.html`.
2. Check the notification exists and the address is spelled right.
3. Check spam in Milka's inbox. Netlify notifications come from a
   `@notify.netlify.com` address, which some mail providers filter.
4. Remember that a **branch deploy** still posts to the production form
   definition — the dashboard may show the notification under the production
   site, not the branch-deploy URL.
