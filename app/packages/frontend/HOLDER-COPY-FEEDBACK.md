# Holder inspector clipboard feedback

A clipboard write can settle after a mint edit, Clear, or another derivation.
Those actions reset the inspector's feedback, but the previous write used to
replace that reset with its old success or failure message. The stale message
appeared both visually and in the polite live region.

The inspector now captures a generation for each copy operation. Editing,
clearing, deriving or starting a newer copy advances it. Only a completion from
the current generation can update feedback. The browser's clipboard operation
can still finish; the discarded part is feedback for an older inspection.

Three delayed-Promise browser cases cover success after editing, rejection
after Clear, and success after another derivation. The baseline case on main
`60bdd8a7a522921058d18563bb9335d2a06aec75` reproduced an empty live region being
replaced by `Normalized mint copied.` The candidate passed all three new cases
and all eight existing holder-inspector cases:11/11. Four existing SDK
derivation groups and frontend TypeScript also pass.

The first candidate run passed the three new cases and seven existing cases;
the final console check caught a missing tracked font in the sparse checkout.
Restoring the exact Git-authenticated font bytes fixed that setup issue, and
the same source/tests passed the full11-case retry. Both failed runs and the
successful retry are retained in `visual/holder-copy-order-20261029/`.

From app:

```sh
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/holder-copy-order.spec.ts tests/holder-rewards.spec.ts --max-failures=1
node --test tests/holder-rewards.test.mjs
pnpm --filter @pump-reconstruction/frontend exec tsc --noEmit --incremental false
```

The change is local feedback handling. It adds no new SDK recovery, rewards
calculation, API compatibility or visual-equivalence claim. Feature milestone
counts do not increase.
