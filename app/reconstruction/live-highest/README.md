# Archived Highest market cap section

The maintained `/live` adapter exposes only the first `initialSectionData`
array (42 Most viewers records). The retained HTML also supplies a second array
of 24 records. This unit makes that separately observed section readable at
the original Show-all destination, `/live/highest-market-cap`, with a sibling
link from the existing archive.

`scripts/original-live-highest.mjs` authenticates the physical capture and
factory variant, parses its AST, and binds:

- `31113`'s actual `944001` registry and `310766` renderer imports, registry
  map, `initialSectionData[s]`, forwarded props and Show-all callback;
- `944001`'s `Z` export and registry index 1, the Highest market cap title key,
  and the actual section renderer's Show-all href;
- `788501`'s `highest-market-cap` literal, captured resource
  `7c.resources.web.live.section_highest_market_cap`, Flight `$L116`, and all
  24 ordered second-array mint identities.

The selected chunk/range/hash bindings are in `contract.json`. Numeric IDs
alone do not identify a unique corpus variant. Captured JavaScript is never
executed.

All 24 records also occur in the existing 42-record archive. The second
section's membership/order is retained independently; no 66-stream count is
claimed. Its values do not establish a market-cap ranking formula or current
status. The new page exposes only validated title, symbol, identity, creator
address and viewer count at capture, with native HTML metadata disclosures.
No original child-route HTML was captured, so these disclosures and the page
layout are local design. The existing two tabs, selection readiness,
navigation, first array and hero boundary are unchanged.

The server checks the manifest provenance and entire capture hash before
selecting a bounded section. Missing/extra/duplicate records, malformed
required metadata and unresolved Flight references fail the selected snapshot.
Media URLs, nested coin data and financial fields are discarded. No remote
reads, excluded coin links, player, wallet operation, feature credit, native
API compatibility or original visual parity is claimed.

Run from `app`:

```sh
node scripts/original-live-highest.mjs
node --experimental-strip-types --test tests/live_highest.test.ts tests/live_snapshot.test.ts
corepack pnpm --filter @pump-reconstruction/frontend typecheck
corepack pnpm --filter @pump-reconstruction/frontend exec playwright test tests/live-highest.spec.ts tests/live.spec.ts
```

Qualification records will distinguish the exact tested source, baseline
failure, finite browser controls and excluded/unrun checks.
