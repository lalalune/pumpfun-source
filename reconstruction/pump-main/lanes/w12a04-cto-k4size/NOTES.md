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

## Step 2: can_edit cleared after the fee store (L2, 0.45177)

On the landed L1 (#2749), moving `curve.can_edit_creator_fee=false;` from the old-value reads back to
after the fee store (the original also clears it last, `stb [r1+0xa4],0` at orig 0x275c8) keeps
27,400 B and raises the ratio 0.45147 -> **0.45177** (slots_diff 3,308 unchanged), 1033/1033, zero
losses, unstripped sha256 `6892c2a15de3ba6a...`.

## Step 3: fee match + per-arm cashback compensation table (measured on L2, superseded by #2831)

Base: main after #2792 (L2) and #2808 (nested pool-authority signer seeds): 27,400 B.
Two validate genes from other wave-12 lanes raise the ratio a lot but leave admin_cto short of
27,400 B: w12a09-cto-cleanroom's `match fee{None=>{},Some(f)=>{..}}` (None successor first; on L1
27,392 B / 0.47551) and w12a11-cto-sibling's AMM-sibling per-arm cashback
(`let cashback=if holder{false}else{st.cashback};`, tested by 330; on L1 27,384 B / 0.48367).
Size compensation from this lane's knob search (measured on L2, before #2808):

| L2 + | bytes | ratio |
| --- | ---: | ---: |
| fee match + cashback local | 27,384 | 0.48517 |
| + old fee read after the cashback store (`curve.is_cashback_coin=cashback;let old_fee=..`) = Y | 27,392 | 0.48599 |
| + old fee read after the creator store instead | 27,384 | 0.48517 |
| Y + event `is_holder_reward:holder,is_cashback_coin:cashback` (evfl) | 27,408 | 0.48465 |
| Y + evfl + `if let Some(f)=fee` fee store | 27,408 | 0.48525 |
| Y + `sharing_config_reset` bound before the seeds | 27,384 | 0.48547 |
| Y + event `is_holder_reward:holder` only | 27,384 | 0.48547 |
| Y + event `is_cashback_coin:cashback` only | 27,408 | 0.48435 |
| Y + evfl + `pool_updated=if ..{cpi?;true}else{msg!;false}` | 27,400 | 0.48472 |
| Y + evfl + `reset` early | 27,400 | 0.48502 |
| Y + evfl + `reset` early + `if let` fee store | 27,400 | 0.48562 |
| Y + evfl + `pool_updated` if-expr + `if let` fee store | 27,408 | 0.48465 |
| Y + evfl + `pool_updated` if-expr + #2808 nested seeds | 27,400 | 0.48562 |
| **Y + evfl + `if let` fee store + #2808 nested seeds with `reset` bound first (this PR)** | **27,400** | **0.48652** |

w12a14-cto-hillclimb-2 (#2831) landed the same family at 0.48742 first; the rows above are kept as a
compensation table for these genes.

## Step 4: old fee read after the cashback store (H3, 0.48772)

On main after #2831 (H2: 27,400 B, 0.48742, slots 3,273), moving `let old_fee=curve.creator_fee_bps;`
from after the holder store to right after the cashback store keeps 27,400 B and raises the ratio to
**0.48772** (slots 3,273), 1034/1034, zero losses, unstripped sha256 `4d9f82e4e97d0c10...`,
differential 363/363.

Single genes on H2 so far (bytes / ratio): `match fee{None=>{},Some(f)=>..}` 27,400 / 0.48742;
holder store before cashback 27,400 / 0.48742; `let reset=sharing_update.is_some();` before the
nested seeds 27,392 / 0.48839 (needs +8 B).

## Knob table (single genes, admin_cto bytes and ratio)

Bases: k4 = 27,384 / 0.4525; L1 = k4 + bump-first + su-match = 27,400 / 0.45147 (main after #2749);
L2 = L1 + can_edit last = 27,400 / 0.45177.

| base | gene | bytes | Δ | ratio |
| --- | --- | ---: | ---: | ---: |
| k4 + bump-first | `if let Some(f)=fee` store instead of `unwrap_or` | 27,384 | -8 | 0.45190 |
| k4 + bump-first | old_creator read before old_fee | 27,392 | 0 | 0.45094 |
| k4 + bump-first | can_edit cleared last | 27,392 | 0 | 0.45124 |
| k4 + bump-first | sweep `frozen` before `amount` | 27,328 | -64 | 0.43768 |
| k4 + bump-first | drop `let mut target=target;` | 27,392 | 0 | 0.45094 |
| k4 + bump-first | sweep gate `(holder&&shared)` | 27,392 | 0 | 0.45094 |
| L1 | can_edit cleared last | 27,400 | 0 | **0.45177** |
| L1 | can_edit cleared right after the creator store | 27,400 | 0 | 0.45147 |
| L2 | `pool_updated` as `if ..{cpi?;true}else{msg!;false}` | 27,392 | -8 | 0.45094 |
| L2 | sweep gate as a phi-of-constants flag from the region-2 tree | 27,392 | -8 | 0.36794 |

Exploration builds use `fastbuild.py` + `target_metric.py` only; 27,400 B hits are rescored with
`score.py` against the current baseline and the 363-case differential before landing.

## Reproduction scope

This packet retains the selected source change and its measured result. The
worker-specific search queue, mutation library and scoring wrapper are omitted;
they depended on private worktree paths and were not needed to reproduce the
selected candidate. Build with the maintained `reconstruction/harness/fastbuild.py`
and score with `reconstruction/harness/score.py` against a fresh main build.
