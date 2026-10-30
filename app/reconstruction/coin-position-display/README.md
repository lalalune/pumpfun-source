# Complete ordinary coin/position display workflow

The actual ordinary MAIN row349919.f passes supplied positionRead and coin
metadata to335703.f. This recovers that whole memo-wrapped16-slot read owner,
the complete local16-slot projection handoff, its8/6-slot fallback skeletons,
and full downstream223363.f154-slot display owner:200 slots. The local amount
format callback and consumed ring data are included in this coherent unit.

Both physical335703 origins are byte-identical. All three223363 variants compare
equal under the existing lexical-alpha AST comparator and their actual import
IDs. Complete callbacks/statement order/memo slots remain. All four79631 read-hook
variants, both672287 price-hook origins and actual financial/renderer/formatting
exports are pinned as **interface witnesses**, not recovered providers or a
global active loader winner.

Authenticated root Flight→conditional mobile163807.HomeView eH→ez→eG→349919
provides static conditional MAIN admission and the actual incoming position
descriptor. It does not establish original returned rows, position observations,
rendered Home behavior or a recovered query/parent coordinator.316917/individual
coin/token-detail incoming surfaces remain excluded. #1959 admission and prior
parent/display work are credited, not retallied.

## Explicit boundaries

`createCoinPositionWorkflow(capabilities)` returns `{CoinPosition,PositionDisplay}`,
corresponding to the two actual public source exports. Construct one stable
workflow before mounting. Full renderer variants, namespace roles, source API
signatures, raw offsets and hashes are in `PROVENANCE.json`.

| Capabilities | Actual source API |
| --- | --- |
| `jsx,jsxs,Fragment,useMemoCache,memo,Skeleton,classNames` |732486/445242/352386.memo/248496.l/338319.c |
| `usePositions` |79631._(descriptor)→`{positionFor,isLoading}`; always constructed, even when disabled |
| `useLivePrice,projectLivePosition,projectServedPosition` |672287.f(mint),889451.j(raw,price) and889451.y(raw); **opaque outputs**, no valuation or accounting recovered |
| `LocalImage,ChainBadge,CoinAvatar` |928529.default facade→876299 CJS.Image,667876.f,34011.CoinAvatar |
| `useTranslation,useClientReady` |398902.f→`{t,i18n:{language}}`,170450.f() |
| `pnlTone,moneyCompact,moneyValue,moneySigned` |540805.k/l/w/u; financial/formatting policy external |
| `RelativeTime,ClosedBadge` |529841.f,908163.E |
| `formatLargeAmount,makeNumberFormatter,formatFullDate,formatDate` |890088.J/R/V/u; locale/formatting APIs external |
| `normalizeNumberText,localeFor,defaultLocale,parseTimestamp` |714283.f,592209.v/T,633311.l; parser/locale policies external |

The accepted `positionLookupKey` from the existing positions-by-mint reader is
imported unchanged and bound by its file hash and original contract. No new key
policy, reader, client, acquisition or helper recovery credit is claimed. That
module performs no request on import; this workflow never constructs its reader.
The original price/projection policies remain required supplied capabilities;
none of their mathematical internals is copied or replaced.

## Source behavior

- A truthy supplied positionPnl suppresses query enablement. Otherwise a nullish
  positionRead permits querying. The read hook is still constructed on every
  render with exact userId, single namespaced mint, enabled and conditional
  polling option. Falsy/non-null supplied PnL retains the source distinction
  between boolean admission and nullish selection; no new input validator is
  added. Query rows use namespaced positionFor first, then raw mint fallback.
- Supplied read loading/state takes precedence when querying is suppressed.
  The strip/framed/flat/terminal loading skeleton branches remain complete.
  The projection frame passes raw mint to the price capability and performs
  only source nullish selection of its opaque live/served projection result.
  It forwards positionUsd/isClosed/exitProceedsUsd/netPnlUsd without calculating
  those values or inventing zeros.
- The full display keeps strip/feed/elevated/pill/row branches, name/symbol
  fallbacks, finite-value admission, value→exit→closed-date/tag→dash precedence,
  profit absence, child/action slots, CoinAvatar/chain metadata and local-image
  renderer handoff. Source clamps/guards and raw failures remain.
- Closed/last-trade stamps call the supplied parser/locale/readiness/time APIs;
  native Date serializes only their returned value. No clock, timestamp parser,
  localization, price or financial-service policy is invented. The local
  amount callback retains its1000 threshold/Intl-style options through explicit
  formatting ports, not a new financial normalization algorithm.

## Reproduce

From `app/` with existing pinned dependencies:

```sh
node reconstruction/coin-position-display/verify.mjs --check
node --test tests/coin_position_display.test.mjs tests/original_source.test.mjs
PUMP_COIN_POSITION_OUTPUT=/your/isolated/output node --test tests/coin_position_display.browser.mjs
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
```

From repository root:

```sh
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

The verifier parses authenticated captures inertly, then regenerates complete
editable owners under exact explicit APIs. Original captured factories/runtime
are never imported or evaluated. Regenerate deliberately with `--write` only
after reviewing source/variant changes.

The realReact/compiler/nativeDOM host supplies a synthetic Context read hook,
scripted opaque financial projection outputs, compatible renderer/money/date/
translation APIs and a self-contained data image. Native activation reaches an
inert supplied action-slot callback. It performs no position, market, HTTP/RPC,
price, wallet, protected or financial operation. Only local root/bundle GETs are
allowed. Valid numeric synthetic timestamps are supplied; locale/parser/money
policy equivalence is not qualified. Authored CSS does not reproduce original
Tailwind/layout/pixels or responsive density policy.

No original query cache/scheduler/provider, live data, finance/valuation/policy,
service/native/API/security/translation/UI/pixel parity or feature-completion
claim. Existing pages, SDK, captures, dependencies and ledger remain unchanged.
Original shipped authorship remains with the material; public names and
capability admission are editable integration adaptations.

## Finite qualification record

The complete eight-file source/method freeze is
`4fdd2faa8827b80439f07e663b5bc9b6481afa03`. Thirteen new Node/SSR/source-negative
checks and eleven shared cases pass. The first extraction attempt stopped at a
generator-local temporal-dead-zone error before any generated source was written;
its raw failure is retained. The loop binding was corrected before freezing.
The unfrozen attempted generator is not separately qualified or retained as a
replay implementation. Positive image-facade→CJS getter attribution was added
before the final source/Node checks; earlier checks are not transferred to
that changed verifier.

One realReact/compiler/nativeDOM workflow passes at390/1280 in1.07seconds. It
records initial enabled read/loading, namespaced→raw-key result fallback,
opaque served display, supplied PnL overriding provider loading with disabled
read construction, explicit supplied-read loading, closed exit strip, direct
closed timestamp, native inert action-slot activation, pill/zero-value display
and actual unmount. This is generated source through a compatible synthetic
Context/provider/renderer host, not an original React-query or financial system.

All16 actual bundled inputs and8 declared inputs are retained. Only four
loopback root/bundle GETs occur; no unexpected/remote attempts or page errors.
Browser/server close; two React DevTools info messages remain.698capture/npm/
unchanged-SDK integrity and progress checks pass. No code, timeout, method or
fixture correction followed the first frozen browser run.

`validation/VALIDATION.json` binds exact frozen inputs and compressed/raw
receipts. Publication adds only this qualification text and receipt files.
Initial pending mandatory-gate text remains historical; final exact-public
checks are stated in the PR without another runtime run.
