# Original language selector and resource workflow

The captured custom Settings language field renders `447890.f`. This component
normalizes the current i18n language, displays the original 35 locale choices,
guards unchanged/invalid/busy selections and invokes `411657.C` with its actual
37-namespace list. That client performs same-origin namespace GETs, writes the
locale cookie, awaits the supplied provider's language change, then refreshes
the router. The component clears its pending state in `finally`.

This is the complete selected component/client workflow, with explicit ports for
React, Select, i18n, router, fetch, logger and a synthetic document/location. It
adds no product Settings page, global translation implementation or locale
backend. The actual custom language control calls this client directly; it does
not use the separate generic `547562`/`214100` setting adapter. No unmerged local
settings-runtime dependency is introduced.

The generator authenticates seven explicit physical factories, actual descriptor
and custom-field consumers, and all complete retained AST regions. Only the
language export and used declarations are adapted from the co-registered
`447890`/`749099` factory; its trading sibling is excluded. Captured factories
are parsed as data and never evaluated or imported. Existing locale/copy work,
the original prize-format locale helper and privacy/local-settings mapping are
credited. No first-helper, whole Settings, active runtime-winner or milestone
claim is made. Original materials retain their authorship.

## Preserved source behavior

- Locale metadata/order, aliases and hyphen-prefix normalization come from
  `592209`. Unknown current provider language falls back to English. The
  option's native/English labels, flags and string marker are source-bound.
- Catalog GET is `/api/i18n/{locale}?ns=__all__`. Successful catalogs cache by
  instance and locale. The cache marks before awaiting: a concurrent call
  resolves without waiting for the first fetch. Failure removes that mark and
  logs the original formatted warning, permitting a later retry.
- Namespace GET requests only names whose `getResource` result is falsy, in
  supplied order, through `URLSearchParams`. JSON passes unchanged to
  `addResourceBundle(locale, "translation", body, true, true)`; no response
  schema or private provider merge implementation is invented.
- Normal prefetch/seed failures warn; the controller still proceeds to cookie
  write, awaited `changeLanguage`, then router refresh. A throwing cookie port
  stops before provider work. A rejected provider change leaves the prior
  cookie write and skips refresh. No atomic persistence guarantee is implied.
- The full selector keeps its original pending/transition guards and `finally`
  cleanup. Its ignored rejected promise can surface an uncaught provider error.
  There is no source cancellation on unmount; already-started cookie/provider/
  refresh work can finish afterward. These quirks are retained and explicit.
- Cookie parsing uses the first matching `pump_locale`, URI decoding and the
  same normalizer. Malformed URI values throw. The writer keeps the original
  path, one-year max-age, same-site and protocol-sensitive secure attributes.
  These functions use only the supplied document/location; importing and
  constructing them reads no actual cookie.

## Explicit integration

Construct instances once per intended original module lifetime:

```js
const catalog = createLocaleCatalog();
const cookie = createLocaleCookie({
  document: syntheticDocument,
  location: syntheticLocation,
  normalizeLocale: catalog.normalizeLocale,
});
const client = createLanguageClient({
  fetch: suppliedFetch,
  logger: suppliedLogger,
  writeCookie: cookie.writeCookie,
});
const Selector = createLanguageSelector({
  ...suppliedReactTranslationRouterSelectPorts,
  catalog,
  changeLanguage: client.changeLanguage,
});
```

Cookie read/header helpers are retained source context, not evidence that the
custom selector bootstraps its provider from cookies. That selector reads the
injected i18n language. The original private Select/provider, server origin,
authorization, current resource availability and translated tenant contents
remain unknown. The relative GET path alone does not establish anonymous access.

## Qualification

Run from `app/` using the existing pinned dependencies:

```sh
node scripts/original-language-switch.mjs
node --test tests/original_language_switch.test.mjs
PUMP_LANGUAGE_OUTPUT=/your/isolated/output node --test tests/original_language_switch_browser.test.mjs
```

The source gate checks exact generated client/contract bytes and complete
retained ASTs against authenticated originals. Node tests exercise actual
loopback GETs, warning/fallback/cache/concurrency behavior, synthetic cookie
attributes/errors, awaited provider/refresh ordering and real React SSR.

The browser fixture uses the actual source component and client with authored
Select/i18n/document/location/router ports and an owned GET-only dictionary
server. It holds fetch/provider promises to observe pending states, exercises
selection/cache/rejection and observes completion after unmount. Its synthetic
provider rejection is an expected uncaught error, not a zero-error or original
tenant-failure claim. Its screenshots depict this explicit fixture, not the
product Settings page or original visual parity.

No real app/tenant request, actual cookie/session/credential access, global UI
language change, new locale backend, signing, network mutation, original private
provider/API/pixel equivalence, security clearance or feature completion is
qualified. Source, runtime/test and receipt revisions remain separately bound.

Frozen source and method `da80fe42e79abe53a817e832201007e75582052a` passed
14 domain tests, 11 shared-source tests and one actual React browser workflow
at 390px and 1280px. Recursive typecheck, 698 evidence checks and nine progress
tests also passed. Each browser width intentionally retains one uncaught
synthetic provider rejection and no other page errors. The [qualification
packet](validation/README.md) binds the selected executed inputs, raw outputs
and screenshots; publication changes no runtime or test method.
