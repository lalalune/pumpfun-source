# Dated anonymous Mayhem screener read

The maintained Mayhem UI had a declared origin/path but no retained coin
response. This packet binds the **actual captured consumer and transport** to
one independently acquired anonymous response. It adds evidence, not a native
adapter, market dataset, website/developer-API equivalence or feature credit.

## Source and request closure

All original inputs remain unchanged from main
`094a06f18df738d41e77070c1a009e135671ac1a`. `SOURCE-TRACE.json` was generated
and saved **before** the request. It authenticates the complete selected
factory variants and exact UTF-16/UTF-8 source witnesses through the existing
shared source reader. That reader, original inventory and previous Mayhem
reconstruction are credited prerequisites.

| Actual used boundary | Captured evidence |
| --- | --- |
| Mounted consumer | `/mayhem` HTML `0c1c38e553b5ee46`, SHA-256 `13c794c2602f465fd458974dbfc093dc28c2273a0574a485171e9c08010417f5`, imports RSC reference `103:I[457065,…]` and renders `$L103` under the screener heading. The script URL selects `b5dd8c92e81b5961.js`. |
| Screener query | `457065.MayhemScreener` starts with `all`; its used query callback calls `C({state})`. No supplied `fetchOptions`, login predicate or `enabled` guard occurs on this query path. |
| Request builder | `C` calls `759257.j()("GET /coins/mayhem-mode",…)`; query keys are `mayhemState` and `limit`. `all` maps to `undefined`, so the key is omitted. The mounted default limit is 60. |
| Service and credentials | `759257.j` passes `503630.R()` = `https://frontend-api-v3.pump.fun` and `credentials:"same-origin"` into `30181.K`. This overrides the base client's `include` default. The origin is cross-origin from `https://pump.fun`, so that credential mode does not send website cookies. |
| Header construction | The used base hook `I` is empty; `M` adds fixed `x-pump-source: WEB` and `x-pump-platform: web`. The optional internal-key local in `759257.i` is uninitialized, so its false branch returns the options unchanged. Authenticated livestream constructors are separate exports and are not this path. |
| HTTP and result | `402030` forwards `898661.createContractClient`. It splits method/path, stringifies defined query values, strips the leading slash for the prefix URL and consumes `.json()`. `C` rejects non-OK/null results and passes success through `997887.l`, an identity function. |
| Declaration | `985722` declares optional integer `limit` (default/clamped to 60), `offset` (default 0, maximum 1000), `includeNsfw` (default false), and `mayhemState` (absent/empty = active+paused). The response declaration is an array of `540480.coinDto`. The used client path does **not** invoke that DTO parser. |

Each selected literal ID currently has one indexed physical origin. Full
factory hashes, alias ID arrays, object hashes, URLs and ranges are preserved;
no global numeric-ID uniqueness or opaque grouped-provider inference is added.
`38279`'s previously recorded URL constants alone were insufficient to settle
the credential override and actual request/normalizer chain.

## Exactly one acquisition

At `2026-10-29T19:57:48.514864+00:00` the preserved standard-library collector
made one GET to:

`https://frontend-api-v3.pump.fun/coins/mayhem-mode?limit=1`

The builder explicitly accepts a limit argument and its declaration admits
this integer. **Limit 1 deliberately bounds this acquisition; the mounted
initial query uses 60.** Offset, NSFW and state were omitted. The only explicit
request headers were Accept JSON and the two fixed source/platform headers.
No cookies, authorization, internal key, redirect, retry, browser session,
wallet, mutation or admin request was used. No second request was made.

This collector deliberately differs from browser transport: its timeout is
25 seconds, retries are disabled and redirects are refused. Captured `30181.K`
instead supplies a 30-second timeout and retry limit 1; this packet does not
claim the website never retries or follows redirects. Python sent no Origin
header or preflight. The browser's absolute cross-origin request with custom
WEB headers would require CORS/preflight admission, which was not tested.

The actual result was HTTP **200**, an untruncated **2,092-byte, one-row JSON
array**, SHA-256:

`d7dffc8ea16430b9b479b1d41b6e58889b7f8abee1d02cf5da787eb3330ae320`

`body.bin` preserves the exact application body. `RESPONSE.json` retains URL,
start/end time, parsed response headers, status, full body digest, field names,
the pre-request source-trace digest and the exact executed collector digest.
Two response `Set-Cookie` fields were omitted without retaining their values.
Headers are Python's parsed header representation, not raw network bytes;
the raw response body was not reformatted. Public coin/media URLs in that
body were never followed.

The sample exposes raw fields referenced by the screener, including
`mint`, `name`, `symbol`, `created_timestamp`, `usd_market_cap` and
`mayhem_state`; it also contains a nested `mayhem.state/mode` object. It does not contain
the independently fetched per-coin volume/chart inputs. One successful read
establishes neither current availability/ranking nor completeness, freshness,
browser CORS admission, DTO-wide compatibility or original rendering parity.
It supplies no user-specific state and makes no financial inference.

## Offline verification

Use the repository's pinned installed dependencies. From the repository root:

```sh
node app/research/mayhem-public-read-20261029/verify.mjs
node --test app/research/mayhem-public-read-20261029/verify.test.mjs
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

Expected: eight source factories/eight selected witnesses authenticate, the
actual source trace reproduces exactly, the frozen response/collector bindings
pass, and seven focused tests pass. The tests reject changed body bytes,
origin/redirect changes, authenticated/repeated request metadata, changed
pre-request trace or collector, truncated/cookie-bearing retained evidence,
and corruption of the actual captured transport object. Verification makes
**zero network requests** and never evaluates captured JavaScript. Use
`verify.mjs --app-root /path/to/app` for an alternate public-input location.

`capture.py` is the exact acquisition source, retained for inspection. It is
**not** a replay step: with the preserved `RESPONSE.json` present, its first
assertion refuses to repeat the request. Do not remove that receipt to refresh
this packet. A future separately authorized capture must be a distinct dated
observation.

The source and response were acquired independently on different dates. This
does not recover server source or establish that the current server implements
the October 28 contract. The maintained `/api/mayhem-screener` still fails
closed with 503 and accepts no unqualified native fallback. Original captures,
SDK, backend and every qualification status/count remain unchanged. Only the
Mayhem ledger's factual reviewed-state note and its generated report rows are
updated to acknowledge this dated research response without feature credit.
