# Captured advanced creator-fee control

This recovers the complete used advanced creator-fee control in archived website
factory 734638: local state initializer `C`, optional decimal/range validator
`T`, all 39 compiler slots of the field/error component `S`, and its actual
quote selector `O`. The default Create component mounts `S` directly. This
boundary was absent from maintained source models; it is not a mounted new
Create feature or an implementation of fee calculation.

The producer authenticates six current factory roles and 38 source witnesses.
It binds the actual controlled input and error/ARIA consumers, both later
parent state subscriptions, the pre-upload `T` recheck, and both later `I`
projection callers. Those downstream operations remain **static witnesses**:
`I`, submission, funding, instructions, upload and transactions are never
emitted or invoked. Base-field/social/dialog recovery #1869 and existing SDK,
media #681/#885 and upload #1817 retain their separate scope and attribution.

## Complete selected control

- `C` initializes an empty string and exposes the original raw partial-state
  setter. The component calls its bound hook **without a selector**, so the
  supplied provider must support the original whole-state default.
- `T` accepts a falsy/empty value; otherwise the exact decimal regular expression
  and `Number(value)` range 0.01 through 3 apply. Empty is optional, `1.` is valid,
  `0` and `.` are invalid. Nothing trims, rounds or canonicalizes input.
- `O` reads `snapshot.pair` through the supplied quote hook. The complete used
  275799.Q helper is exactly the `stock`/`pump` kind predicate. `sol`, `usdc` and
  other kinds hide the control. There is no extra asset, viewer or wallet gate.
- `S` retains all source memo dependencies, translation calls and selected
  optional label. Its raw change callback forwards `event.target.value`.
  The input declares `type=text`, `inputMode=decimal`, `maxLength=4` and
  `autoComplete=off`. JavaScript does not add a separate length clamp.
- The invalid state controls the original error paragraph, `aria-invalid` and
  `aria-describedby`. The advanced section receives `defaultOpen=true`.
  Actual disclosure behavior and styling belong to the external primitive
  components, not to this reconstruction.

One runtime factory owns one local store shared by its controls; a new runtime
factory represents a separate explicit host. Quote changes do not reset the
fee string. These are input/control semantics, not fee/accounting admission or
financial validity claims. Original deployment/provider selection is unknown.

## Explicit ports

`createAdvancedCreatorFeeControl(ports)` returns `{ Control, store }`.
`client.d.mts` provides **local structural types for witnessed JavaScript call
signatures**, not original recovered TypeScript:

| Port | Actual selected call |
| --- | --- |
| `createBoundStore` | Direct `initializer => boundHook`; supports whole state or selector |
| `useQuoteState` | `selector(snapshot)`, where the selected path is `snapshot.pair.kind` |
| `useTranslation` | Hook returning `{t}`; keys and min/max variables remain source-bound |
| `compiler` | Memo cache capability called with 39 |
| `jsxRuntime` | `jsx`/`jsxs` renderer calls |
| `Collapsible.Y/v/C`, `Input`, `Chevron` | Opaque renderer-compatible primitives |

No original store/provider, renderer primitive, translator, quote acquisition,
wallet, viewer/session or service is loaded. The included standalone host uses
real pinned React/compiler and explicitly authored synthetic state, quote,
translation and primitive ports. Its translation text and disclosure markup
are local test design; they do not establish original wording, DOM or styling.

## Reproduction and proof limits

From the repository root with existing pinned application dependencies:

```sh
node app/scripts/original-create-advanced-fee.mjs --check
node --test app/tests/original_create_advanced_fee.test.mjs
```

The producer parses authenticated captured bytes as inert AST, transcribes
only the selected nonmutating control, and checks canonical UTF-8 bytes of the
client and contract. It checks all indexed variants of the six selected IDs.
`--write` regenerates the two derived files. Raw captures and shared helpers
are unchanged.

The direct checks cover the full field→state→validation→error/ARIA path,
quote visibility, raw values, source memo behavior and actual verification-gate
mutations. Synthetic events that exceed four characters demonstrate the absence
of a callback clamp; they do not claim native input admits those events.

The finite standalone React controller is frozen before execution. Once the
selected source revision is available, run:

```sh
node app/reconstruction/create-advanced-fee/qualification/browser.mjs \
  --source FULL_PUBLIC_OR_LOCAL_COMMIT \
  --output "/tmp/create fee fresh qualification"
```

Choose a new output directory. The controller requires the four actual runtime
inputs to equal the selected Git commit before bundling. A fetchable public
commit with identical runtime bytes is supported; it does not require an
unpublished historical HEAD. It retains inputs, bundle, result and trace, checks
input hashes again afterward, and closes its ephemeral GET-only loopback server
and browser. External requests are blocked. No Next server is involved.

Planned finite browser cases: actual pair visibility/optional attributes;
trusted input range/error transitions; native four-character maximum and raw
whitespace; hidden/reshown state retention; actual compiler response to changed
translator identity; supplied-state redraw and hook cleanup. Their source and
method are frozen before proof. Results are pending until an explicit receipt
is added; no browser pass is claimed by this source README.

There is no captured factory, private whole Create/H, fee projection, submit,
upload, instruction, signing, transaction, credentials/cookies, provider request,
original runtime parity, mounted website, visual parity, native compatibility,
security clearance or feature-milestone claim.
