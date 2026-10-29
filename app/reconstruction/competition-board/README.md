# Original competition-board coordinator

The recovered competition hooks, participant row, viewer card and prize display
were independent components. Their complete captured coordinator was missing.
This reconstructs the full `590407.to` function and both actual person/group
call sites, making the original data selection, row planning and component
dispatch editable and composable. It uses ordinary array mapping; no virtualized
table is inferred.

## Original boundary

The producer authenticates seven selected factory variants and all their
origins. It verifies actual query/selection/provider import edges, exact raw
byte/UTF-16/UTF-8 witnesses and generated AST/bytes. Full `to/tc/tu/tm` bodies
are independently compared with the original after TypeScript annotations are
removed. Complete `T` section headings, `O` paid-rank boundary, `K` pending
display and the used `706615.V` reducer are preserved. Captured runtime factories
remain inert.

The actual person/group JSX invocations preserve their different control
placement classes. The coordinator:

- Reads the list with `isVisible:true`, chooses its first matching live/upcoming/
  past competition through the accepted selector, and passes its ID or literal
  null to the detail hook. A detail competition takes precedence over the list.
- Plans highlights when entries exist, pending content for a live empty detail,
  and a supplied viewer row only when standings or prize tiers exist. It does
  not identify or authenticate that viewer.
- Preserves standings versus final headings, original entry order, rank-prize
  lookup and paid-rank line placement. Empty standings display supplied prize
  tiers. Nothing is ranked, priced, filtered for eligibility or repaired here.
- Passes only a finite increasing parsed date window to highlights; invalid,
  missing or reversed bounds become null. Opens/closes rules through the
  original local React state and forwards list refetch to the hero retry port.
- Retains original loading/error/retained-data decisions, even where a detail
  error does not add a new global fallback. No new cache or error policy is
  invented.

Original authorship is retained. Module names and types are local adapters,
not recovered private TypeScript sources.

## Composition and dependencies

`createCompetitionBoardComponents` binds real React/compiler/JSX and composes:

- PR1296's complete participant row and explicit identity/image contexts.
- PR1315's complete viewer card and optional stats with an injected price hook.
- Accepted PR937's complete prize tier/formatters and rank-prize lookup.
- Accepted PR850's list/detail hooks, bucket selector and foreground modules
  when supplied as the client capability.

These prerequisites are reused and credited, not claimed as new recovery.
Open prerequisites are explicit in the PR; their source and receipts remain
unchanged. Create the factory once outside render in a legitimate client module:

    const { PersonConsumer, GroupConsumer, Board } = createCompetitionBoardComponents({
      squadVariant, imageVariant, numberVariant,
      useTranslation, useSolPrice, useReducedMotion,
      Avatar, Link, client,
      Hero, Highlights, Rules, Card,
    });

All three source-context hashes are explicit. `client` has the recovered
useList/useDetail/selectCompetition interface. Hero media, highlights content,
rules dialog internals, motion-card behavior, query runtime/cache, translations,
Avatar/Link, viewer/contract providers and price are compatible injected ports.
Their complete implementations or upstream parity are not certified here.
The two original motion-card contexts are recorded without guessing a global
winner. Bound functions belong in a client module, not serialized RSC props.

No native page/API/projection, server auth, registration, terms mutation,
financial calculation, SDK, capture, dependency, lockfile, global style,
feature ledger or completion-count change is made.

## Finite workflow proof

    node scripts/original-competition-board.mjs --check
    node --test tests/original_competition_board.test.mjs \
      tests/original_competition_board_browser.test.mjs tests/original_source.test.mjs
    pnpm -r typecheck
    python3 scripts/verify-evidence.py

The focused suite has 18 passes: six source/SSR checks, one real React/Chromium
workflow, and eleven shared-source checks. SSR composes the actual recovered
row/viewer/prize components across all six identity/image and both NumberFormat
contexts. It verifies ordering, disabled detail, loading/error forwarding,
pending/prize/final branches, reduced-motion class choice, date bounds and
immutable supplied inputs. Negative source and receipt edits fail verification.

The browser executes the actual accepted list/detail hooks and foreground
modules, their real queryFns and local GET transport, original bucket selector,
full coordinator, actual caller wrappers and real recovered child components.
The local query port runs one abortable request per supplied key; it records
stale/refetch options but does not implement original query-cache/polling/retry
policy. The server serves explicit synthetic DTO-shaped inputs under a loopback
fixture prefix. It does not emulate private backend ranking, auth or eligibility.

Twelve desktop/mobile context runs cover six identity/image contexts, alternating
both explicit NumberFormat and foreground variants. A held detail request
observes prize-only intermediate output before standings arrive. Additional
failure/retry, pending, empty, final and in-flight cancellation cases preserve
the source decisions. The held loopback response closes after the local query
port aborts on unmount; this does not establish original query-runtime policy.
Rules callbacks, group/person consumer changes, query abort and original
foreground-subscription cleanup are exercised. Cookies and local storage remain
empty; requests are GETs to the loopback origin with the recovered WEB headers.

Hero/highlights/rules/motion/Avatar/translation are visibly local host ports.
Inspected desktop/mobile PNGs demonstrate composition and responsive fit, not
original-reference visuals, media behavior, whole Next/browser operation,
native API compatibility, universal behavior or security acceptance. Exact
source/tool/input/log/image hashes are retained in the validation receipt.
