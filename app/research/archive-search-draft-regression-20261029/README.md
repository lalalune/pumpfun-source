# Archived Live and GO search draft race

This is a local browser-state correction for the included `/live` and `/go`
entries in `contracts/routes.json`. Their existing `behaviorQualified` and
`visualQualified` flags remain unchanged. No service operation, captured
artifact, SDK source, or completion percentage is changed.

The pages continue to use their authenticated archived inputs:
`evidence/web/objects/c45d40b52df03727` for Live and
`evidence/web/objects/e66810e11f481135` for GO. Their existing evidence loaders
and hash checks are unchanged. These checks do not qualify a live service.

## Reproduction and correction

Start with `?q=previous`, hold the Clear/Reset navigation's RSC request, then
enter `new draft` before releasing it. Previously, the empty URL query committed
by that older navigation replaced the newer draft with an empty string.

The pending-Clear marker preserves that newer draft when the empty query
commits. Explicit submission and browser history navigation reset the marker,
so URL-backed search and Back/Forward still synchronize normally. This follows
the existing local Explore repair in
[PR #951](https://github.com/lalalune/pumpfun-source/pull/951) and shared search
repair in [PR #918](https://github.com/lalalune/pumpfun-source/pull/918).

## Finite local coverage

Both new Playwright regressions fail on unmodified base
`05cbb8b58795cfb9f8344901a8695a25f0cadda5`: expected `new draft`, received an
empty string. With the fix, all 27 existing and new Live/GO browser cases pass:

```sh
pnpm --filter @pump-reconstruction/frontend exec playwright test live.spec.ts go.spec.ts
```

The added cases hold the RSC request, preserve and submit the next draft, and
exercise Back/Forward. Separate local before/after recordings cover both pages
at 1440px and 390px widths. They demonstrate this interaction only; they are not
comparisons against a running original website or a visual-parity claim.

[Comparison PNGs and WebM recordings](https://github.com/oxks12/pumpfun-source/releases/tag/evidence-archive-search-drafts-20261029)
use descriptive `before/after-{live,go}-{1440,390}` asset names. They contain
local test interactions over the public archived datasets, with no wallet
connection, production mutation, or private account data.