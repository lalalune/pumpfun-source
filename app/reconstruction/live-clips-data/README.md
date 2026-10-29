# Main `/live` clips/VOD read coordinator

This editable module recovers the **complete private `944001.E` hook**, its mode table and seven used helpers. The existing main-page section registry calls it for Trending clips and Popular recordings; OPEN [1897](https://github.com/lalalune/pumpfun-source/pull/1897) deliberately left this exact hook as a required capability. This closes that bounded source boundary, without mounting an application or making a provider request.

The generator parses authenticated captures and emits complete selected AST declarations. It never evaluates the original factory. `PROVENANCE.json` retains the observed `https://pump.fun/live` HTML/Flight context, actual main-page imports, both registry callers and the result consumer, full item-schema declarations, all actual source-import bindings and both physical `944410` client variants. The selected initial-script presence establishes static context, not an active registration winner. Shared schema-runtime forwarders remain explicit ambiguity; no Zod runtime is selected or reconstructed.

## API and exact external boundaries

`createLiveClipsData(ports).useClipSection({sectionId, limit?})` is a React hook. All these capabilities are **required**, rather than synthesized defaults:

- `memoCache(size)` is the actual compiler cache (`445242.c` through `532815`); `useQuery(options)` supplies the actual query result/runtime (`690877`).
- `useLivestreamApiClient()` supplies the actual client (`944410`) with `get(path,{searchParams}).json()` and `post(path,{json}).json()`. Transport, destination, authentication, cancellation, HTTP/error/retry and query-cache lifecycle remain external. A JSON POST here is a read-shaped source operation; this work performs no original request and makes no anonymous-access claim.
- `arraySchemaModule.z.array(itemSchema).parse(body)`, `analyticsItemSchema` and `clipItemSchema` supply the actual array parser and exact source `N`/`w` schemas. Their complete declarations and dependencies `p/v/g/b` are witnessed, not copied as an approximation. Tests use explicitly synthetic acceptance ports and do not establish original validation.
- `useCoinMetadata({mints})` (`458013.f`) and `useSolPrice({})` (`363250.f`) supply hook results. The module does not fetch, validate or price coins independently.
- `analyticsLogger.error` (`254667.y`) and `clipLogger.error` (`54567.logger`) retain the separate parse-error boundaries.
- `Date` is an explicit Date-compatible constructor with `prototype.getTime`, `parse` and `now`. Each actual source sample stays at its original operation; there is no single frozen-time substitution.
- `sectionKinds` is actual `788501.f`; `listingConstants` supplies the existing [1821](https://github.com/lalalune/pumpfun-source/pull/1821) API `LIVE_LISTING_LIMIT` (24) and `LIVE_CARD_COUNTS` (`large:4`). No existing listing/request/pager helper is copied or counted as new work.

The caller supplies original-compatible capabilities when integrating. This packet does not silently import another open PR. Related [1570](https://github.com/lalalune/pumpfun-source/pull/1570)/[1617](https://github.com/lalalune/pumpfun-source/pull/1617) archive/category/hero attribution and 1821/1897 operational boundaries retain their original attribution; their implementation is not claimed again.

## Preserved behavior

The original **10/13/21/12 memo slots** remain intact. Trending clips uses weekly/HIGHLIGHT and Popular recordings monthly/COMPLETE. The request limit is `floor(3*nominalLimit)`; analytics oversample defaults to five and both query option objects carry one-hour stale time. Only `sectionId` and `limit` are consumed from the outer argument: extra properties do not invent a new query override surface.

The analytics key excludes time. Each query invocation samples `new Date().getTime()` and sends ordered type/limit/timestamp/oversample/clipType parameters to `vod-analytics/top`. Its parsed served IDs retain duplicates/order and truthy room/vod filtering. The clips query exists even for an empty ID list, which returns `[]` before POST or parse. Nonempty IDs feed `clips/by-ids` unchanged. HTTP/JSON errors are outside the parser catches; parse errors log the exact distinct message and rethrow the same object (including the source behavior if the logger itself throws).

Clips sort by their own view counts, then a repeated room needs a distance of four **retained entries including the previous same-room entry** (three intervening entries with `large:4`). Rejected clips do not advance that count. Retained original indices restore order, metadata is requested once per unique room in that order, and the last metadata row for a mint wins. There is **no final nominal-limit slice**, analytics-view-count override or added hidden/deletion filter.

Cards retain every original field and truthiness/nullish fallback, raw coin identity, playlist precedence and coin-detail link string without navigating it. A parsed epoch-zero date is falsy and therefore calls `Date.now()`; invalid dates do too, with a separate sample per affected row and rerender. Loading joins analytics, clips and coin metadata only. SOL-price loading/errors and query errors do not add output fields. The actual fetch-next function is a no-op and both paging flags are false. No financial correctness, current availability or native/backend compatibility follows from this source recovery.

## Replay

From a repository checkout with pinned app dependencies available:

```sh
cd app
node reconstruction/live-clips-data/recover.mjs --check
node --test tests/live_clips_data.test.mjs
node reconstruction/live-clips-data/browser.mjs --output /absolute/new/output-directory
```

`--write` regenerates `client.mjs` and `PROVENANCE.json`. The verifier also exports `recover(appRoot)`/`verify(appRoot)` for explicit public-input exports; the portable Node case copies only declared repository inputs to an isolated directory. No private workfiles or open-PR source implementation is needed.

The finite browser host uses real React/compiler/DOM and authored synthetic query/client/schema/metadata/price/clock capabilities. Only its own HTML/bundle GETs are allowed. It exercises recomputation, identity, query-function delegation, projection, clock samples and cleanup; it does not execute captured JS, real provider HTTP, original parser/runtime, playback/media, account actions, application UI or visual parity. Its source, fixture, runtime bundle inputs and failures/results must be hash-bound before interpreting a run. Qualification results are appended only after the frozen method executes.

## Frozen finite result

At local measured `ffe68589ed24ea14b89cddeb2fc7da9ebccf3d35`, the source verifier and **11 focused Node/real-React SSR cases passed**. One standalone real-React/compiler/DOM story passed **eight observations**, with zero page errors or non-host requests and explicit browser/host cleanup. Its synthetic schema/client/query/coin/price/clock boundaries retain the exclusions above. Required **53 Git inputs / 9 captures / 10 tooling** and app698/npm/SDK checks passed. Progress's initial sparse-evidence failure, exact three-file Git hydration and successful check are retained separately; nine progress tests passed.

The [qualification packet](qualification/README.md) seals the exact seven measured source/method files, all 12 emitted-bundle inputs, trace, results, required-check logs and failures. A draft wrong consumer-alias diagnostic was corrected before freeze; the unavailable draft snapshot is not invented. The exact emitted bundle digest was reproduced for byte retention after the run, with no second browser execution. Later README/qualification additions do not change or relabel the measured runtime inputs. These finite results establish neither mounted main-page behavior nor service/parser/media/native/financial compatibility.
