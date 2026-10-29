# GO bounty discovery evidence and limits

This note separates retained product observations from local reconstruction
choices. Recovered JavaScript was inspected only as inert text and is never
imported or executed by the application.

## First-visit Escape ownership

At `f93b52ba3f6a18cf334522c35a9726974a9c6eb1`, a fresh browser context
opening an archived `?task=` selection loses that task when Escape dismisses
the actual Welcome dialog. The dialog prevents the key's default action while
recording its existing acceptance preference, but GO's window listener also
closes the underlying nonmodal detail on the same event.

GO now leaves an already-prevented Escape to its owner. The first key dismisses
Welcome without changing the task URL; the second closes the detail and
restores the archived card's focus. Desktop/mobile browser regressions use the
real first-visit dialog and archived read-only data, with an external/mutation
request guard. This local event-ownership correction changes no acceptance,
authentication, wallet or payout behavior and adds no compatibility credit.

## Captured page provenance

The only listing data used by the reconstruction is the authenticated
first-party `/go` document retained by the capture manifest.

| Field                  | Value                                                              |
| ---------------------- | ------------------------------------------------------------------ |
| Original and final URL | `https://pump.fun/go`                                              |
| Capture timestamp      | `2026-10-28T10:48:45.546100+00:00`                                 |
| HTTP status            | `200`                                                              |
| Object                 | `evidence/web/objects/e66810e11f481135`                            |
| Bytes                  | `1030034`                                                          |
| SHA-256                | `8037ac8c628063897531326090f1a4d3cbf8ed0051f4f6e9f88c821f4fee9ece` |
| Manifest               | `evidence/web/manifest.json`                                       |

The server adapter requires the manifest URL, final URL, status, path, byte
count, hash and capture timestamp to match. It then parses the embedded RSC
payload as JSON, requires the exact 50-item feed shape, and extracts the 25
direct bounty records. Submission cards are not silently converted into
bounties. Invalid provenance, bytes, UTF-8, RSC shape, records, amounts or
identities fail closed.

## Recovered factory map

Ranges are UTF-16 source ranges from `recovered/modules.json`. Hashes identify
the recovered factory text, not the formatted recovered file.

| Module   | Factory SHA-256                                                    | Source bundle                              |   UTF-16 range | Classification and finding                                                                                                             |
| -------- | ------------------------------------------------------------------ | ------------------------------------------ | -------------: | -------------------------------------------------------------------------------------------------------------------------------------- |
| `409355` | `8fbae86760a69cc53406c63c27077f9f9bc6e0f4bc501825a8b3b36944028ad4` | `evidence/web/objects/229e1f0da48ca815.js` |   `3715..4569` | OBSERVED: GO root, open, bounty, mine, draft, submission and action-item route constructors. Only `/go` is in the current route scope. |
| `372812` | `c297053e2dc481df50299dccc203e1404c6dabc727b832abce61bef41cc23e17` | `evidence/web/objects/41216a65a59eaf37.js` |   `5280..6116` | OBSERVED: URL query state is retained when navigating the discovery view.                                                              |
| `170258` | `c2cc17f47ff237994e797d3c09ce05b91dcc0d691b003d5682f68469ef526806` | `evidence/web/objects/41216a65a59eaf37.js` | `23120..25473` | OBSERVED: infinite read client for `GET bounties/v2/tasks`, default `limit=24`, cursor and filter construction, and response parsing.  |
| `986071` | `b8b5c48b0e1698ae04d6450303338955af3430a18b062cf2f732dd51bf0e6e12` | `evidence/web/objects/9eb69cb75e0ff997.js` | `14062..15171` | OBSERVED: filter/query key declarations.                                                                                               |
| `146742` | `f5ca91407565583f41e699557587527a7c9b2376bf2c6db07cb3f264ad663720` | `evidence/web/objects/4f3529a0b713e63d.js` |    `138..2982` | OBSERVED: tasks request, public query parameters and status constants.                                                                 |
| `711902` | `4e833805fd88afe2c9931aa89916705ddc7e88e990d472c420c88c11707579c1` | `evidence/web/objects/4f3529a0b713e63d.js` |  `3088..23233` | OBSERVED: strict task, reward, response and status schemas.                                                                            |
| `768385` | `b9050b8d3404f58e6a2a8b462e269f4f00ea54a445964b7601cac35f8a77d2f4` | `evidence/web/objects/62e6fa852396858e.js` |   `138..53893` | OBSERVED: search/filter layout, list states, stats read, account tabs and mutation-dependent action boundaries.                        |
| `158791` | `62f3eef4211b4a2dd1d7c12624c61a0112aa6b402d12265d31e87135da4698ce` | `evidence/web/objects/41216a65a59eaf37.js` | `13215..16749` | OBSERVED: sort mappings for created time, reward value, expiry and submissions; public phase labels and OPEN derivation.               |
| `503630` | `df5a12d4b76158889dd38a02d0d9afc0d0405065772b589c9cadf9806422d0e7` | `evidence/web/objects/1e479323ffe53c14.js` |    `654..1035` | DECLARED: `https://livestream-api.pump.fun` client origin. It is never contacted locally.                                              |

## OBSERVED

- The captured feed contains 25 direct bounty items and 25 submission items.
- Direct bounty fields include task and creator identity, title, Markdown body,
  timestamps, status, reward legs and submission counts.
- Captured task statuses name `DRAFT`, `PUBLISHED`, `PENDING_RESOLUTION`,
  `IN_DISPUTE_PERIOD` and `CLOSED`. The retained public direct records use
  pending, dispute and closed states; draft/published visibility is therefore
  not exposed as a local public filter.
- `GET bounties/v2/tasks` accepts `q`, creator/coin/reward filters, status,
  phase, sort, order, limit and cursor. This reconstruction deliberately uses
  only search, public phase, sort, direction and cursor.
- The captured client also names `GET bounties/v2/stats`. No authenticated
  archived stats response is retained, so no counts, TVL or payout KPIs are
  shown.

## DECLARED

- The recovered client declares a livestream-service origin and task/stats
  paths. Those strings are website-service leads, not proof that an anonymous
  caller can use a current production API.
- Schema factories declare reward quantities as atomic strings with an
  optional captured decimals snapshot.

## INFERRED

- `PENDING_RESOLUTION` with an expiry after capture is presented as “Open at
  capture”, matching the recovered phase derivation. This is historical state,
  never a statement that the bounty remains open now.
- The embedded direct records are the capture's initial discovery dataset, not
  a complete historical corpus.

## LOCAL DESIGN

- Search, public phase, sort direction, sort key, cursor and selected task are
  allowlisted and URL-backed. Refresh and browser Back/Forward preserve state.
- A same-origin read-only route queries only the already authenticated local
  snapshot. It has no proxy URL and cannot fall back to production.
- Requests are abortable and sequence-gated so stale responses cannot replace
  newer filter results. Pagination is manual, bounded and uses the captured
  default page size of 24.
- Atomic reward strings use `BigInt`. A quantity is displayed only when the
  retained amount and decimals snapshot both validate; otherwise the amount is
  explicitly unavailable. USD-at-capture is available only for sorting and is
  not presented as a current price.
- Markdown bodies are rendered as escaped plain text. Attachments and external
  images are not loaded.
- Detail selection provides historical metadata and an explicit unavailable
  state for funding, submissions, moderation and payouts. Escape closes the
  detail and restores focus to its card.

## UNKNOWN

- Current task contents, authentication, rate limits and website-service
  response compatibility.
- Production ranking formula, cursor lifetime and stats semantics.
- Authenticated identity, submissions, drafts, action items, funding,
  resolution, dispute, payout and moderation behavior.
- Original mobile interaction details and pixel-level visual parity.

## Qualification

- `pnpm test:go` verifies exact capture integrity, mutation rejection, schema
  failure, bounded queries, deterministic sorting/pagination and precise atomic
  amount formatting.
- `packages/frontend/tests/go.spec.ts` drives the running application through
  search, URL history, filters, sorting, pagination, network/invalid response
  failures, retry, detail focus, responsive layouts and no-external/no-mutation
  boundaries.
- Screenshots in `packages/frontend/visual/go-20261028/` are local acceptance
  evidence. Equivalent original interaction screenshots are unavailable, so
  pixel-perfect parity is not claimed.
