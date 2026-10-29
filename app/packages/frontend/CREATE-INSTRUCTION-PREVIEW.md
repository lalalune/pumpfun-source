# Offline create instruction inspector

## Purpose and source boundary

PRD §§3 and 10 include `/create`, SDK integration and offline composition. The
existing metadata draft stops before SDK integration. This advanced panel is an
explicit local inspection tool, not a recovered original UI or a launch flow.
It consumes the unmodified published `@pump-fun/pump-sdk` 4.3.1 root entrypoint.
The Create-page factory mapping remains in `CREATE-COIN-EVIDENCE.md` (734638,
586090 and metadata helper 421159/778435). No captured JavaScript is executed.

Original inspected baseline: `e22319e576126b6189dbae0101a838987a94c58a`.
Integration refreshed against `60bdd8a7a522921058d18563bb9335d2a06aec75`.
The merged video-cover lifecycle and external-link confirmation/privacy
controls are preserved; supplied instruction metadata remains independent
of this local media draft.
SDK Git blobs: `src/index.ts` `4fad5b89f2b28b2b61fab8cb4cd3c81f3ff8ee91`,
`src/sdk.ts` `b38f291d532d922600cd488ff08e2c5364d6bda1`,
`src/onlineSdk.ts` `65663e9d589390c075760af2ad4876d91a6e47e1`,
`src/idl/pump.json` `55560e00ba1df6a418b9efc4f24b8bedf3fa9a18`.

`PumpSdk.createV2Instruction` supplies the Token-2022 program, Mayhem constant
accounts and deterministic PDAs, then uses Anchor `.instruction()`. The IDL
`create_v2` discriminator is `d6904cec5f8b31b4`; there are 16 ordered fixed accounts,
with mint and user signer flags. No quote mint supplies no remaining quote
accounts (SOL). All three mode flags are explicitly false; creator fee defaults
to zero. No initial buy is composed. Required signer flags are displayed but no
signature is requested or obtained.

Before importing, the SDK entrypoint and transitive offline program setup were
inspected: `OFFLINE_PUMP_PROGRAM` calls `getPumpProgram(null)`, whose Anchor
provider has a null wallet and connection. The fee/AMM offline providers are
also null. The pinned agent-payments SDK builds its offline program with a null
connection and an inert wallet whose signing methods reject; it does not read
a local wallet. No `OnlinePumpSdk` is instantiated by this consumer.

## Input and lifecycle policy (local design)

- Explicit mint, creator and payer public keys only, canonical Base58 after
  surrounding whitespace removal. No address is generated or assumed owned.
- Uses the draft's name/ticker validator and preserves text, including Unicode.
  Unpaired UTF-16 surrogates are rejected in name, ticker and URI to prevent
  silent UTF-8 replacement. This is not chain-limit or name-eligibility validation.
- A separately supplied absolute HTTPS/IPFS metadata URI, at most 2,048 UTF-8
  bytes, without whitespace or embedded credentials. This is an inspector input
  bound, not a recovered chain/storage limit. URI syntax does not prove a CID,
  resource, safe content or relationship to the draft. It is never fetched.
- Changing inspector inputs immediately hides prior output and supersedes any
  pending computation. Changing draft name/ticker remounts the inspector and
  clears its addresses/output; clearing also invalidates pending work.
- Local state only. No provider, wallet storage, signing, RPC, account fetch,
  blockhash, Transaction, upload, simulation, submission or fee estimate.

The output contains program ID, hexadecimal instruction data with byte count,
and ordered account keys with signer/writable flags. It is not a transaction
and does not demonstrate account existence, mint availability, funding, program
configuration, metadata integrity, current eligibility or a successful launch.
Advanced quote chains, initial buys, Mayhem, cashback and holder rewards are not
exposed. SDK source and captured evidence remain unchanged. No compatibility or
completion milestone is promoted by these finite local checks.

## Verification

After the normal frozen workspace install and SDK build:

```sh
pnpm test:create-instruction
pnpm --filter @pump-reconstruction/frontend typecheck
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/create.spec.ts tests/create-instruction.spec.ts
```

The deterministic unit tests exercise the actual app consumer, compare every
account and byte with the SDK, independently decode Borsh strings/creator/flags,
check IDL signer flags/discriminator, reject malformed inputs, and forbid fetch.
The browser regression exercises the user controls, clears stale outputs,
retains the disabled launch action and records external requests. Running tests
against synthetic public addresses does not establish ownership or chain state.

## Dependency compatibility and recorded results

The first real browser/SSR compilation exposed the pre-existing agent-payments
patch's unconditional Anchor default import. Anchor's browser build has no
default, so importing the SDK root failed both graphs. The patch now imports a
namespace and reads an optional CommonJS default with `Reflect.get`, falling
back to the named-export namespace. Both module formats resolve the same BN
constructor. The three lockfile patch-hash references were updated to the
patch's SHA-256; all package versions and integrity/resolution entries are
unchanged. A frozen offline install validates the patched dependency. No SDK
source edit, replacement package or provider stub is used.

Historical first-candidate checks (Node 24.22.1 and pnpm 10.24.0):
- Frozen offline install with scripts disabled: passed.
- Complete app build (SDK CJS/ESM/declarations, backend, Next browser/SSR/static
  generation): passed after the compatibility correction.
- Sequential app typecheck: passed. An earlier concurrent check raced the SDK's
  clean output directory and failed missing declarations; it is not a pass.
- Five existing published-SDK differential tests and five app-consumer tests:
  passed; pure-JS bigint fallback. All 31 SDK source files match the archive.
- Ordinary app test command: stopped at tsx CLI IPC `listen EPERM` before the
  backend tests. The focused consumer suite uses the supported Node tsx loader
  without that CLI IPC server; this is not a full test-suite pass.
- App evidence gate: fails because this cloud source-only snapshot lacks most
  captured objects. No capture is regenerated or fabricated.
- Browser interaction and matched-viewport screenshots: authored but not run;
  the environment's browser/IPC restrictions remain in force. No visual parity
  or runtime browser pass is claimed.

## Refreshed integration checks

On `60bdd8a7a522921058d18563bb9335d2a06aec75` plus this inspector,
using Node 24.22.1 / pnpm 10.24.0:

- Frozen offline, scripts-disabled install; complete SDK/backend/Next build;
  sequential package typechecks: passed.
- Explicit `tests/sdk.test.mjs`, `tests/create_video_bindings.test.mjs`,
  `tests/create_video_preview.test.mjs` and
  `tests/video-ready-reentrancy.test.mjs`: 43 tests passed.
- Explicit actual-consumer suite: 5 tests passed through the Node tsx loader.
- App evidence gate: 698 retained objects, npm integrity and all 31 unchanged
  SDK source files passed. Unlike the original source-only test snapshot above,
  this snapshot contains the authenticated inputs required by that gate.
- Repository-root static gates: 9 capture-integrity checks and 6 synthetic
  byte-comparator tests passed independently at the same commit.

The refreshed form preserves the current video lifecycle/reentrancy correction,
external-link privacy confirmation, and existing profile/public-wallet test
commands. None of those controls is replaced by the inspector. These checks
are explicitly selected maintained-source tests, not an aggregate workspace,
browser, visual, live account, upload or launch qualification. Browser cases
remain authored but unrun. Historical private React/jsdom checks do not replace
native browser qualification.
