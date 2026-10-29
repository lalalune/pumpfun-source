# Offline profile reconstruction evidence

This note records the static evidence and local-data contract used to implement
`/profile/[id]`. Captured factories are inert research inputs that require the
original Turbopack runtime and import graph; they are never executed here.
Factory ranges are UTF-16 code-unit offsets over decoded JavaScript, as defined
by `recovered/modules.json`.

## Capture checkpoint

- Web manifest checkpoint: `2026-10-28T10:48:45.546100+00:00`
- Captured user-contract object:
  `evidence/web/objects/2b47dd0b38a1608f.js`
- Captured object SHA-256:
  `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d`
- Local users seed SHA-256:
  `56259663a146236df2f0e6e1d931df7cc2dda4d39ed7a090c18505434155b20d`
- Local posts seed SHA-256:
  `f4d12a7812b07be6dcef4b966430a086cba9e867ff89de669a95a74bdd73d705`
- Local-data classification: `synthetic-seed-play`

The web capture scope did not include a concrete `/profile/:id` page response.
Consequently this work maps the captured contract, route construction, identity
presentation primitives, and profile translation namespace, but does not claim
an equivalent original profile screenshot or full original page composition.

## Observed

| Concern                         |  Factory | Factory SHA-256                                                    | Captured source and SHA-256                                                                                    |     UTF-16 range | Observation                                                                                                                                                                                                                           |
| ------------------------------- | -------: | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ---------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Profile route construction      | `146695` | `bb995bc856796eb404e21763f5a72275af2b0efa06b46f0d12507e1c6a3d90a1` | `evidence/web/objects/fd402d4185b44ce9.js`, `1dc5d2351887b14932acbddf37ea653566df106b41c56ddc19ae70158e43f806` |   `29806..30355` | Constructs `/profile/${encodeURIComponent(identity)}` from an address or user id. It also contains username-related routing branches that are not adopted locally because the checked-in store resolves only user id and address.     |
| User row schema                 | `896727` | `c6d26c3befe1f767147fcfcf6c16016bbaa9870548c96bd0ad5fa391ace658b6` | `evidence/web/objects/2b47dd0b38a1608f.js`, `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d` | `490565..493848` | Declares address, optional user id, nullable username/avatar/bio, person/group kind, member count, group badges, followers/following, Pump-user and ban flags, and canonical wallets.                                                 |
| Identity presentation primitive | `107240` | `4b94aa99e04cf92a4e2a79379d9c2336e2ea9f81d3ba90ff5433452a04e30a4d` | `evidence/web/objects/eb0b23ee6feb7543.js`, `8ff9a060d8b1c540a04bb505094eb61ce0c2b2c5d83579af3e3976bf49a16d54` |   `11466..21254` | Composes address/user id/username, avatar fallback, verified lookup, profile link, subline, and follow-slot boundaries. The local implementation retains identity/fallback structure but does not perform verified or follow lookups. |
| Profile route namespace         | `532843` | `07e45ce65eee481055c678c52eac4c0ccb904c6cfd463d1a79c72c0c7367a7b0` | `evidence/web/objects/c96cd69e95f3f01a.js`, `8899083b932ccf201b417e6382eba3a88412f599356c00a4f0c67883e0dd7ecc` |     `1060..8099` | Associates the profile route with profile, feed, callout, transaction, wallet, auth, trade, and report namespaces. This establishes a broad dependency surface, not local qualification of those features.                            |

The static operation inventory additionally records `GET /users/{id}` from
`evidence/web/objects/27a1ee00eb5909ec.js` (SHA-256
`4f15372b7572090fd27f1c612bafee0a0a3672127d5187b66e05b6ddd0d21452`)
at UTF-16 range `29840..29857`, and `GET /users/{id}/overview` from the
captured contract object at `342803..342829`. The checked-in OpenAPI declares both under
`profiles.read`, with bearer authentication for the developer API. This offline
page reads files directly on the server and does not call or qualify either API.

Home post-card evidence is recorded separately in
`HOME-FEED-EVIDENCE.md`. This page reuses the same local `FeedList` and
`FeedItem` presentation and visibility rules.

## Declared local input

The backend explicitly classifies `users-seed.json` and `posts-seed.json` as
hand-authored synthetic data. They are not captured Pump users or activity. The
profile loader authenticates the exact bytes before parsing. It rejects duplicate
user or post identities, unknown author references, unsupported account kinds,
invalid counters, malformed timestamps, and inconsistent canonical wallets.

External avatar, header, group-badge, and post-media URLs are shape-validated
but never passed into browser markup. A deterministic initial and local media
placeholder preserve the offline/network boundary.

## Local design

- Exact `userId` and wallet-address matches resolve; username lookup is not
  implemented because the local store does not define it as an identity key.
- Unknown and malformed identifiers render the application's 404 boundary.
- Person/group classification, member count, bio, and follower/following counts
  are shown only when supported by the authenticated seed.
- Banned examples are explicitly marked, and follow remains disabled for every
  profile because authentication and social writes are unavailable.
- Authored posts include only validated visible roots. Replies, quotes, reposts,
  hidden rows, and deleted rows are not promoted into the Posts view.
- All visible data carries synthetic-data disclosure. No ownership, live
  activity, real relationship, verified status, or native API compatibility is
  inferred.

## Qualification

- Pure adapter tests cover exact hashes, id/address resolution, duplicates,
  malformed JSON, invalid kinds/counts/timestamps, author consistency, field
  fallbacks, post visibility, stable ordering, banned/group classification, and
  identifier boundaries.
- Browser tests cover deep links, 404s, history, person/group/empty/banned
  states, disabled writes, accessibility, external-request rejection, and five
  responsive viewports from 320 to 1440 CSS pixels.
- Local screenshots and limitations are recorded in
  `visual/profile-20261028/README.md`.

## Unknown and unsupported

- Live users, current follower/following counts, follow relationships, mutuals,
  authenticated viewer state, and account ownership.
- Profile writes, follows, messages, wallet connection, verified lookups, live
  post queries, pagination, and realtime updates.
- Full original profile layout, localized copy, transition behavior, and pixel
  parity in an equivalent captured state.
- Username route resolution, which appears in some captured route helpers but is
  not established by the local store contract used here.

## Walletless local profile identities

The local adapter previously rejected every empty `address`, even when a usable
`userId` was present. This is narrower than the retained identity contract:

- Factory `146695` (`bb995bc856796eb404e21763f5a72275af2b0efa06b46f0d12507e1c6a3d90a1`,
  range and source recorded above) selects `address?.trim() || userId?.trim()`
  for its object-form profile-route helper. An empty wallet need not prevent a
  profile route when an independent user id exists.
- Factory `896727` declares `address` as a string, not a non-empty string, and
  declares `userId` separately. Person/group classification is independent.
- Factory `972407`, SHA-256
  `a77710a323d3fa83fc470b2e3837d2da42a97a6726c92ce96dd73e236c0a6365`,
  in the same `2b47dd0b38a1608f.js` object at UTF-16 range `206003..219056`,
  explicitly describes compact graph-row addresses as canonical SVM, otherwise
  canonical EVM, otherwise empty for a walletless account. These three factory
  ranges were independently hash-checked against their retained origins; none
  was evaluated.

The local profile and feed adapters now retain an empty wallet **without treating
it as an identity key**. A walletless profile needs an independently usable user
id under the existing local route-identifier policy; malformed or absent ids
still fail closed. This is local admission policy, not an added upstream schema
refinement. Canonical wallet consistency checks use SVM first, then EVM when SVM
is absent/empty. They do not invent a wallet from a user id.

Feed adaptation retains the resolved author's user id. Profile post ownership
uses that stable id when available, falling back to a non-empty wallet only for
wallet-only profiles. Merely allowing empty wallets while grouping by address
would incorrectly combine posts from unrelated walletless accounts. Empty
addresses are neither indexed nor resolved, and cross-alias/duplicate identity
checks remain in place.

The header omits the clipboard control when no wallet is recorded. Header and
post-card markup explicitly disclose that absence instead of rendering an empty
wallet; unresolved feed authors remain a separate state. `Unnamed local account`
is a local fallback label, not a recovered translation. This does not enable
follow/message/auth actions, ownership or verified status, external media, or
network requests.

The checked-in seed bytes and their pinned hashes are unchanged. They still
contain the same five synthetic profiles; this change qualifies the adapter and
presentation for additional contract-permitted local inputs, not a new live
profile source. It neither installs the separate follow-list query client nor
claims a recovered original profile modal.

Validation commands:

```sh
# From app/:
node --import ./packages/backend/node_modules/tsx/dist/loader.mjs --test tests/profile_data.test.ts tests/home_feed.test.ts
# From app/packages/frontend/ (so tsx reads the frontend JSX configuration):
node --import ../backend/node_modules/tsx/dist/loader.mjs --test tests/profile-walletless-render.node.ts
```

The explicit `.node.ts` filename keeps this Node suite outside Playwright's default test-discovery pattern.
The 22 pure profile/feed tests and two actual React server-rendering tests pass.
Before the change, four added pure test groups failed and both rendering tests
showed empty wallet presentation. The SSR command's working directory is
intentional; an earlier root-directory run lacked JSX configuration and is not
counted as a behavioral baseline. Cases include two distinct walletless users,
post isolation, id/address aliases, duplicate and unusable ids, SVM/EVM precedence,
unchanged inputs, preserved wallet copy controls, and unresolved-author separation.
Server-rendered markup checks are **not** browser, hydration, clipboard, mobile
layout or original-screenshot qualification. No feature milestone is advanced.

On the application source snapshot at
`faea9aea0dcc3056bd7c346700c96ce86b737549` plus this change, full `pnpm build`
(SDK, backend and Next 16.4.1, static page generation 16/16) and all-package
`pnpm typecheck` pass. The pinned offline/frozen dependency install reused cached
packages with scripts disabled and the existing minimum-release-age policy.
Formatting passes. Browser tests were not run for this follow-up.

The complete aggregate test command remains unrun, including its browser
posttest; captured runtime execution was not authorized or attempted. The local
`verify-evidence.py` run fails on absent manifest capture inputs, and the
`progress.py --check` run first fails on missing
`packages/frontend/visual/portfolio-live-20261028/live-verification.json` in the
partial checkout. These are missing-input failures, not passing qualification
gates. No screenshots, captures, receipts, seed changes or ledger increases are
included in this follow-up.

## Local follow graph lists (2026-10-29)

The profile now also reads the existing backend `following-seed.json` on the
server. Its exact SHA-256 is
`37a0e7710055e94dd6035e3e6c418eac16797095471601ed059440ee97530dae`.
This adds an actual UI consumer for the previously backend-only synthetic graph,
not a website API transport or an authenticated social state.

Source and contract boundaries:

- [Original exported follow-list client](../../contracts/ORIGINAL-FOLLOW-LIST.md)
  binds captured **500056.Q** to the followers/following list reads and default
  `followers` sort. The retained source does not establish a rendered original
  profile list or modal. It is not executed or modified by this feature.
- Captured **972407**, documented in the walletless identity section above,
  and `contracts/developer.openapi.json` declare compact graph rows and their
  identity fields. Their developer-host bearer credential is not used here.
- [Existing local following model](../backend/FOLLOWING.md) supplies the
  hand-authored directed edges and deterministic default ordering: descending
  stored follower count, username, then stable user id/address. That tie-break
  and the small seed's contents are local design, not observed production ranking.
- The existing profile route helper evidence (**146695**) supports encoded
  identity routes. The lists prefer an exact routable local user id, falling back
  to a routable wallet when the optional user id is absent or unusable.

The two inline lists, all-at-once presentation, labels, unavailable state and
responsive layout are local design. They show all validated edges of this small
seed. There is no search, pagination, recent-sort control, modal, mutation,
viewer, mutual relationship, refresh loop, API key, production origin or HTTP
request added. Recorded banned profiles remain visibly marked as in the local
store; this does not establish production social visibility policy. Remote
avatars and other media never enter the graph view model.

The existing aggregate profile counters remain unchanged and are explicitly
separate from the local graph's edge counts. Every edge must resolve to the
validated profile dataset; malformed edges, duplicate canonical pairs and unknown
identities fail the graph as a whole. Missing files or a hash mismatch produce
an unavailable graph, while the existing identity and post view remain available.
A successfully validated empty side displays an explicit empty state.

`tests/profile_follow_graph.test.ts` covers both directions, exact bytes, count
separation, stable ordering, walletless/wallet-only identity, duplicate aliases,
unknown members, malformed edges, missing reads and changed bytes. The focused
browser regression first failed because no Local follow graph existed, then
passed list ordering, links/history, wallet aliases, empty and banned examples,
network boundaries and four viewport widths. All six existing profile browser
cases also pass. Local screenshots at 320 and 1280 pixels are in
`visual/profile-follow-graph-20261029/`; no equivalent original profile screenshot
was captured, so original visual parity and full profile/graph compatibility
remain unqualified. No feature completion milestone is newly credited.


## Profile route admission correction (2026-10-29)

The maintained identifier guard previously admitted lone UTF-16 surrogates and
exact `.` / `..` identifiers. A `FeedItem` could therefore throw `URIError`
during `encodeURIComponent`, or link to a different route after URL dot-segment
normalization. The existing wallet-to-user-id fallback was also bypassed when
an unsafe wallet was incorrectly considered usable.

The shared guard now rejects those inputs without rewriting them. Valid Unicode,
including paired astral characters and distinct composed/decomposed text, remains
unchanged. Literal percent strings such as `%2e`, `%2E%2E` and `%2F` are still
identifiers: they are encoded once into `%252e`, `%252E%252E` and `%252F`, not
decoded into path separators or dot segments. The existing 128 UTF-16-unit
bound and whitespace/control/separator rules remain in force. Missing authors
stay plain text; usable feed wallets still take precedence over user ids.

The graph consumer had a second path to the same defect: a profile could resolve
through a valid wallet while its optional, unrouteable user id was selected for
the rendered link. Graph identity now prefers a usable user id, then a usable
wallet, consistently for projection, edge deduplication, subject matching and
tie-breaking. It does not mutate stored identifiers or profile records. An edge
that cannot resolve still fails the entire graph; no substitute account is
created. Aggregate counts, seeded edges and all default seed bytes are unchanged.

This is local route-safety policy, not an inferred production identifier grammar.
The original route-construction evidence remains factory **146695** above;
its retained object and UTF-16 range hashes were rechecked without executing the
capture. No original code, profile lookup transport, clipboard behavior,
authentication, wallet operation or compatibility milestone changes.

### Focused verification

Against main `60bdd8a7a522921058d18563bb9335d2a06aec75`:

- The same explicit maintained tests reproduced **41 pass / 5 fail** before the
  two implementation changes, then **46/46 pass**: profile data and graph,
  local search, Home feed and actual React/Next `FeedItem` server rendering.
- A separate private actual React/NextLink graph server-render check used
  validated synthetic users and the maintained graph projection. The baseline
  had **3 pass / 4 fail** (two wrong dot links and two `URIError` cases); the
  candidate passed **7/7**. Only CSS classes were stubbed. This supplemental
  harness is not part of the published test suite.
- Complete SDK/backend/Next production build and all three workspace typechecks
  passed; focused strict test-source checking also passed. No install or
  dependency change was required.
- App evidence verification retained the **698-object** manifest and unchanged
  published SDK source. The independently checked same-main repository-root
  static gates passed **9 capture-integrity and 6 synthetic comparator checks**.

Reproduce the published focused cases from `packages/frontend` with:

```sh
node --import ../../node_modules/.pnpm/tsx@4.20.6/node_modules/tsx/dist/loader.mjs --test \
  tests/profile-walletless-render.node.ts \
  ../../tests/profile_data.test.ts ../../tests/profile_follow_graph.test.ts \
  ../../tests/home_feed.test.ts ../../tests/local_user_search.test.ts
```

These are local synthetic-input and server-render checks, not a running Next
router, browser/history/navigation test, real-user lookup or visual parity.
The default hash-bound seed contains none of these malformed identifiers.
Browser and aggregate suites were not invoked, and historical browser results
elsewhere in this document are not new qualification for this correction.
