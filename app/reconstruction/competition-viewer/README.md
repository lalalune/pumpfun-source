# Original competition viewer rank card

The captured competition board has an interactive viewer card, separate from
its public participant rows. Before this unit, that complete card and its
expandable statistics were not available as an editable, source-checked React
component. This recovers the actual `590407.e9` card, `e7` statistics, `e8` cells,
`e5` near-zero/null decisions, `te` state updater and the actual board invocation.

The result is a usable component factory for a host that already has a validated
entry. It does not identify a viewer, read a session, create an authenticated
query or implement backend ranking. The maintained page/API/projection and
original captures remain unchanged.

## Source boundary

The producer authenticates all six selected factory variants and every recorded
origin using the unchanged shared source reader. It validates actual imports
and exports, records raw-byte/UTF-16/UTF-8 witnesses, and reproduces maintained
AST and bytes. The full generated card/stat function bodies are also compared
directly against the original AST after removing only TypeScript annotations.
Captured runtime factories are parsed as data and never executed.

The complete caller/planner and `139209` entry/viewer DTO witnesses establish
that the original board passes `detail.viewer.entry` to this card. The original
DTO includes rank zero and struck entries; the adapter does not infer eligibility
or filter those values. Identity routing/image normalization reuse PR1296's
explicit two squad and three image contexts. Its helpers and all five variant
files are pinned as a prerequisite, with attribution preserved. They are not a
new recovery claim. The used SVG wrapper was also already traced there; the two
actual expand/collapse chevrons are bound here.

The original card preserves its supplied PnL, rank-zero `#—`, nullish name and
wallet-shortening behavior, person-only YOU badge and squad label. Expanding
stats mounts `e7`; collapsing or removing the card unmounts it. Realized and
unrealized values with absolute value below 0.005 display neutral zero. The
volume cell uses the original truthiness check and display multiplication of
supplied `buySpendSol` and supplied SOL price. No price, PnL or rank is computed
by a new service.

`90832.v` is an alias through `t.l` to `540805.l`. The complete used formatter
and closure preserve its missing/nonfinite dash, Unicode minus, zero/precision
and compact thresholds. It is not replaced with an approximate currency helper.

The `363250.f` price hook and its actual query function/imports are retained as
source evidence. Its query runtime, key provider and `60326` transport remain
unreconstructed capabilities here. The component calls the injected hook with
the original empty options object only while stats are mounted. A local hook
does not establish original React Query/cache/polling or price-feed behavior.

## Host use

Create once outside React render, in a legitimate client module:

    const { Card, ViewerConsumer, Stats } = createCompetitionViewerComponents({
      squadVariant: reviewedSquadSha256,
      imageVariant: reviewedImageSha256,
      useTranslation: legitimateTranslationHook,
      useSolPrice: legitimatePriceHook,
      Avatar: compatibleAvatar,
      Link: compatibleLink,
    });
    // ViewerConsumer takes { row: { entry } } and executes the captured call.

The host owns validated props and account scoping. Updating an entry in place
preserves the card's expanded state, as the original does; removing/remounting
it resets to collapsed. This UI state is not authorization. Ports are functions
bound in a client module, not function props passed through an RSC boundary.
Avatar, Link/router, translations, provider cache/auth lifecycle and backend
compatibility are not supplied or certified by this unit. The bounded class
join covers only the finite nonconflicting strings used by this card.

## Repeatable local workflow

    node scripts/original-competition-viewer.mjs --check
    node --test tests/original_competition_viewer.test.mjs \
      tests/original_competition_viewer_browser.test.mjs tests/original_source.test.mjs
    pnpm -r typecheck
    python3 scripts/verify-evidence.py

The focused result is 18 passes: six source/helper/schema/SSR checks, one real
React/Chromium workflow across six contexts at desktop/mobile, and eleven shared
source-reader checks. Wrong numeric fixture input is rejected using the retained
public entry schema. The loopback host exercises the captured invocation,
mouse/keyboard expansion, original chevrons, missing/zero/supplied prices,
in-place prop updates, group/person differences, invalid-input clearing and
remount reset. The injected price hook records mount/unmount balance; that is
proof of the card's conditional React lifecycle, not an original query-provider
implementation. No timer behavior is invented.

The host uses visibly synthetic translations and a local placeholder Avatar;
its anchor suppresses activation. All requests are loopback GETs. Browser
cookies and local storage stay empty. Four inspected screenshots show collapsed
and expanded states at 1280x900 and 375x812; they are local component-host
artifacts, not original-reference screenshots or a native page parity claim.

The validation receipt pins exact source/tool/input/image/log hashes. Required
root/common checks are coordinator-owned and will be attached only for their
actual published head. No full Next/browser, universal behavior, security
acceptance or native API compatibility is claimed from these finite tests.
SDK, captures, dependencies, lockfile, global styles, completion counts and
feature ledger are unchanged. Original source retains its upstream authorship;
local module names and types are reconstruction adapters, not recovered TS.
