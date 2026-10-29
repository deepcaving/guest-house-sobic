# Testing a branch before it goes live

You do not need a second Netlify site to test a branch. One switch gives
every branch its own live URL, on the site you already have.

## Turn it on (once)

**Netlify → Project configuration → Developer settings → Continuous deployment
→ Branches and deploy contexts → Configure → Branch deploys → All**

`main` is excluded automatically, so production is never affected. You can
also add individual branches, or a prefix wildcard like `feat/*`.

The label has moved around over the years - older documentation says *Site
configuration → Build & deploy → Continuous deployment*. Same setting.

**It builds on the next commit pushed to the branch.** Netlify does not go
back and build branches that already existed when you saved the setting. If
you enabled this after pushing a branch, push something to that branch to
wake it up.

## The URL

```
https://<branch-slug>--guesthousesobic.netlify.app
```

The branch slug has `/` replaced with `-`, so `feat/italian-language` becomes:

```
https://feat-italian-language--guesthousesobic.netlify.app
```

The deploys list in the Netlify UI always shows the exact URL - trust that
over any pattern you work out by hand.

The URL is permanent: it survives every new push to that branch and lasts as
long as the branch exists. A Deploy Preview URL (`deploy-preview-<n>--...`)
is tied to a pull request number and dies with the pull request, which is
why branch deploys are the better tool for testing something you want to keep
checking.

## What to check on a branch deploy

- [ ] The page loads, images and the video play
- [ ] The language switcher works - and on this branch, that is **four**
      languages: English, Deutsch, Bosanski, Italiano
- [ ] `?lang=it` opens the Italian page directly, whatever your browser is
      set to
- [ ] The enquiry form submits (it opens WhatsApp with the details filled in)
- [ ] It looks right on your phone - that is the device your guests use
- [ ] The prices are the ones you expect

Leave notes directly on the page with the Netlify Drawer. It is on by default
for Deploy Previews; for branch deploys you have to enable it yourself:
**Project configuration → Developer settings → Continuous deployment →
Collaboration tools → Configure**.

## The catch worth knowing

A branch deploy of the *same* site is handled by that site, so an enquiry
submitted from a branch deploy can land in the **production** Forms inbox.
Handy, because it proves the form works end to end. Not handy if you would
rather test without putting a fake enquiry in front of the host.

If you need that isolation, make a second site instead: **Add new site →
Import an existing project** → the same repository, publish directory `.`,
no build command. The clone gets its own Forms dashboard, its own domain and
its own environment variables. Production cannot be touched by it.

## Merging

When the branch reads right, merge it into `main` and push. Netlify deploys
`main` to the production URL and the branch deploy disappears with the
branch.

Do **not** switch the production branch in the Netlify UI to publish a
branch. That makes Netlify treat the branch as production, demotes `main` to
a preview, and leaves stale deploys behind when you switch back.
