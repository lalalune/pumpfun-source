# x2-cto-rent-local-24b-frame (round 2)

Base: origin/swarm/x1-integrator 678c7ea0b (= main c8dcbbcf7 + notes), fresh build sha 89f8069932c2.
Scored against the shared 1852a872e baseline and against the base build.

Change (sweep, native arm of `admin_cto`):

    - let min=Rent::get()?.minimum_balance(0);
    + let rent=Rent::get()?;let min=rent.minimum_balance(0);

The `Rent` value is now a named binding whose scope covers `ensure_rent_exempt` and
`transfer_native`. Same line count, so no line!() immediates move.

| build | admin_cto 0x22a10 | size | slots diff | normalized/raw vs shared | losses vs shared / vs base |
|---|---|---|---|---|---|
| base | 0.3601 | 27,400 | 3297 | 1033 / 1033 | 0 / 0 |
| **v1 (committed)** | **0.40893** | 27,400 | 3295 | 1033 / 1033 | 0 / 0 |

0x1e7c0 (1.0) and 0x5b3b0 (0.98907, 127 slots) are unchanged. Candidate sha 2cd138343b.

Variants (all recorded in the ledger, keys `0x22a10-x1int-678c7ea0b-rent-*`):

- v2: minimum_balance inlined into the saturating_sub argument: 0.40893 (different sha, same ratio).
- v3: `let rent=&Rent::get()?`: byte-identical to v1.
- v4: lamports read before the Rent local: 0.40893, 3296 slots.
- v7 (control): `let min={let rent=Rent::get()?;rent.minimum_balance(0)};`: byte-identical to base.
  The gain therefore comes from the Rent binding's scope spanning the CPIs, not from naming it.
- v6: `Option<Rent>` hoisted before the vault seeds: 27,632 B, 0.35621 (worse).

The prologue spill slots and the 0x20 local shift (orig [-0x6c0] vs ours [-0x6a0]) are not fixed by
this change. The gain is in original offsets 0x2000-0x3800 (orig-only slots 2137 -> 1974), with a smaller
regression at 0x5000-0x5800.
