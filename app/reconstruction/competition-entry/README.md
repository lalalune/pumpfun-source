# Original competition participant row

The maintained competition view uses a locally designed row. Before this unit,
the complete captured participant row was not an editable, source-checked React
component. This recovers that missing display boundary: the full 590407.X body,
its actual JSX invocation, original verified badge/crown SVGs and all used
identity, image-normalization and supplied-PnL display helpers.

The existing page, API and projection remain unchanged. The current projection
omits profileImageUrl, which the original row consumes. Supplying a fabricated
image or silently changing that projection would not qualify an original page
integration. Instead, the component factory accepts the documented entry shape
and explicit host providers and is exercised by its actual captured invocation.

## Complete source boundary

The generator authenticates 17 selected factory variants and every recorded
origin through the unchanged shared original-source reader. It verifies actual
import IDs and exports, preserves complete function bodies, and regenerates the
maintained AST and exact bytes. The contract includes raw-capture hashes,
UTF-16/UTF-8 witnesses, the complete original row planner, actual X invocation,
139209 entry DTO/shared profile fields, provider edges and emitted file hashes.
Captured bundles, runtime factories and route-schema code are parsed as data,
never imported or executed.

The recovered row preserves:

- Person versus group profile links, avatar arguments, secondary wallet/member
  text, nullish username fallback and an intentionally preserved empty username.
- Supplied rank zero as a dash, original top-three palette/crowns and the exact
  verification display predicate. Verification is a UI hint, never authorization.
- Supplied positive/zero/negative PnL formatting and color; no PnL calculation,
  pricing, rank assignment or membership calculation.
- The optional raw-text prize badge inside the complete row. Accepted PR937's
  prior prize/706615 tracing is credited; no duplicate prize recovery count.

Used complete helpers are 146695.$ profile href, 365089.d short wallet,
599432.f verification hint, 90832.w display formatting, both 69399 squad-route
closures and all three 741084 image-normalization variants. The 426091 image
sentinel and 897665 prefix are exact used constants. The 179537 palette literal
is identical across both reviewed variants; no whole-factory winner is inferred.
Original 98525 badge and 745018 crown/SVG-wrapper bodies remain intact.

Both squad contexts and all three image contexts are retained independently.
The caller must supply full reviewed hashes; no global active variant is guessed.
Original material retains its authorship. Local file names and TypeScript
interfaces are analyst adapters, not recovered upstream TS sources.

## Usable host interface

Create the components once in a legitimate client module, outside React render:

    const { Row, EntryConsumer } = createCompetitionEntryComponents({
      squadVariant: reviewedSquadSha256,
      imageVariant: reviewedImageSha256,
      useTranslation: legitimateTranslationHook,
      Link: compatibleLinkComponent,
      Avatar: compatibleAvatarComponent,
    });
    // EntryConsumer receives { row: { entry, prize } }.

EntryConsumer executes the actual captured JSX expression that calls X with
entry and prize. It is not the complete original board/dispatch
provider. The host supplies validated entry values and an already selected
prize. The generator retains the actual original planner as source evidence but
does not implement a new ranking/selection policy.

The facade binds real React JSX/compiler/createElement capabilities. Translation,
Avatar and Link are explicit ports. Original Avatar fallback/identicon/CDN
behavior, Next Link/router scheduling and provider/auth/cache lifecycle remain
unreconstructed here. The local class join covers only this row's finite,
nonconflicting strings; it is not the complete original class-merge library.
Heterogeneous compiler cache slots use any[]; public props are typed. No
ts-nocheck, captured-factory execution, new dependencies or source-library edits.

## Rendering and actual consumer proof

The loopback host admits complete synthetic entry objects using the retained
public OpenAPI entry schema and the existing generic validator. It then passes
the objects unchanged through the real component factory and captured JSX
consumer. The host's translation labels are visibly synthetic. Its Link is a
local anchor with activation suppressed; Avatar records the provided props and
renders a local placeholder. These capabilities qualify argument binding and
row behavior, not navigation destinations or image-provider parity.

The browser workflow runs all six explicit source-context combinations at
1280x900 desktop and375x812 mobile. It checks person/group href encoding and
reserved-name fallback, rank0, all three crowns, strict badge visibility, raw
prize text, Avatar arguments, schema rejection and clearing. Updating supplied
username/PnL/image/badge props exercises the original compiler-cache decisions.
Rows fit without horizontal overflow. SSR also checks HTML escaping and input
immutability, including all six contexts.

Four inspected [local screenshots](visual/README.md) show the initial supplied
state. They are not authenticated original-reference screenshots or evidence
that the maintained page changed. The result is an editable, usable original
row component; original whole-page visual parity, full Next/browser behavior and
API compatibility remain unqualified.

    node scripts/original-competition-entry.mjs --check
    node --test tests/original_competition_entry.test.mjs \
      tests/original_competition_entry_browser.test.mjs tests/original_source.test.mjs
    pnpm typecheck
    pnpm verify:evidence

The focused result is23 passes: eleven source/helper/schema-admission/SSR
checks, one actual React/Chromium workflow across12 source-context/viewport
combinations, and eleven unchanged shared-source checks. Validation receipts
pin the exact tested source, tools, inputs, raw logs and images. Full app/root
gates are coordinator-owned and remain explicitly pending until qualified for
the published head.

No live profile, account, cookie, credential, wallet operation, production
request or financial mutation is used. All browser requests are loopback GETs.
Backend/API/types/page, captures, SDK, lockfile, feature ledger and completion
counts are unchanged. Finite local proof does not establish universal behavior,
private backend logic, native compatibility or security acceptance.
