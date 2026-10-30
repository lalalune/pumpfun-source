# Lane w12a04-cto-k4size (wave 12, pool a)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: land the best unlanded composite, w9r2-admincto-harvest trial **k4** (0.4525 at 27,384 B,
16 B short), by searching size knobs on top of it until it sits at exactly 27,400 B.
Base: main 20a1ae9c0 (programs/ identical on origin/main e61df0357); main admin_cto = h1 (#2642),
27,400 B, ratio 0.43919, slots_diff 3,352. Ledger approach `k4-size-search`, keys
`0x22a10-w12-20a1ae9-k4size-<trial>-v1`.

## k4 on current main

k4 = h1 + `wallet_flags` (#2518: `do_collect`/`do_coin` flags) + `region2_tree` (#2515:
`(sharing_update,collect_old)` as one if-tree) + `fee_unwrap` (`fee.unwrap_or(old_fee)`) +
`canedit_first` (`can_edit_creator_fee=false` with the old reads) + `old_fee_first`.
Ported unchanged (only admin_cto.rs differs from main): **27,384 B, 0.4525**, 154+3 calls,
1033 normalized, raw 347 (686 raw losses from the -16 B size alone).

## Result: k4 + two +8 B knobs = 27,400 B

| knob on k4 | bytes | ratio |
| --- | ---: | ---: |
| (k4) | 27,384 | 0.45250 |
| sweep `let bump=..;let old=..;` (reverts h1's old-before-bump) | 27,392 | 0.45094 |
| **bump-first + `match sharing_update{Some(val)=>{..}None=>{}}`** | **27,400** | **0.45147** |

| metric | main 20a1ae9c0 | this lane | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 | 27,400 |
| ratio | 0.43919 | **0.45147** | 1 |
| slots_diff (positional) | 3,352 | **3,308** | 0 |
| calls | 154+3 | 154+3 | 154+3 |
| normalized / raw | 1033 / 1033 | 1033 / 1033 | 1035 |
| gains / losses | | 0 / 0 (raw 0 / 0) | |
| swap_hop | 0.99913 / 18 | 0.99913 / 18 (unchanged) | |

Unstripped sha256 `784bea21ed580b15791d642573314f778751b461334a4a217edb90013d7cbd7e`.
Runtime: `scripts/pump_admin_cto_differential.py`: 363/363 cases match.

## Reproduction scope

This packet retains the selected source change and its measured result. The
worker-specific search queue, mutation library and scoring wrapper are omitted;
they depended on private worktree paths and were not needed to reproduce the
selected candidate. Build with the maintained `reconstruction/harness/fastbuild.py`
and score with `reconstruction/harness/score.py` against a fresh main build.
