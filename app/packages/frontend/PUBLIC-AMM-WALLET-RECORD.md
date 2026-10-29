# Public PumpSwap wallet activity record

## Automatic HEAD correction supplement

Next's installed `autoImplementMethods` maps an unimplemented HEAD to the exported
GET function with the request method still HEAD. The original AMM handler rejected
that request with 405 before query validation or its reader. This is corrected in
source `36597272c45f2291bac434acb08913976705c0a2`: GET and HEAD use the same query,
wallet, reader, signal and error paths, while HEAD responses have no body. GET
retains the existing `Response.json` serialization. The SDK, transport, route,
client and UI are unchanged; open #1403's Pump handler remains separate.

The same final regression file (SHA-256
`54be748827dd75d7a5e2df5b0388c33375f3016adf27c792bb32dcfe615e2e5e`)
fails all four groups on the original handler and passes after correction. The
combined run passes **22/22**: four HEAD groups, ten existing AMM groups and eight
existing Pump groups. It exercises installed Next automatic dispatch, the actual
90-byte SDK decoder/read port, query and provider/cluster error mappings,
bodyless/no-store responses, unchanged GET data, and real loopback HTTP HEAD/GET.
Frontend TypeScript, application evidence and progress checks also pass.

Additive proof is in `visual/amm-wallet-record-head-20261029/`. The original
`visual/amm-wallet-record-20261029/` packet remains unchanged. The historical Next
browser and root production results below retain their original source bindings;
they do not qualify the new HEAD branch. A subsequent actual Next dev-server
check on exact `9351ea368d79033728abb11a4a2e2c5a04835e9b` passes three
unconfigured product-route requests: GET 503 with complete configuration-error
JSON, automatic HEAD 503 with no body, and malformed-query HEAD 400 with no body.
All responses are JSON/no-store. `actual-next/` retains the response records,
server log, checker-only header-case failure, corrected checker and owned cleanup.
No fixture or RPC endpoint was configured. This qualifies compiled unconfigured
route admission only; no new browser run, production build, configured RPC or
mainnet success is claimed for the HEAD correction.

```sh
node --test tests/amm_wallet_record_head.test.mjs tests/amm_wallet_record.test.mjs tests/wallet_program_record.test.mjs
```

### Public replay and retained checker layout

Public fork commit `c1e4680b4bcc4f0b196690e9657ba1223280322f` contains the
historically measured product inputs. A clean Git-blob export of its 8,117 app
files reproduced the seven-source contract check and all 22 Node checks after
building the SDK from that public source, using the existing pinned dependencies.
No private fixture or prebuilt private SDK output was copied. From `app/`, after
the documented frozen pnpm 10.24 dependency setup:

```sh
pnpm --filter @pump-fun/pump-sdk build
node scripts/amm-wallet-record/contract.mjs --check
node --test tests/amm_wallet_record_head.test.mjs tests/amm_wallet_record.test.mjs tests/wallet_program_record.test.mjs
python3 -B -m unittest discover -s tests -p test_amm_wallet_record_http_check.py -v
```

The retained `actual-next/check.py` is the exact historical checker, executed
originally under `work/amm-head-observation/`. Its relative-root calculation is
not valid at its published packet location: the clean public run fails before
HTTP with `FileNotFoundError`. It and the old real Next receipts are preserved
unchanged. For a new observation use `scripts/amm-wallet-record/check-http.py`,
which accepts explicit checkout/origin/output arguments, binds the three on-disk
product sources to that checkout's HEAD, refuses to overwrite an earlier receipt,
and never follows redirects or ambient proxies. With an independently started
local server using this source and an explicitly empty `SOLANA_RPC_URL`:

```sh
python3 -B scripts/amm-wallet-record/check-http.py \
  --repository "$(git rev-parse --show-toplevel)" \
  --origin http://127.0.0.1:3027 --output /tmp/new-amm-http-receipt.json
```

Choose an unused output path and the server's actual loopback port. The checker
does not start/configure a server or prove which implementation serves it. Its
five isolated checks use a real local HTTP protocol fixture: explicit paths,
metadata failure, dirty-source refusal, existing-receipt preservation and
nonlocal-origin refusal. A separate run over the same public source export
observes GET 503 / HEAD 503 / bad-query HEAD 400 from that synthetic fixture.
These new observations qualify checker portability only; they are not a new
Next, browser, SDK-runtime or configured-production success. Raw negative,
protocol-only receipt, source bindings and clean-public Node logs are additive
under `visual/amm-wallet-record-head-20261029/public-replay/`.

The Portfolio public-balance result now offers a separate **Read public PumpSwap
record** action beside the existing Pump record. Neither account is requested
by loading balances; each read and refresh is explicit. Program/PDA, observed
slot, mainnet/confirmed status, UTC time and sanitized RPC host stay separate.
Their counters are not summed, priced or interpreted as current rewards.

This is an independent public-chain integration supported by the published SDK,
not recovered original frontend/private API parity. The SDK's actual
`fetchUserVolumeAccumulatorTotalStats` reads both program records. This view
adds the missing independent AMM read without running that aggregation or its
missing-record zero substitution. Missing remains absent. Flags/counters are
stored raw fields, not eligibility, ownership, a claim amount or verified payout
history. No signing or authenticated session exists in this read path.

## Different program and layout

The published AMM wallet account has a 90-byte known prefix, unlike Pump's
106-byte prefix. AMM does not declare `stableCashbackEarned` or
`totalStableCashbackClaimed`. They remain absent, never invented as zeros.
The SDK uses the same seed/discriminator name in separate program namespaces;
the server checks the actual AMM owner, discriminator, canonical booleans,
embedded wallet, bounded canonical base64 and account metadata before projecting
known fields. Short inputs are rejected; unknown trailing bytes are retained
only as a byte count and are not interpreted.

Seven SDK source files match immutable npm archive
`c8ff4e850651c81e9f488bfc6dffb4513a041bb4bca0819879dc19d9a72a4641`.
Seven AST witnesses bind the AMM PDA, program, non-nullable decoder, actual read,
two-program consumer, separate Global-based incentive calculation and stale
handwritten type. Run `node scripts/amm-wallet-record/contract.mjs --check`.
Source proof is in `research/amm-wallet-record-20261029/SOURCE.json`; it reuses
#684's UTF-16/strict-UTF-8 source primitive and never executes captured frontend
JavaScript. SDK sources and metadata are unchanged. The already-adapted
workspace package export map is explicitly distinguished from npm's export map.

The published handwritten swap return type omits three fields present in its
own IDL/runtime. This integration validates the actual decoder's extra boolean
and unsigned counters locally instead of asserting a richer SDK type or
changing SDK files. Another measured control shows the Pump codec accepts the
shorter buffer and produces zero trailing stable counters; that does not make
those fields present in an AMM account. Application program/width admission and
program-specific projection are necessary.

## Runtime and public-read boundaries

The cold maintained CommonJS swap entry failed before any account read with a
buffer-layout class-identity error. Its ESM import entry succeeds. The reader
therefore lazily calls native `import()` on an explicit read. A fresh-process
regression invokes the actual reader without an SDK preload and verifies that
it selects no CommonJS swap entry. No unused import-order preload, dependency
replacement, SDK mutation or silent decoder fallback is used. The CommonJS
negative is preserved; no claim about that entry working is made.

Public result → explicit AMM button → credentials-omitting/no-store GET
`/api/portfolio/amm-record?address=…` → fixed one-argument Node route/handler →
existing pinned HTTPS RPC factory → mainnet genesis check → fixed SDK-derived
PDA `getAccountInfo(base64,confirmed)` → ownership/layout/user guards → actual
AMM decoder → exact known-field strings. Browser input cannot choose an RPC
method, endpoint or program. The local route is not an upstream/private or native
`/v1` API claim. Existing Pump server/client/route and the shared RPC factory are
unchanged. The Portfolio navigation form remains untouched.

Wallet navigation, balance refresh and unmount discard both observations and
invalidate/abort pending work. The AMM client has its own finite 20-second
deadline; refresh clears its previous result before loading. It does not cache,
persist or substitute a historical/zero record. Existing server DNS/HTTPS,
redirect, body-size and per-call policies are reused. No claim is made to cancel
the OS DNS lookup or impose an aggregate server deadline across phases.

## Finite qualification

```sh
node scripts/amm-wallet-record/contract.mjs --check
node --test tests/amm_wallet_record.test.mjs tests/wallet_program_record.test.mjs
pnpm --filter @pump-reconstruction/frontend exec tsc --noEmit --incremental false
```

Ten new source/SDK/handler/client checks pass, including the actual cold reader,
90-byte decoding, u64/i64 bounds, program/user/metadata rejection, missing and
extended accounts, no fabricated stable fields, strict query/method handling,
error privacy and real loopback HTTP. Eight existing Pump checks also pass in
a separately retained cohort. Frontend TypeScript passes. Earlier cold-CJS and
stale-type failures are retained, as is a mistaken test assumption that the Pump
codec would throw on a short buffer; the measured control replaced that
assumption without weakening application admission.

Actual Next/Chromium on `3a5c17ad91c7407fb21cf3b6d489724fde9f24a7`:
**22 passed, 1 explicit old-guard skip, 23 discovered**. All 15 new AMM cases and
seven existing Pump cases pass. The first case uses a temporary loopback,
development and explicit-flag-gated route that imports the actual shared
handler/reader and decodes a controlled 90-byte account under Next. This is not
proof transferred from Node. The separate unchanged product route’s unconfigured
503/no-store/UI/error-body admission also passes. Configured production-route
success and live mainnet/HTTPS transport remain untested.

The original default Playwright stop killed the helper before cleanup. That
negative is preserved; only the exact hash-matched owned fixture was manually
removed. A test-only graceful shutdown correction with a direct Next launcher
and lifecycle sidecar then passed **two repeated critical cases**, with explicit
installation/removal hashes and automatic cleanup. Those are repeats, not two
additional unique cases. The temporary route is absent from the product commit
and working tree. Runtime 526550 is unchanged across these runs. After retaining
its manifests, the inactive owned Next cache was removed; clean TypeScript
passes without a stale fixture validator.

`visual/amm-wallet-record-20261029/` contains a sealed manifest, raw positive and
negative logs, source/dependency bindings, reviewed 320/1440px screenshots and
fixture lifecycle. Source/API/SDK checks, 698-object evidence, progress (9 tests) and
required root 9-capture/10-tooling gates pass. Independent normal SDK/backend/Next production build, recursive TypeScript,
698-object evidence/npm/SDK and progress all pass on sealed runtime/test head
`116d0f64a4d04d04bcc8631ae94da7a5b2f5d1cc`. The raw four logs, checks and
tested-to-public mapping are retained under this packet’s `root-production/`.
This supplement changes only documentation/receipts. Configured production-route
success and mainnet HTTPS requests remain untested. Synthetic public accounts are finite test inputs, not current balances
or eligibility. Feature-progress/native-operation counts remain unchanged.

```sh
SOLANA_RPC_URL='' AMM_RECORD_FIXTURE_TEST=1 AMM_RECORD_TEST_NO_RPC=1 WALLET_RECORD_TEST_NO_RPC='' \
  pnpm --filter @pump-reconstruction/frontend exec playwright test \
  --config playwright.amm-wallet-record.config.ts --max-failures=1
```
