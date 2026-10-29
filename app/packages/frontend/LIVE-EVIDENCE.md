# Live discovery evidence and limits

This note distinguishes captured product observations from local reconstruction
choices. Captured JavaScript was inspected only as inert text. It is never
executed by this application.

## Captured source provenance

The first-party `/live` document is the only archived listing source used by
the reconstruction.

| Field                  | Value                                                              |
| ---------------------- | ------------------------------------------------------------------ |
| Original and final URL | `https://pump.fun/live`                                            |
| Capture timestamp      | `2026-10-28T10:48:45.546100+00:00`                                 |
| HTTP status            | `200`                                                              |
| Object                 | `evidence/web/objects/c45d40b52df03727`                            |
| Bytes                  | `785309`                                                           |
| SHA-256                | `aeff704c15d99482fe6e6347a92db0170dffeceb940a70e61dcc10002b006355` |
| Manifest               | `evidence/web/manifest.json`                                       |

The adapter requires the manifest URL, final URL, status, object path, byte
count, hash and exact capture timestamp to match before parsing. It reads the
single retained Flight push as inert JSON, then extracts all **42 unique card
objects** from the first `initialSectionData` array, in captured order. It does
not mix in hero records or the second (24-record) section. It undoes React Flight
string escaping (`$$` → `$`; any other
`$`-prefixed value fails closed) and validates their
identity, creator address, symbol, title, historical viewer count and captured
`isLive` flag. Playlist, thumbnail, nested coin data and other unexposed fields are deliberately
discarded before data crosses the Server/Client Component boundary. A duplicate
identity, missing/extra record, invalid required field, ambiguous push or section
marker fails the whole snapshot; records are not silently dropped. The decoder
accepts at most 1,000,000 source bytes and bounds the decoded section scan to
250,000 UTF-16 code units (the retained first array occupies 162,528).

The separate `/live/highest-market-cap` archive now maps the **second array's
24 cards** in its own captured order, using the same provenance and strict card
projection. Its label and route are bound to the actual registry index 1,
`LiveHomepage`'s `initialSectionData[s]` consumer and Show-all callback, the
section renderer, the enum, and the captured English translation resource.
See [the executable source proof](../../scripts/original-live-highest.mjs)
and [its contract](../../reconstruction/live-highest/contract.json).
All 24 identities also occur in Most viewers. They are a separately ordered
section, not 24 more unique streams. Hero data stays excluded. Neither array is
used to derive a ranking formula, and market-cap values and nested coin fields
are not exposed. No child-route HTML was captured; the child page's native
metadata disclosures and layout are explicitly local design. The original
Most viewers search, pagination, selection and two tabs remain unchanged.

The separate `https://livestream-api.pump.fun/health` observation is object
`evidence/web/objects/2f97956d4bb68473`, 191 bytes, SHA-256
`fcc3587e9bb0c61121f2189a097cb57e6af7e39cdfd0ce0c53a927f198aa002f`.
It proves only that a health request returned successfully at capture time. It
does not declare a listing, playback, authentication or realtime contract.

## Recovered factory map

Each range is a UTF-16 source range recorded in `recovered/modules.json`.
Hashes identify recovered factory text, not original source files.

| Module ID                      | Factory SHA-256                                                    | Source bundle                              |     UTF-16 range | Classification and finding                                                                                                                                                    |
| ------------------------------ | ------------------------------------------------------------------ | ------------------------------------------ | ---------------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `31113`                        | `aa72011769a3b4ed93846aa469860c5b661aafea0e98fbf5da8432305f2348c5` | `evidence/web/objects/8cb897425bbbb845.js` |      `118..3161` | OBSERVED: `LiveHomepage` maps section registry index `s` to `initialSectionData[s]`; capture Flight reference `$L116` identifies this factory.                                |
| `369731`                       | `fc87a2c85f17569e3f50a0b0bd960e814109550629c9baef4200792008e6d9b3` | `evidence/web/objects/44a65b4313e51497.js` |    `8997..20378` | OBSERVED: six-slot hero carousel, selection, pagination and viewer-count rendering.                                                                                           |
| `763145`                       | `d6c5fb78571198cbdce125397e28ac5a9cda6f2fa2b71dca1836de1e13821064` | `evidence/web/objects/0ba78d0f42544445.js` |    `2766..11008` | OBSERVED: stream card title, ticker and creator identity presentation. Its default coin-detail link remains outside this route's allowed scope.                               |
| `944001` / `310766`            | `1c56dd013720ae62a9c8ec316ebf1921d9fb13dc436bd75f7eefacdaad40aecb` | `evidence/web/objects/0ba78d0f42544445.js` |   `13588..21847` | OBSERVED: discovery section registry and `Most viewers` section assembly.                                                                                                     |
| `788501`                       | `db885fc927427d144544ada8524614dc33547634693bc8824951e2a65c25f6f0` | `evidence/web/objects/44a65b4313e51497.js` |   `25697..25933` | OBSERVED: section identifiers `most-viewers`, `highest-market-cap`, `trending-clips`, `popular-recordings`, `new-creators`, and `for-you`.                                    |
| `859960` / `606706` / `539335` | `d97c7c9447e248dcaeef4b872bb869c9056d2979cdf53731913116fb8544e429` | `evidence/web/objects/44a65b4313e51497.js` |   `25955..30183` | OBSERVED: card mapping for mint, name, creator, username, symbol, thumbnail, live flag, playlist and participant count; observed listing and playlist-map request call sites. |
| `133244`                       | `248fcf72a5bbbd3cb39cd391e161c90c6d496a0828ec3e07c15e7df093aecd97` | `evidence/web/objects/44a65b4313e51497.js` |   `24553..25689` | OBSERVED: initial hero data mapping and six loading slots.                                                                                                                    |
| `137793`                       | `208b37abad878fd4231b6202163e20c8e8465676becf56035e6375aa9211e002` | `evidence/web/objects/49fea3547104f38d.js` |     `3154..3380` | DECLARED: production LiveKit URL constant. It is not initialized or contacted locally.                                                                                        |
| `845785` / `606706` / `539335` | `3be974636ce9d23cc25b6ade092f28934d7defd6b6aff3c9d4e9e0073fa24bef` | `evidence/web/objects/b7df9c4704b957ab.js` |   `26584..29109` | OBSERVED: LiveKit/Pump provider, livestream/VOD/clip and player-context enums.                                                                                                |
| `828496`                       | `3de590f475c2c64a53ffb2d8a156561077bc83abaee5473de15b44c1f592c157` | `evidence/web/objects/2b47dd0b38a1608f.js` | `161584..163756` | DECLARED: public developer `GET /feed/video-feed` read operation and `clip`/`live` union. No captured binding proves that `/live` uses this operation.                        |

## OBSERVED

- The captured document title is `Live streams | Pump` and contains an
  accessible `Live streams` heading.
- Captured structure includes a hero carousel and a `Most viewers` section.
- Cards expose coin title/ticker, creator identity and a viewer indicator.
- All 42 first-section records are unique and were marked live at capture.
  The first five historical counts are 42, 34, 26, 24 and 20. Record 13
  (`CryptoCasinoWEB3`) reports 40 and record 42 (`Be a U$Dolly visionary!`)
  reports zero. This is not evidence of current broadcasts or presence.
- The captured response contains remote image and playlist URLs. Local code
  validates but never sends those fields to the browser.

## DECLARED

- Recovered client text names LiveKit/Pump providers and media/player types.
- The developer contract declares a read-only video-feed operation.
- These declarations are not evidence of authorized playback tokens, current
  broadcast availability or `/live` production endpoint equivalence.

## INFERRED

- Viewer numbers are interpreted only as values at capture time because the
  response and page were captured together.
- The captured array order of all 42 cards is retained for the default
  local order. The captured section is not strictly ordered by viewer count (a
  later card reports 40 viewers), so no ranking formula is inferred.

## LOCAL DESIGN

- Search covers captured title, ticker, creator address and mint locally.
- Sort controls offer captured order (default), historical viewer count and
  title. Viewers/title sorts use mint as a deterministic tie-breaker. Filtering
  occurs before pagination, without mutating the authenticated order.
- Local pages contain 12 records (12/12/12/6 for the whole archive). Query, sort,
  section, selected record and page are URL-backed. These page numbers are not
  upstream cursors or a reconstruction of production pagination.
- Search, clear, sort and section actions reset the page; page changes clear
  selection. A duplicate, noncanonical, empty or out-of-range page parameter
  produces an explicit unavailable view and a first-page recovery action. Empty
  searches have one empty page rather than a negative or phantom page.
- `Other sections` remains unavailable. The second retained array exists but is
  deliberately not mapped/validated/exposed by this adapter; no missing-data
  claim is made for that array.
- Selection opens a metadata panel whose only playable outcome is `Playback
unavailable`. Escape closes the detail and restores focus to its card, or
  the visible search control/section tab when that card is off-page. Escape
  events already prevented or owned by an open/modal dialog do not dismiss
  this nonmodal metadata panel.
- Remote thumbnails are replaced with text placeholders; coin-detail links are
  not exposed because `/coin/:mint` remains excluded.

## UNKNOWN

- Current listing endpoint authorization, request parameters, rate limits and
  response compatibility.
- Playback token acquisition and provider selection.
- Current livestream, viewer and presence state.
- Chat, broadcasting, recording, authenticated creator identity and wallet
  behavior.
- Original mobile detail-panel behavior and pixel-level visual parity.

## Verification

- `node --experimental-strip-types --test tests/live_snapshot.test.ts`: **15/15
  passed** for this expansion. Checks include all 42 records against an independent
  whole-Flight-row JSON oracle, three hash-bound source-factory ranges linking
  the first section to `most-viewers`, timestamp/hash/schema controls, duplicate
  and last-record corruptions, escaped strings, stable sorting and all four
  page partitions, invalid/duplicate page inputs, filtered and empty pages.
- Focused pure TypeScript check and Babel TSX/test syntax parsing: **passed**.
- `pnpm --filter @pump-reconstruction/frontend test:browser -- live.spec.ts`
  has expanded cases for all-page navigation, reload/history, query/sort reset,
  invalid pages, off-page/blank-selection Escape recovery and modal/prevented
  Escape ownership. These new browser
  cases and refreshed screenshots are **not yet run**: the full pinned frontend
  install is held by the environment's dependency minimum-release-age gate.
  No gate override, substitute dependency or proxy was used.
- Pinned Next 16.4.1 `use-search-params` and `use-router` guides were read from
  an integrity-verified official npm archive, extracting documentation only.
  No Next runtime or dependency was installed through that documentation path.
- The complete app build, test, typecheck, evidence and progress checks remain
  pending release gates for this patch. Historical local screenshots in the
  repository do not validate this expanded view. Local screenshots are structural
  qualification only;
  equivalent original interaction screenshots were not captured, so visual
  parity is not claimed.
