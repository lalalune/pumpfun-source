# w18a06-shim-raforce: event reads in the original's order, curve pointer held across the tail

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. See the PR body for the metrics. Tools and the force table are on
`origin/swarm/w18a06-shim-raforce`.

- The event literal now reads `is_holder_reward` and `creator_fee_bps` after `Clock::get` in the original's order, so it gains
  `ldxdw r4,[r3+0x70]`, `ldxb r5,[r3+0xa5]` and their stores.
- `nf` used to hold r9 from the pool gate to the event. With r9 free, the pool_updated flag takes r9 instead of evicting old_fee
  from r6, the arm's accounts reload loses r6 and the sweep layout collapses. `cvk` (marked shim) keeps a long range in r9: the
  curve box pointer, read at the gate head and last used at the event, at the size of the removed reads.

## Placeholder move (after #4151)

The holder_key byte placeholder before ensure_rent_exempt (line 664) moves to the end of the event CPI. The size stays the same, and every far jump that spans the
stretch between the two points regains the original's displacement. Priced by moving each placeholder over the tail's block heads (IR screen, 260 cells).
