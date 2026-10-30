# Lane w9r2-admincto-harvest (wave 9, round 2)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`). Angle: harvest every
swarm PR/branch that touched admin_cto.rs, rebuild on latest main, combine compatible edits.
Base: origin/main 2abb99ccb (1033/1033, admin_cto 27,400 B, ratio 0.36010, slots_diff 3,297).
Builds: `~/.cache/pumpfun-reconstruction/lanes/w9r2-admincto-harvest/` (not in git).
Ledger approach `harvest-combine`, keys `0x22a10-main-2abb99c-<trial>-v1`.

## Harvested sources

| source | edit | on main 2abb99c |
| --- | --- | --- |
| #2622 w10r1-admincto-state | can_edit first, fee unwrap_or, pool empty-first | 27,400 / 0.36129 (their PR) |
| #2621 w10r1-admincto-stitch | is_holder_reward before creator | 27,400 / 0.36099 (their PR) |
| branch x1-cto-sweep-exit-nonconst-tag (g), no PR | sweep native arm returns `transfer_native(..).map(\|()\|amount)` + gate `(shared&&holder).then(..).transpose()?.unwrap_or(0)` | **27,416 / 0.43816** (g0) |
| branch y1-cto-spill | sweep `old` before `bump`; token arm `frozen` before `amount`; old_fee first | size knobs below |
| #2564, #2528, #2515, #2518, #2550 (closed) | alternatives to #2524's size fix | not stacked (each moves size off 27,400 on #2524) |

x1 (g) moves the 784-insn sweep tail before the post-sweep join as in the original, but on top of #2524
it overshoots by 16 B. Size knobs measured on the g0 base:

| trial | g0 + | bytes | ratio |
| --- | --- | ---: | ---: |
| g1 | pool empty-first | 27,416 | 0.43756 |
| g2 | collect_old `!shared` | 27,408 | 0.43762 |
| g3 | frozen before amount | 27,392 | 0.43416 |
| g4 | quote_locked before shared | 27,536 | 0.42492 |
| g5 | old before bump | 27,408 | 0.43972 |
| **h1** | **collect_old `!shared` + old before bump** | **27,400** | **0.43919** |
| h2 | frozen first + can_edit first | 27,400 | 0.43619 |
| h3 | frozen first + old_fee first | 27,400 | 0.43649 |
| h4 | frozen first + old before bump | 27,392 | 0.43476 |

## Result (h1)

| metric | main 2abb99ccb | h1 | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 | 27,400 |
| ratio | 0.36010 | **0.43919** | 1 |
| slots_diff (positional) | 3,297 | 3,352 | 0 |
| calls | 154+3 | 154+3 | 154+3 |
| normalized / raw | 1033 / 1033 | 1033 / 1033 | 1035 |
| gains / losses | | 0 / 0 (raw 0 / 0) | |

slots_diff is positional and ~96% of slots differ in both (the frame offsets differ from the first
instruction: arg spills `[r10-0x928]` etc. vs ours `[r10-0x8f0]`), so it is dominated by stack-slot
offsets; the ratio gain is the sweep tail moving to its original place.
Runtime: `scripts/pump_admin_cto_differential.py --candidate h1/candidate.so`: 363/363 cases match.
