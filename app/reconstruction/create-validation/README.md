# Captured Create validation and dialog callbacks

This recovers a previously unmodeled, used boundary in captured website factory
734638: the actual text/social fields, complete `tn` validator, both callers,
social errors and the confirmation dialog's opening callback. It does not mount
a Create form or replace the maintained offline draft's separate safety policy.

The archived `/create` HTML names the selected physical chunk. The producer
authenticates that HTML, five physical factory roles (four numeric IDs), both
586090 constant variants, the actual caller bindings and 54 source ranges.
Ranges carry UTF-16 and UTF-8 offsets and hashes. These are archived Googlebot
captures; no current deployment, active provider or authenticated state is inferred.

## Reconstructed boundary

| Source | Included behavior | Local capability or limit |
| --- | --- | --- |
| 734638 default component inputs | Raw name/ticker/description setters; name change admits at most 32 UTF-16 units, ticker 10; ticker also declares `maxLength:10` | Supplied setters, no DOM or React scheduling |
| 734638 `tn` | All thirteen inputs, original first-error order and exact messages; success returns `undefined` | Supplied availability value and UTF-8 byte helper; no session lookup |
| 586090 `O`/`f`, both physical variants | Image/banner 4,500,000 bytes; video 10,000,000; name/ticker 32/10 bytes; description 2,000 UTF-16 units | Exact constants, not new media admission or a type schema |
| 426091 `q` | Complete Telegram, website and Twitter/X regular expressions | Native RegExp; no URL normalization or Zod runtime |
| 734638 `Q` | Complete raw change and blur callbacks, initial errors, actual field wrappers and error-span consumers | Supplied setters and functional error updater; no rendered component |
| Actual parent `<H validate=…>` | Captures the thirteen current-render values; catches validation errors, translates and reports the message, returns `false` | Supplied translator and `toast.c.error`; no toast provider |
| 734638 `H` opening callback | Complete missing-wallet prompt branch, validation invocation, open/error state changes and catch behavior | Supplied UI availability, telemetry/logger/state ports; no wallet/context hook |
| Actual dialog `onOpenChange` | Direct `setDialogOpen` identity | No extra close policy or invented callback |
| Later submit validator caller | Same thirteen field bindings, catch/report/return before upload | Static witness only; never emitted or called |

There is **no normalization step** in these selected callbacks. Whitespace is
retained, social blur changes errors only, and names containing spaces pass the
original truthiness check. Input change admission counts UTF-16 units; `tn` uses
an external byte counter for name/ticker. Description uses `.length`. The
validator does not add type repair, zero-byte/MIME checks, social length limits,
or server authorization. Other media selection and local form policies remain
separate.

807757.W is the already-attributed `value => new Blob([value]).size` helper,
including in open PR #1424. It is **not copied or claimed as new here**. That PR
is absent from the pinned base, so `createFieldValidator` requires a supplied
`utf8Bytes(value)` capability of that exact signature. Tests supply a local Blob
counter. There is no silent runtime dependency on an unmerged PR.

## Preserved event semantics

`createParentValidate(snapshot, ports)` captures individual field values once,
as the original callback does for a render. Later replacement of a property on
the supplied snapshot does not change an old callback; referenced media objects
retain their identity. On failure it evaluates the translator then calls
`toast.c.error` with its receiver intact and returns `false`. A failure in the
reporter itself can escape to the outer opening callback.

The opening callback calls validation synchronously but **does not inspect or
await its return value**. Consequently a normally reported validation failure
returns `false`, then the dialog still opens and its local error is cleared.
The separate later submit caller validates again and returns on error before
upload. Both source boundaries are retained. This is a captured event-order
quirk, not a vulnerability or a claim about backend admission. No submit or
upload implementation is exposed by this module.

The literal `previewStatus === 2` branch in `tn` can bypass the selected-thumbnail
requirement. Within the captured media hook the status initializes to zero,
the only setter call is `T(0)`, and no status setter is exposed. The model's
supplied status-two test covers the literal branch; it does not demonstrate an
original reachable UI state.

Whole `H` also contains Keypair/lease/funding/amount and submit work. It remains
inert source context. Only the complete nonmutating opening callback and direct
dialog setter are transcribed. Disabled-button financial gates, React compiler
memoization, resets, private providers and transaction callbacks are not executed
or modeled. `decodedJwt` is an opaque **supplied truthiness value** and
`walletAvailable` is an independent supplied UI flag; neither reads or validates
a credential, wallet or session.

## Use and verification

The module exports `createFieldValidator`, `createParentValidate`,
`createTextCallbacks`, `initialSocialErrors`, `createSocialCallbacks` and
`createDialogCallbacks`. All effects require explicit caller ports. There are
no default services, global session/storage reads or network operations.

From the repository root, with the pinned existing application dependencies:

```sh
node app/scripts/original-create-validation.mjs --check
node --test app/tests/original_create_validation.test.mjs
```

`--check` parses raw captured bytes without executing factories, reconstructs
only the selected callback source, and compares **canonical UTF-8 bytes** for
both the client and contract. It checks all indexed variants for the four IDs;
the chosen Create route context and equal constant variants are explicit, not a
global loader-winner assumption. `--write` regenerates these two derived files.
The source helper, raw captures, existing SDK, local form and package scripts are
unchanged. The new `.test.mjs` is included by the existing application test glob.

The finite tests use only in-memory events, Blob byte counting and supplied
setter/translator/toast/logger/UI ports. They exercise all validation branches,
ordering, UTF-8/UTF-16 distinction, social change/blur errors, snapshot lifetimes,
both opening branches and the ignored-false return. Seven mutations call the
actual maintained verifier, including noncanonical JSON and altered callbacks.
The synthetic Promise-returning validator tests the opener's literal no-await
behavior; the actual captured parent validator is synchronous.

Existing #681 presign/image/metadata binding, #885 video helpers, #1817 signed
video handoff and #1424 UTF-8 helper keep their separate attribution. This adds
no upload contract or helper credit. There is no original bundle execution,
HTTP (including loopback), provider emulation, signing, transaction, React/Next
run, mounted UI, native compatibility or feature-milestone claim.
