> Current extension: [PUBLIC-WALLET-EVIDENCE.md](PUBLIC-WALLET-EVIDENCE.md) adds an opt-in, public-address-only Wallet Standard workflow. The original unavailable-auth adapter and its boundary remain. Statements below about disabled wallet discovery describe the prior chooser checkpoint; the new panel does not implement server sign-in.

# Sign-in presentation reconstruction

The [Auth backdrop press-origin correction](../../research/auth-backdrop-press-origin-20261029/README.md)
qualifies a later local dismissal fix. An aborted press on the public wallet's
Disconnect button could retarget its click to the dialog and close the chooser.
AuthControl now requires the press and release to be outside. Trusted desktop
and mobile before/after cases use a native `closedby="any"` button control;
18 product-browser cases and 28 controller/model tests pass. Seven unmounted
synthetic-adapter browser cases remain skipped. This does not apply the separate
public-wallet child-focus or connect-result changes, recover original backdrop
code, enable sign-in/signing, or add compatibility/feature credit.

## Scope and acceptance boundary

This adds the missing shared **Sign in** entrypoint and evidence-mapped chooser
presentation. It does **not** implement authentication. The product entrypoint
is fixed to an unavailable, read-only adapter; there is no provider SDK, remote
request, credential input, email/OTP form, wallet-extension detection, account
creation, session token, cookie/storage access, signing or transaction command.
An address alone is never treated as proof of identity. No backend operation or
visual/API compatibility count is increased.

The local contribution is the reachable modal, wallet catalogue
preview/expansion/back, async loading/error/timeout/retry/dismiss transitions,
focus and responsive presentation. Disabled provider rows and the persistent
local-unavailable notice distinguish UI reconstruction from working sign-in.

## Observed capture authority

All factory references are from `recovered/modules.json` and the immutable
`evidence/web/manifest.json` checkpoint captured at
`2026-10-28T10:48:45.546100+00:00`. Factory ranges are half-open UTF-16 code-unit
offsets in UTF-8-decoded source, not byte ranges. Captured code was read as data,
never evaluated or imported.

| Factory  | SHA-256                                                            | Source and range                                            | Observed role                                                                                                 |
| -------- | ------------------------------------------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `400466` | `b55e1d78341162edfc6c5ff1ba32c4b4faa3d0ade6de3a39f440fe39f2e9e5dd` | `evidence/web/objects/13c13db9eb86191b.js`, `92522..190511` | Shared Topbar; `sign-in-button`; hydration/address/authReady gating; opens wallet; async loading and error UI |
| `233555` | `8962e9fa8cb7cfd50c25b3ad5028b74396534a59200744973d8795e251066fcd` | `evidence/web/objects/e02656dccdb8d127.js`, `2323..3890`    | Lazy chunk graph, resolves module `544115`                                                                    |
| `544115` | `7c806db37992e04be39864fd8cac4526e4e68f1544570af0283f501e3c24bd59` | `evidence/web/objects/44c4a5703d358ccb.js`, `119..148`      | Re-exports `180013`                                                                                           |
| `180013` | `0edfb5b3c164fa6adfa0659cc15852ed0813a1a185d909c930e253fbcaa4d7a7` | `evidence/web/objects/5b258d2d30442e7e.js`, `119..109929`   | Wallet modal, social/email entry states, list prioritization, expansion/back, account-ready branches          |
| `574472` | `e58749a6217d91ac7d17f86aaecaf4bd89b7aa36ca49025a064cc2c6020f4238` | `evidence/web/objects/1e479323ffe53c14.js`, `28729..28826`  | Shared auth context read hook, not a session implementation                                                   |
| `170450` | `72a61a3e662f4e2995ea53610e55b0658ec866cf82ddca6c904962252fe06ff7` | `evidence/web/objects/994c0030bcc62017.js`, `10785..10893`  | Client hydration check (`useSyncExternalStore`, false server / true client)                                   |
| `29542`  | `ede316c07dd8ceb3faff4f840fefbb61a5b1a18d372e600225db0f8410a661bd` | `evidence/web/objects/fd402d4185b44ce9.js`, `5207..9672`    | `NAV_BAR.BUTTON.LOG_IN = "Sign in"`                                                                           |

The Topbar chunk is
`https://pump.fun/_next/static/immutable/chunks/1ggmlsuhd8iw1.js`
(whole-object SHA-256
`15e7cb5caef8d58d0d263486883e7aac6e39e9e2f7e037af29887849bd0cd6c6`).
The Wallet chunk is
`https://pump.fun/_next/static/immutable/chunks/3fjm9jo0gjmjv.js`
(whole-object SHA-256
`037b0b4492487b245250942ee605b982526b37642d7d608f6a3fd62000ed853e`).
The recorded lazy graph includes that Wallet chunk, so this is a reachable
shared sign-in surface, not an unrelated SDK login string.

The Topbar imports `198825.useConnectWallet`; the current factory index has no
literal top-level `198825` entry. Its call sites establish `showWallet` and
`setShowWallet` usage, but this reconstruction does not claim the missing
provider/store implementation or assign it a guessed original filename.

### Captured transitions and layout

- Topbar: after hydration, an absent address renders **Sign in**. An address
  without `authReady` renders a loading account slot. Ready account controls
  require both address and auth readiness. This source is not proof of a valid
  server session and does not authorize creating one locally.
- Open resets the prior Privy failure and returning-login prompts, requests
  the wallet modal, and lazy-loads `Wallet`.
- The lazy loading fallback uses a **15,000 ms** deadline. Loading is a dialog;
  load error or timeout is an alertdialog with **Try again**, **Refresh the
  page**, and **Close**. A retry resets the local timeout.
- The chooser has **Welcome back**, Google, Apple, GitHub and email controls,
  then the wallet section. **More wallets** expands the list, changes the
  heading to **Select wallet**, and exposes **Back**.
- Wallet score is `2 × recent + installed`; stable descending order is used.
  Preview chooses at most two installed/recent wallets, filling remaining
  slots from Phantom then Coinbase Wallet. Expanded view uses the full list.
  The source also inserts a Magic Eden catalogue entry when unavailable from
  the adapter. No such entry establishes installation or wallet ownership.
- Captured modal width is `min(356px, 100vw - 32px)`, with 16px padding; loading
  fallback has a 22px radius, black/60 blurred backdrop and centered placement.
  Expanded wallet scrolling is capped at 360px. Local CSS uses those values
  and the repository's captured color tokens.

## Exact locale copy

`scripts/extract-auth-copy.py` verifies the retained `/live` record by URL,
final URL, status, timestamp, path, length and SHA-256 before parsing the
`self.__next_f.push` arguments strictly as JSON. It joins string frames and
reads the unique `c6` record with `locale: "en"`, selecting 23 explicit keys.
No code is executed, no arbitrary resource reference is followed, and no
network request is made.

- URL: `https://pump.fun/live`
- Object: `evidence/web/objects/c45d40b52df03727`
- Length: `785309` bytes
- SHA-256: `aeff704c15d99482fe6e6347a92db0170dffeceb940a70e61dcc10002b006355`
- Deployment marker in HTML: `dpl_AimdmiN1oNXBp4XEjm3dPQeskJrw`
- Generated subset: `src/app/auth/auth-copy.json`

Google/Apple call-site keys are `auth.continue_with_google` and
`auth.continue_with_apple`, but the retained English resource object does not
contain the `auth` namespace and repository searches did not locate their
English values. Plain **Google** and **Apple** are explicit local accessible
fallbacks, not claimed verbatim captured translations. The GitHub label is
retained verbatim as **Continue with GitHub**.

## Local implementation and deliberate differences

- `SignInControl` is the sole product entrypoint, with no environment
  flag, query override or browser-global injection. It always chooses
  `unavailableAuthAdapter`; its only prop is a presentation-only trigger class.
- The live captured shell (`components/shell/TopBar.tsx`, reached from the root
  layout since PR #685) mounts it in the signed-out `data-pf-auth-slot="out"`
  position that previously held the disabled captured `prepaint` Sign in button,
  reusing that button's captured geometry and classes. The legacy
  `src/app/app-shell.tsx` mount is unreachable from the root layout. No
  pixel-parity claim is made for the interactive trigger.
- The adapter only has `read(AbortSignal)`. It returns a named wallet catalogue
  with `readiness: unavailable`, no recent wallet and `session: unavailable`.
  It has no login, logout, connect, detect, challenge, sign or submit method.
- `AuthDialogController` implements loading, deadline, generic error, retry,
  ready and closed states. Attempt generations and cancellation prevent late
  results from reopening the dialog or replacing newer state. Error payloads
  never reach the UI. These concurrency safeguards are local design.
- A strict presentation parser rejects authenticated/signed-in claims, live
  sources, duplicate/invalid wallet labels, unsupported readiness, and
  unavailable-source claims of remembered or installed wallets. The explicit
  synthetic-test source is accepted only by a separately opted-in test
  component; no authenticated presentation is supported even there.
- Social/wallet controls are disabled. The email row is text, **not an input**;
  there is no OTP panel. The trading subtitle and upstream prompt to download
  a wallet are deliberately omitted: this app cannot sign in or detect
  extensions, so those prompts would mislead users.
- Local unavailable/synthetic notices, wallet initials instead of external
  icons, text provider buttons, and the existing local Pump logomark are
  explicit visual deviations. No external image, provider identifier or
  upstream tenant configuration is reused.
- Native `<dialog>` is portalled to the document body so the shell's mobile
  inert subtree cannot hide it. Escape, close and backdrop dismissal cancel
  pending reads. Native modal focus containment plus explicit Back/More
  focus restoration are local accessibility safeguards. When a state change
  removes the focused control (for example Retry), focus returns to the
  persistent Close button only if no in-dialog control retains focus. Path/history
  navigation dismisses the dialog without changing or adding URL state.

## Verification commands and acceptance

Run from `app` with the repository's pinned dependencies, without relaxing
release-age, lifecycle-script or network policies:

```sh
python3 scripts/extract-auth-copy.py --check
python3 -m unittest discover -s tests -p test_auth_copy.py
pnpm --filter @pump-reconstruction/backend exec node --import tsx --test ../../tests/auth_interface.test.ts
node --test tests/auth_fixture_helper.test.mjs
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/auth.spec.ts
```

Additional synthetic browser states are opt-in and **must run in an isolated
test checkout**, never in a served or deployed application directory:

```sh
cd packages/frontend
AUTH_INTERFACE_TEST_MODE=1 node tests/with-auth-fixture.mjs pnpm exec playwright test tests/auth.spec.ts
```

The helper refuses a preexisting route, verifies template bytes, creates only
`src/app/auth-interface-test/page.tsx`, and removes it in `finally` after the
child exits. If the bytes changed, it refuses to delete unrelated work. The
test template is outside product source, never part of a normal route/build,
and contains only labeled synthetic non-authenticated states. Its adapter
exercises delayed ready, failure/retry, timeout, stale resolution, empty/long
wallet lists and malformed read rejection. No provider or account is used.

The browser suite checks default unavailable state, disabled actions, no
credential controls, list expansion/back, Escape/close, focus, history, no
external or mutating requests, and 320×640, 375×812, 768×1024 and 1440×900
layouts. Pure tests additionally cover synchronous adapter failure, repeated
opens, cancellation before the read begins, retry, disposal, bad records and
late resolve/reject suppression. Test-helper tests cover opt-in, collisions,
cleanup on child success/failure and preservation of unexpectedly edited
bytes. Locale tests cover retained hashes, malformed JSON, missing/duplicate
locale records and invalid label data.

At authoring time, focused pure tests and locale verification pass; browser,
full frontend build/typecheck and aggregate app gates remain pending the
existing frontend dependency release-age gate. Final test output and local
desktop/mobile screenshots must accompany integration before acceptance.

## Unqualified behavior

Original open-modal screenshots and an authorized authenticated reference
session are unavailable. The archived HTML contains locale data and a closed
shell, not this client-rendered open modal. Local screenshots cannot establish
pixel parity with an unobserved original state. Exact auth provider store,
feature-flag variations, returning-account flows, wallet detection, OAuth,
email verification, account linking, session expiry/revocation, signing,
balances and authenticated backend compatibility remain unimplemented or
unqualified. Captured strings and local tests confer no authentication or
security qualification.
