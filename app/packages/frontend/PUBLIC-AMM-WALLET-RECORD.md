# Public PumpSwap wallet activity record

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
