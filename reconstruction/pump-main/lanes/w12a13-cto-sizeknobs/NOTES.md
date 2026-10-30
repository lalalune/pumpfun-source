# Lane w12a13-cto-sizeknobs (wave 12, pool a)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: a size-compensation catalog. Small, ordinary, semantics-preserving single edits to `admin_cto.rs`,
each measured alone with the identity recipe (`measure.sh`): byte delta, ratio delta, losses and the
entry spill offset (frame proxy). Composites that gain ratio but miss 27,400 B by 8-56 B can pick
compensators from it.

Machine-readable catalog: `pump-main-swarm/w11/sizeknobs-cto.json` (copy: `sizeknobs-cto.json` here).
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w12a13-cto-sizeknobs/` (not in git).
Ledger approach `size-knob-catalog`, keys `0x22a10-w12-20a1ae9-sizeknob-<base>-<knob>-v1`.

## Bases

| base | admin_cto.rs | bytes | ratio | first spill |
| --- | --- | ---: | ---: | ---: |
| `main` | main 20a1ae9c0 (= h1, #2642) | 27,400 | 0.43919 | `[r10-0x8f0]` |
| `j3` | main + `wallet_flags` (#2518) | 27,312 | 0.45251 | |
| `k4` | main + wallet_flags, region2_tree, fee_unwrap, canedit_first, old_fee_first (w9r2 k4) | 27,384 | 0.4525 | `[r10-0x8f0]` |
| `L1` | k4 + `s_bump_first` + `p_share_match` (= PR #2749, w12a04-cto-k4size) | 27,400 | 0.45147 | `[r10-0x8f0]` |
| original | | 27,400 | 1 | `[r10-0x928]` |

## How to use

- `tools/knobs.py` holds every knob as exact `(old, new)` substitutions, `tools/genes.py` the bases.
  `tools/trial.py <name> <base> <work_idx> <knob>...` builds one variant through `measure.sh` and refuses any
  edit that changes the line count or moves an `error!`/`require!`/`msg!` site off its line (line!() values are code).
- Byte deltas are **not additive** (x1-integrator: sweep knobs b=-16 and e=+16 composed to g=+16, not 0).
  Pick candidates from the table, then measure the combination.
- `=` means the build is byte-identical to its base (the knob does not change codegen).
- `tools/cdiff.py a.so b.so` diffs two candidate builds of `admin_cto::execute` (what a knob really changed);
  `tools/jumpmap.py cand.so` aligns against the original with jump offsets masked and shows where inserting
  k slots would fix or break aligned jumps; `tools/frame.py` prints the entry spill offset.

## Catalog (measured here unless noted)

| knob | category | main Δbytes | main Δratio | L1 Δbytes | L1 Δratio | k4 Δbytes | k4 Δratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `s_old_borrow` | copied-vs-borrowed Pubkey | -80 | -0.00295 |  |  |  |  |
| `g_old_fee_first` | statement / evaluation order | +48 | +0.00080 |  |  |  |  |
| `st_ql_first` | statement / evaluation order | = |  |  |  |  |  |

| prior knob on main (ledger; admin_cto.rs identical to main 20a1ae9c0) | Δbytes | ratio | Δratio | source |
| --- | ---: | ---: | ---: | --- |
| genes.G wallet_flags (#2518 do_collect/do_coin) | -88 | 0.45251 | +0.01332 | w9r2-admincto-harvest j3 (re-measured here) |
| sharing_update/collect_old as one if-tree (#2515) | +16 | 0.43995 | +0.00076 | w9r2-admincto-harvest j5 |
| curve.creator_fee_bps=fee.unwrap_or(old_fee) | +8 | 0.43822 | -0.00097 | w9r2-admincto-sibling h4 |
| curve.can_edit_creator_fee=false right after the old reads | +48 | 0.43969 | +0.00050 | w9r2-admincto-sibling h3 |
| pool_updated tests !data_is_empty() first | +0 | 0.43859 | -0.00060 | w9r2-admincto-harvest i4 |
| is_holder_reward stored before creator (#2621) | +0 | 0.43919 | +0.00000 | w9r2-admincto-harvest i1 (same ratio/slots) |
| cashback computed at the curve store (!holder&&cashback) | -104 | 0.30977 | -0.12942 | w9r2-admincto-harvest j1 |
| sharing CPI CpiContext::new(..).with_signer(..) | +24 | 0.40844 | -0.03075 | w9r2-admincto-harvest j2 |
| validate returns st.creator when shared (#2564) | -24 | 0.28893 | -0.15026 | w9r2-admincto-harvest j4 |
| holder.unwrap_or(false) + cashback with & (#2550) | -184 | 0.4371 | -0.00209 | w9r2-admincto-harvest j6 |
| if !(f>0&&f<=st.max_fee) (pump-amm sibling spelling) | +0 | 0.43919 | +0.00000 | w9r2-admincto-sibling v3 (byte-identical) |
| sweep native arm: let rent=Rent::get()?;let min=rent.minimum_balance(0); | +16 | 0.43816 | -0.00103 | w12a11-cto-sibling sib-rent-local |
| sharing CPI with_signer (re-measured) | +24 | 0.40844 | -0.03075 | w12b12-cto-cpi cpi-sws |
| signer seeds as inline literal in both signed CPIs (no pb/poolseeds/signer_seeds locals) | +184 | 0.39982 | -0.03937 | w12b12-cto-cpi seedsinline |

| prior knob on k4 (ledger) | Δbytes | ratio | Δratio | source |
| --- | ---: | ---: | ---: | --- |
| sweep native arm named Rent local | -32 | 0.45217 | -0.00033 | w12a11-cto-sibling sib-k4-rent-local |
| sweep binds bump before old (l1) | +8 | 0.45094 | -0.00156 | w9r2-admincto-harvest l1 |
| curve.creator stored after is_holder_reward (l2) | -48 | 0.45231 | -0.00019 | w9r2-admincto-harvest l2 |
| pool_updated tests !data_is_empty() first (l3) | -8 | 0.45197 | -0.00053 | w9r2-admincto-harvest l3 |
| k4 without region2_tree (l4) | -16 | 0.45174 | -0.00076 | w9r2-admincto-harvest l4 |

| w12a04-cto-k4size knob on k4+s_bump_first (27,392 / 0.45094) | Δbytes | ratio | Δratio |
| --- | ---: | ---: | ---: |
| `gate_rev` | +0 | 0.45094 | +0.00000 |
| `p_canedit_revert` | +0 | 0.45124 | +0.00030 |
| `p_feeunwrap_revert` | -8 | 0.4519 | +0.00096 |
| `p_oldfee_revert` | +0 | 0.45094 | +0.00000 |
| `p_su_match` | +8 | 0.45147 | +0.00053 |
| `s_frozen_first` | -64 | 0.43768 | -0.01326 |
| `target_rebind_drop` | +0 | 0.45094 | +0.00000 |

## Findings so far

- Knobs that only reorder side-effect-free reads (`st_ql_first`: `quote_locked` first in the `CtoState` literal) are
  byte-identical: LLVM reorders them freely. Reorders across a call or syscall (`Clock::get()?`, CPIs, memcmp) and
  changes of control shape (`?` vs `match`, split checks, `match` vs `if let`) are the ones that move bytes.
- No knob so far moves the entry spill (`[r10-0x8f0]`, original `[r10-0x928]`): the 56 B frame gap is not a
  size-knob effect (frame lanes: w12a01/w12a05).
- From the k4+s_bump_first rows: reverting `fee_unwrap` (-8 B, +0.00096) and `canedit_first` (0 B, +0.00030) both move
  the curve-store block toward the original. The original stores, in order: creator (4 words), is_cashback_coin (+0xa5),
  is_holder_reward (+0xa3), a branchy `if let Some(f)=fee` store to creator_fee_bps (+0x70), and can_edit (+0xa4) last.
  A +8 B knob with a ratio gain on L1 is therefore the missing piece for an L1-family composite at 27,400 B.
