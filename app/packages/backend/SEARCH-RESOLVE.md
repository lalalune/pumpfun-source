# Local account resolution

`GET /v1/search/resolve` has a native account-only implementation when `buildApp`
receives an explicit `userStore`. With no injected store, fixture replay and the
existing 501 fallback are unchanged. The store is a local synthetic model, not an
upstream account registry.

## Contract and implemented branch

The declared service is `https://api.pump.fun/v1`, OpenAPI `0.294.0`, operation
`get_search_resolve` with `profiles.read`. `contracts/developer-bindings.json`
binds it to captured factory `402734-7679a980be13` (`recovered/modules.json`).
The factory is inert evidence, never executed by this implementation.

The query accepts one to five identifiers of at most 128 UTF-16 code units.
Comma-separated, repeated and mixed `identifiers` forms flatten in request order;
values are not trimmed, normalized or deduplicated. A successful result has exactly
`identifier`, `kind`, `chain`, `coin`, `user`, `resolvedVia` and `definitive`.

This local implementation supports exact stored UUID **user IDs**, including
person and group accounts. The UUID admission pattern is an explicit local restriction
(reusing the posts route's UUID shapes, including nil/max), not a recovered production
identifier validator. Matching is exact; no case normalization is inferred. An address
alias is not treated as a user ID. A known
person returns `kind: "user"`, `resolvedVia: "cc_user"`; a group returns `"squad"`
and `"group"`. Both have `chain: null`, `coin: null`, `definitive: true` and the
existing developer-host User row. The last-seen field is omitted and no presence
lookup or extra profile enrichment runs. Each requested identifier gets one
result, including duplicates, with an empty `degraded` list because every required
lookup in this supported branch answered from the injected store.

`definitive` applies only to that supplied local model. Successful responses have
`X-Reconstruction-Data-Source: synthetic-seed-play`,
`X-Reconstruction-Compatibility: unqualified` and `Cache-Control: no-store`.

## Explicit local boundaries

- Missing UUIDs, non-UUID local IDs (including the default seed's `user-001`), wallet
  addresses, coins and other shapes return 501 for the whole request. There is no
  partial success, guessed `unknown` or `external_wallet` verdict, or invented
  upstream degradation reason.
- No coin registry, chain classifier, fallback provider, live lookup, registration
  absence inference or production compatibility qualification is implemented.
- Missing `identifiers`, more than five values or values over 128 code units return
  local `400 INVALID_QUERY`. Unknown query parameters return local 501. An empty
  string is within the declared string bound but outside the supported UUID branch,
  so it also returns 501. These error envelopes are local policy, not captured
  production responses.
- The existing native `apiKeyGate` runs before parsing. This does not implement
  production key verification, scope authorization or a website session.

`test/search-resolve.test.ts` verifies the exact DTO against OpenAPI, both account
kinds, raw profile fields and no presence data, ordered mixed/repeated parsing,
bounds, unsupported mixed batches, independent stores, the key gate, and default
fixture preservation. No feature-wide completion credit is added.
