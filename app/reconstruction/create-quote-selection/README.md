# Captured Create quote-selection coordinator

This recovers the complete selected quote coordinator from archived Create
factory 734638, together with its radio, inline icon and dialog gateway:

| Component | Compiler slots | Boundary |
| --- | ---: | --- |
| `eq` | 62 | Actual SOL/USDC/stock/Pump selection, supplied stock-list result, local flags, selected-record display and picker callbacks |
| `eH` | 10 | Complete button/radio role, selected classes, `aria-checked` and click handoff |
| `ez` | 6 | Complete inline SVG; no remote image acquisition |
| `eL` | 15 | Complete open-state gateway and conditional external picker-body mount |

The actual default Create component mounts `eq`; its same-store parent pair
read is bound separately as inert context. The producer authenticates eleven
physical source roles, forty-one witnesses and all current indexed variants.
Both 464649 asset variants agree only on the selected SOL image literal; no
whole-module identity or active-loader winner is inferred.

This is a source-bound, unmounted coordinator, not an asset-search UI or a
launch workflow. Original captures and the maintained offline Create form are
unchanged. #1869 validation/social/dialog and #1884 advanced-fee work remain
separate. The 275799/provider/label/asset dependencies already have source
attribution; their inclusion here earns no first-recovery or copy-retally claim.
Existing SDK, media #681/#885 and upload #1817 are unchanged. There is no runtime
import from an unmerged research PR.

## Preserved selection semantics

The actual quote-store initializer starts at `{kind:'sol'}`. `setPair` stores the
supplied pair and derives `isQuoteMintEnabled` from `kind === 'usdc'`.
`setIsQuoteMintEnabled` resets the pair to SOL or USDC. The original store
provider and React subscription implementation remain an explicit capability.

The stock reader is always called by the coordinator. Its data nullishly falls
back to a memoized empty array. The third radio appears when that supplied
array is nonempty **or** the current pair is stock/Pump. It therefore remains
available for a selected stock/Pump pair with empty or pending data. The source
does not disable the ordinary radios while loading.

Changing to stock through the radio reads the supplied Mayhem and fee-sharing
facades at callback invocation. For each truthy flag it invokes the original
false setter and info toast, in source order, before setting the pair. Same-kind
selection is a no-op; an already stock/Pump third radio does not repeat this
branch. SOL/USDC changes do not run it. Exceptions propagate as in the source;
no additional repair, retry or launch-admission policy is added.

The stock-picker callback stores the exact stock object reference, then closes.
The Pump-picker callback shallow-spreads the complete supplied record and uses
`name ?? mint` and `symbol ?? mint`, then closes. Empty strings survive; missing
values fall back. Neither direct picker callback repeats the radio's local
flag branch. Supplied missing/empty Pump-name cases qualify those defensive
callbacks only; original search eligibility is outside this packet.

Open state is independent of quote kind. A supplied quote change does not
invent a dialog reset. The gateway ignores a true open-state notification and
closes on falsy notification through the original close callback.

## Exact external handoffs

The coordinator passes **six** fields to the complete `eL` gateway:
`isOpen`, `isLoading`, `stocks`, `onClose`, `onSelect`, `onSelectPumpCoin`.
The gateway mounts the external picker body only while open and passes **five**
fields: `isLoading`, `stocks`, `onSelect`, `onSelectPumpCoin`, `onClose`.
The body does not receive `isOpen`.

The large original `eM` body contains asset filtering/search/query behavior and
is retained as an inert full-scope witness. The actual 47938 stock hook and its
loader/schema handoff are also static witnesses. This module implements none
of those requests, schema engines, search admission, retries or service policy.
The `useStocks()` port supplies the already selected data/`isPending` snapshot;
the picker port supplies the exact selection/close callback interface.

`client.d.mts` contains local structural types for observed JavaScript call
signatures, not recovered original TypeScript or a new backend schema. Ports
also cover the bound-store initializer, React/compiler/JSX, translator/toast,
Mayhem and fee-sharing `getState` facades, class merger and shared image/art/
avatar/dialog primitives. The selected image literals are `/chains/solana.svg`
and `/usdc2.png`; no SDK mint construction or image request is emitted by the
source model. The actual label helper is identity, not invented normalization.

The fee-sharing provider contains private reservation/Keypair work. That entire
initializer stays inert; only the coordinator's calls to the supplied facade
are executed. No original provider state, reserved value, wallet, viewer,
session, credential or cookie is read. Supplied setters test invocation and
ordering, not original resource cleanup or financial admission.

## Reproduction and finite qualification

With existing pinned application dependencies, from the repository root:

```sh
node app/scripts/original-create-quote-selection.mjs --check
node --test app/tests/original_create_quote_selection.test.mjs
```

The producer parses captured bytes without executing factories, transcribes
only the selected controls and needed inert dependencies, and compares
canonical UTF-8 bytes for client and contract. `--write` regenerates both.
The shared source reader and captures are unchanged.

Direct checks use explicit virtual renderer/store/state/memo ports. Child
component memo caches are artificial; these checks do not qualify React
scheduling. They cover full selection→state→display/flags/dialog handoffs,
object identity, defensive fallback, error propagation and seven actual
maintained-verifier mutations. The port declarations have a targeted typecheck.

The real React/compiler method is frozen before execution:

```sh
node app/reconstruction/create-quote-selection/qualification/browser.mjs \
  --source FULL_PUBLIC_OR_LOCAL_COMMIT \
  --output "/tmp/create quote fresh qualification"
```

Its planned eight cases cover actual radio choices/availability, same-kind
behavior, flag call order, gateway/body signatures and close notifications,
stock identity, Pump shallow/default branches, pending data, translator memo
updates, independent open state and cleanup. The stock reader, picker, local
flags and shared renderer primitives are authored synthetic ports. They make
no query, media or provider acquisition. A result is pending until an explicit
receipt is added; no browser pass is claimed by this source README.

The runner accepts fetchable public source commits, verifies the four actual
runtime files against Git, preserves bundle/input/result/trace outputs and
readbacks, and closes its ephemeral GET-only loopback server and browser.
External requests are blocked and no Next process starts.

There is no original factory execution, asset search/backend implementation,
wallet/private H, reservation, fee calculation, submit/upload, instruction,
signing or transaction execution. No current assets/prices, original provider
winner, mounted website, whole-Create completion, original DOM/visual/runtime
parity, API/native compatibility, security clearance or milestone is claimed.
