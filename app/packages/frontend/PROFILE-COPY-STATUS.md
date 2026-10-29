# Profile clipboard feedback ordering

## Reproduced defect

On main `e38a8b97a18d33417e364487eb69f8ed74aff19e`,
`src/components/profile/CopyAddressButton.tsx` blob
`4c80e6c1867c8da423b6c4f818945417c3586d37` awaits each clipboard write and then
unconditionally replaces its feedback. Consequently an older failed write can
replace a newer success (and vice versa). Starting another write also leaves
old success feedback visible while the new attempt is pending.

This is a defect in the maintained local UI, not a reconstruction of unseen
original clipboard behavior. Merged PR826 changes whether a walletless profile
renders this component, but does not change the component itself. This correction remains limited to profile copy feedback; holder-rewards and
other clipboard controls are not changed here.

## Change

Each invocation increments a component-local request counter and clears prior
feedback. Only the newest request may report success/failure. Results carry the
address they describe, and the render projection hides an outcome for another
address. The address passed to `writeText` is unchanged and no pending operating-system
write is claimed to be cancelled. The latest requested write remains authoritative
for feedback even if writes finish in a different order. The counter advances
only on a copy attempt, not on prop changes. Returning from address A to B to A
without another attempt may reveal the retained A outcome; this change does not
claim address-change invalidation or cancellation on navigation/unmount.

There is no SDK, chain, wallet connection, signing, network, source capture,
backend, dependency, feature-milestone or layout change. Existing labels and
failure text are retained.

## Verification and limits

`node --test tests/profile_copy_status.test.mjs` is automatically included in
the existing root `node --test tests/*.test.mjs` stage. The three callback cases
were run against the exact unchanged source first: all three failed with the
wrong final/current status. The same cases pass after the change. A fourth
case checks the maintained address-bound status expression.

The test uses Babel to select only the maintained callback and projection, then
executes them with synthetic clipboard/status ports and deferred promises. It
does not execute captured bundles, a real clipboard, React hooks, DOM mounting,
unmounting, navigation or prop updates. It is direct deterministic callback
control-flow proof, **not browser/component-lifecycle runtime coverage**.

`tests/profile-copy-race.spec.ts` authors a product regression for out-of-order
completion, pending feedback and navigation/unmount, but remains **unrun** due
to the known cloud browser restrictions. No browser launch or sandbox workaround
was attempted.

## Current-source validation

The four-file change was refreshed against main
`60bdd8a7a522921058d18563bb9335d2a06aec75` (app tree
`e3d6d8cd07df4f561a4fd058dad29d22de451bfc`). The component preimage remains the
same `4c80e6c1…` blob and the three new paths are absent. Component and test bytes
are unchanged from the separately reviewed original packet; this note alone was
updated for current status and supplemental checks.

An isolated private harness also exercised the actual maintained component with
React 19.2.3 StrictMode and jsdom 26.1.0: **11/11 controls pass**. The same controls
against the original component give seven failures and four passes. They cover
all overlapping success/failure combinations, clearing feedback on another
attempt, settled/pending address replacement, a newer address attempt, and late
completion after unmount followed by a fresh instance. The unmount controls
already pass on the original; they are preservation checks, not new fixes.

Clipboard promises are synthetic and jsdom supplies no browser resources. These
checks execute React props, refs, state and events, not the operating-system
clipboard, permissions, actual Next navigation, hydration or visual layout.
Browser, permission and visual-parity qualification remain open. No compatibility
milestone changes are made.

On that current source composition, the four published callback/projection tests,
25 existing profile/graph/search adapter tests, full SDK/backend/Next production
build, all three workspace typechecks (including the authored browser test), and
app evidence verification pass. The evidence check authenticates 698 retained
objects, npm integrity and unchanged SDK source; it does not execute the captures.
Mandatory root checks independently pass for nine static captures and six
synthetic byte-comparator cases on the same pinned root inputs.

The complete aggregate test command and its browser posttest were not run; the
known cloud browser and tsx-CLI IPC limits were not bypassed. Actual React checks
remain supplemental private evidence, not another checked-in test dependency or
an accepted compatibility milestone.
