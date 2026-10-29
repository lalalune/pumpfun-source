# Public-address wallet connection

The shared TopBar's Sign in chooser now offers **Connect a public wallet**. This is a working, explicitly separate connection boundary: a registered Solana Wallet Standard wallet can expose its public address after an explicit click; account changes update that address; disconnect, unregistration, account revocation, dialog close, navigation or unmount forget it. A connected address is labelled **ownership unverified** and does not change the shell's signed-out state.

There is no backend request, challenge, session, JWT, cookie, storage write, signature, transaction construction or automatic reconnect in this workflow. OAuth, email sign-in, Privy and authenticated actions stay unavailable. No upstream tenant identifier or provider SDK is used.

## Evidence and distinction from prior work

`PUBLIC-WALLET-SOURCE.json` binds raw captured factories and six AST fragments to original capture SHA-256 values, UTF-16 ranges and strict UTF-8 boundaries. Run:

```sh
node scripts/original-contracts/public-wallet/verify.mjs --check
```

The verifier reuses the maintained source primitive from #684. It parses original capture ASTs; captured factories never execute.

- Factory **255220**, variant `62c580d029f0…`, in `08521d498c5b9e8f.js`: `wallet-standard:register-wallet` listener, `wallet-standard:app-ready` dispatch, object-identity registration and unregister closure. The other registry variant is not claimed to be the selected runtime instance.
- Factory **716464/254415/496309**, variant `7e1c970abe23…`, same physical object: `standard:connect`, `standard:disconnect`, `standard:events` feature identifiers.
- Factory **785552**, variant `fc18fd775817…`, in `bb8d7a9653ab0cc0.js`: actual import of registry255220; `tS` subscribes to `change`, connects explicitly (separate from its silent autoConnect path), reads the first account address through `PublicKey`, and supports optional disconnect. It also exposes signing features, which this bounded workflow neither reads nor invokes.

The existing #701 display-restore/pending-logout code and other original auth declarations remain independent and unchanged. No restored cookie claim or saved wallet is trusted here. The newly inventoried **198825** (`292b9629fd07…`) is a modal-state context, not a wallet connection or authentication provider; its name `useConnectWallet` alone does not establish a server protocol.

This is an independent implementation of the observed public protocol, **not recovered original TypeScript or original Privy/auth parity**. Deliberate local policies are: opt-in discovery; no passive account reads; only protocol-v1 Solana wallets with connect/events; canonical 32-byte base58 first Solana account; no remote wallet icons, legacy `navigator.wallets` migration, mobile handoff or autoConnect. Wallet metadata is untrusted and cannot establish installation, ownership or authorization. Object identity, not a provider name, distinguishes registrations. A 15-second deadline and generation guards reject late approvals; a cancelled prompt may remain open in the extension because Wallet Standard supplies no cancellation port.

## Verification and reproducible checks

```sh
corepack pnpm test:public-wallet
node --test tests/public_wallet_protocol.test.mjs
corepack pnpm --filter @pump-reconstruction/frontend exec tsc --noEmit --incremental false
corepack pnpm --filter @pump-reconstruction/frontend exec playwright test tests/auth.spec.ts tests/public-wallet.spec.ts
```

The 12 controller cases cover explicit prompting, no passive account reads, no signing/icon capability access, duplicate identity, malformed metadata/accounts, provider error privacy, cancellation/disposal/unregister races, timeout, account changes/revocation and disconnect rejection. The real loopback HTTP + Chromium test imports the maintained controller over HTTP and exercises the event handshake, approval, account change and cleanup while asserting no auth request or browser persistence.

The six product-browser cases exercise the actual SignInControl integration, declined prompts, late approval after close, unregistration, signed-out shell and unchanged storage/network boundaries. They capture local 320×640 and 1440×900 screenshots. The wallet fixture implements the public protocol with synthetic public addresses; it is not a live wallet, production account or authenticated upstream observation. Original open-dialog screenshots are unavailable, so no visual-equivalence claim is made. The existing archived `/explore` screenshot describes the closed signed-out page, not this new connection state.

The auth feature ledger remains pending for complete source/success/failure/consistency parity. This bounded local connection is not evidence of an authenticated backend, permissions, trades, account linking or complete wallet support.

## Recorded local result

[Validation record](visual/public-wallet-20261029/validation.json) binds the actual tested implementation `f102a5c122e212f70131bf65d0d94373d03124f6`, raw command/results, logs and local screenshots. All five new product UI cases passed; the selected auth/portfolio/public-wallet target finished 17 passed and seven explicit skips. Build and recursive typecheck passed. After restoring unchanged captures and prior evidence excluded by the sparse validation checkout, app evidence verification passed all 698 objects/npm/SDK checks and progress verification passed eight tests. The initial sparse-checkout failure is retained. This evidence supplement changes no frontend runtime source.

![Local mobile public-wallet panel](visual/public-wallet-20261029/public-wallet-320.png)

![Local desktop public-wallet panel](visual/public-wallet-20261029/public-wallet-1440.png)

## Optional disconnect correction

Wallet Standard's disconnect feature is optional, as the captured `tS.disconnect` feature guard shows. A supported connect/events-only wallet can share an address without implementing disconnect. The local controller always forgets its address first; it now explicitly reports that the wallet connection may remain active and can be managed in the wallet when no disconnect port exists. A new controller and product-browser case cover this actual protocol branch. The earlier f102/143 validation remains the preserved pre-correction checkpoint; new validation is recorded separately. No wallet authorization is inferred from local address forgetting.

The [follow-up validation record](visual/public-wallet-followup-20261029/validation.json) binds exact runtime `13b9ec932b657efebf32611ca80d9b39870bdbce`: all six product-browser cases, 12 controller cases, the unchanged AST source verifier, independent SDK/backend/Next production build, recursive TypeScript, all 698 app evidence/npm/SDK checks and progress with eight tests passed. Raw commands, logs and results are retained separately from the earlier checkpoint. The final receipt-only supplement leaves this runtime source tree unchanged.

## Wallet-panel focus continuity

Wallet discovery and account-state transitions replace controls inside a dialog
whose authentication state remains `ready`. The auth dialog's existing
loading/error focus recovery therefore does not run for those child-only
transitions. In an actual React StrictMode/jsdom reproduction, removing the
focused discovery, connect, cancel or disconnect control left focus on the
body; revocation and wallet unregistration had the same result.

The existing public-wallet section is now a programmatic focus target, not an
additional Tab stop. After wallet status or choices change, it recovers focus
only when its enclosing native dialog is still open and the active element is
the body. Surviving Close or other control focus is left untouched. Closing or
unmounting the dialog still disposes the controller and ignores late approval;
no wallet, account, provider, authentication or storage policy changes.

This is a local accessibility correction to the maintained consumer, not a
reconstruction of original focus-management code. The unchanged captured
protocol witnesses still bind the same three factories and six AST fragments.
No sign-in, source-equivalence or feature-completion milestone is added.

Focused cloud verification against app tree
`e3d6d8cd07df4f561a4fd058dad29d22de451bfc` (unchanged between main `60bdd8a7`
and observed main `a509b4f4`):

- The same eight actual React controls gave **six failures / two passes** on
  the original consumer and **eight passes** after the correction. The two
  preservation cases keep surviving Close focus and reject late approval after
  closing. These private checks use synthetic protocol promises, CSS and
  pathname ports, and a dialog open/close-state shim. They do **not** implement
  native top-layer focus trapping, real navigation or a wallet extension.
- **28/28** explicit existing public-wallet and auth-interface controller/model
  tests pass using Node with the ordinary `tsx` import loader. Direct Node
  type stripping cannot resolve the auth controller's extensionless import;
  that initial setup failure was not treated as a passing test run.
- The static source-witness verifier, complete SDK/backend/Next production
  build, all three workspace typechecks and the **698-object** app evidence,
  npm-integrity and unchanged-SDK checks pass.
- Six bounded browser regressions in `tests/public-wallet-focus.spec.ts` cover
  discovery, approval, cancellation, disconnect, revocation and unregistration.
  They inject a synthetic public-protocol wallet and abort HTTP outside
  loopback GET/HEAD. They are **authored but unrun** at this checkpoint.

No live wallet/signing/authentication request, native browser result, visual
parity, aggregate test suite or new root-static qualification is claimed here.
The earlier browser records in this document remain historical observations of
prior implementations, not execution of this focus correction.
