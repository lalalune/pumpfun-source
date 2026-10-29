# Archived Live hero selection

The captured `/live` page contains six hero records and six rendered hero slots,
with only the first slot selected. The maintained page omits that workflow and
renders only the 42-record Most viewers archive. This unit adds a read-only
metadata presentation of the observed initial, looping Previous/Next and direct
selection behavior. These six identities already occur in Most viewers; they
are not additional unique streams.

The executable source proof, `scripts/original-live-hero.mjs`, authenticates five
selected physical factory variants and the full captured HTML without executing
captured JavaScript:

- `31113` forwards `initialHeroData` to `133244`'s actual exported loader.
- `133244` supplies initial data to `859960.L` and consumes its returned data
  through `369731.HeroCarousel`; its hero slot constant is six.
- `859960.L` retains the actual `initialData` in its consumed query options.
- `369731` starts at zero, passes the item count and looping flag, consumes
  functional modulo Next/Previous transitions, and supplies direct selection
  to its slots and `218921.PaginationDots`.
- `218921` invokes the passed index callback and marks the current dot. The
  retained HTML has six `live-hero-slot` elements with one selected, then five
  unselected, consistent with that initial state.

`contract.json` records each chunk/range/factory hash, the used AST witnesses,
Flight consumer and six ordered mint identities. Numeric IDs alone are not
treated as unique corpus identities.

The hero DTOs do not contain `id` or `linkUrl`. The safe local metadata identity
is derived from their actual mint, matching the original keyed renderer's
identity. The adapter authenticates the capture and provenance, requires six
unique records, resolves only literal escaped Flight strings, validates their
required metadata, and checks every projected value against its known identity
in the 42-record archive. It rejects shape/count/identity/state/consistency
failures rather than supplying replacement highlights. Media URLs, nested coin
data and financial fields are discarded before the Server/Client boundary.

The local component uses native buttons and a metadata panel. It has no global
key listener, URL/storage state or remote read. It preserves the observed
selection arithmetic, native keyboard activation and selected-state semantics.
The presentation and explanatory labels are local design. Original autoplay,
player/mute controls, current-live badges, financial values, analytics and
excluded coin-detail actions remain unavailable. Clicking a selected local
choice stays in this read-only workflow; it does not reproduce the original
excluded coin action. No original visual/layout parity or feature credit is
claimed.

This unit branches independently from current main. It does not compose #1570's
Highest market cap route or #1534/#1449/#1328 selection work. `LiveDiscovery`
remains unchanged. Both archive additions modify the `test:live` CI line;
integration must retain both the Highest test path and the Hero test step.
The Hero tests use the workspace's existing pinned `tsx` runner for normal
extensionless TypeScript imports; no dependency, lockfile or TypeScript-option
change is needed.

Run from `app`:

```sh
node scripts/original-live-hero.mjs
corepack pnpm test:live
corepack pnpm --filter @pump-reconstruction/frontend typecheck
corepack pnpm --filter @pump-reconstruction/frontend exec playwright test tests/live-hero.spec.ts tests/live.spec.ts
```

The browser suite covers actual absence on the base, six-record mounting,
wraparound/direct/native keyboard selection, captured-order metadata, local
network/media boundaries, responsiveness, and cooperation with existing search,
selection, Escape and reload. Qualification will retain the exact source,
commands, results and any unproven limits separately.
