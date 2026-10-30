# w13a36-cto-tailregs: register and spill-slot residual in the admin_cto tail

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: register and spill-slot choices in the tail, window-relative orig `0x4c00-0x6b08` (post-sharing join,
`admin_cto_pool` CPI, `AdminCtoEvent` emit/emit_cpi, the sweep native/token tails and `wallet`).
Bases: main dfc3693d8 (0.59916, 3,313 slots) and, after it landed, main cf458a840 / baseline 16c10e631 (0.62043,
3,306 slots; it already carries `is_holder_reward: a.bonding_curve.is_holder_reward` in the event).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a36-cto-tailregs/` (not in git).
Ledger keys: `0x22a10-w13-dfc3693-tailregs-*` (and `0x22a10-w13-16c10e6-tailregs-*`).

No source change is proposed by this PR. It holds the tail register map, the remap bounds and the tools.

## 1. How big the tail register residual is (remap bounds)

`tools/tail.py` aligns original and candidate tokens (scorer tokens: relocated lddw and calls masked) and counts the
original tail tokens that are matched plain, with registers masked (`reg`) and with frame offsets + registers masked
(`fr`). `tools/bound.py <so|fn.bin> [lo hi]` rewrites every candidate token that aligns (reg- or frame+reg-masked) with
an original token in `[lo,hi)` to that original token and re-scores the plain ratio: the ratio a perfect register
(R) or register+frame (FR) assignment in that range would give, with the code shape unchanged.
`tools/bound2.py` does the same for spill slots only (r10 offsets at or below -0x8d0).

| main | range | tail tokens | plain | reg | fr | ratio | R-bound | FR-bound |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dfc3693 | 0x4c00-0x6b08 | 970 | 739 | 857 | 948 | 0.59916 | 0.63451 | 0.66177 |
| dfc3693 | 0x4c00-0x5100 (pool CPI, event) | | | | | | 0.60665 | 0.60905 |
| dfc3693 | 0x5100-0x6b08 (emit_cpi, sweep, wallet) | | | | | | 0.62702 | 0.65189 |
| dfc3693 | whole window | 3,339 | 2,000 | 2,357 | | | 0.70611 | 0.84302 |
| 16c10e6 | 0x4c00-0x6b08 | 970 | 740 | 858 | 948 | 0.62043 | 0.65578 | 0.68274 |
| 16c10e6 | 0x4c00-0x5100 | | | | | | 0.62792 | 0.63002 |
| 16c10e6 | 0x5100-0x6b08 | | | | | | 0.64829 | 0.67316 |

Per 0x400 of the late tail on dfc3693 the R-bound is +0.0012 (0x5100), +0.0042 (0x5500), +0.0063 (0x5900),
+0.0066 (0x5d00), +0.0048 (0x6100): the residual is spread, not one hot spot. Spill slots alone in the tail are worth
+0.010 (0.60935); spill slots + registers +0.047 (0.6459). The pool-CPI/event part the angle started from is the
small part (+0.0075 R); most of the tail's register residual is in the emit_cpi expansion, the sweep and `wallet`.

## 2. Tail value map (dfc3693; orig vs ours)

From `tools/side.py orig.dis cand.dis 4a80 6b08` (side by side, registers/frame/jumps masked for alignment) and
`tools/regperm.py` (orig->cand register pairs per 0x200 segment).

| value | original | ours |
| --- | --- | --- |
| `ctx.accounts` pointer | spill `[r10-0x8d8]`, reloaded into r6 for the pool-CPI clones (orig 0x4c50), r6 for the event (0x4f38) | spill `[r10-0x8e8]`, reloaded into r7 / r8 |
| pool-CPI clone destination (`r10-0x450`) | r7 | r6 |
| `pool_updated` | r8 (`mov r8,0` msg arm, `mov r8,1` after CPI) | r6 |
| `sharing_update` tag (event `sharing_config_reset`) | `[r10-0x8f8]`, reloaded into r6 **before** the pool CPI (0x4d48) and kept across it | `[r10-0x900]`, reloaded into r3 after the CPI |
| holder for the curve store | phi slot `[r10-0x950]` (writers 0xe40/0x1130/0x14e0/0x1830/0x18b0, three constant 0, one 1) | re-derived from the `hopt` byte `[r10-0x8e0]` with `and 0xff; mov r9,1; jne; mov r9,0` (CodeGenPrepare sinks the `icmp`) |
| holder stored first | `is_holder_reward` (0xa5) then `is_cashback_coin` (0xa3) | cashback first; IR store-order swap alone is ratio-neutral (e2) |
| cashback for the curve store | phi slot `[r10-0x958]` `& 1` | `st.cashback [r10-0x908] & !holder [r10-0x8f8]` |
| pool-CPI holder arg | `[r10-0x950]` -> r4 | curve `+0xa5` -> r4 |
| pool-CPI fee (stack args) | `[r10-0x8e8]`, `[r10-0x930]` (not the entry spills `0x928`/r6: a re-defined Option) | entry spills `[r10-0x910]`, `[r10-0x928]` |
| `swept` | r9 from the sweep exits through both CPIs to the event store (orig 0x5030) | spill `[r10-0x968]` |
| `old_fee` | spill `[r10-0x8e0]` | spill `[r10-0x8d8]` |
| emit_cpi `authority_bump` / `&authority_info` | r6 / spill `[r10-0x8d8]` | spill `[r10-0x8d8]` / r6 (w13a19's lane) |
| sweep `amm_frozen` | r8 | spill `[r10-0x920]` |
| sweep `coin_creator_vault_ata.data_is_empty()` | spill `[r10-0x918]` | r8 |
| sweep native memcmp | r9 | r7 |
| global Err-exit payload (`{tag,payload}` -> sret) | **r9** (20 sites `ldxdw r9,[..]; ldxdw r7,[..]; ja exit`; exit `ldxdw r4,[r10-0x8f0]; stxdw [r4+8],r9`) | **r8** (20 sites; exit uses r1) |

## 3. Mechanisms found

### 3a. `swept` and the Err payload share r9 in the original

The sweep returns `Result<u64>` as `{tag, value}`: `value` is the swept amount on Ok and the Error pointer on Err.
In the original the sweep-result value, `swept` and the function-wide Err payload are one register (r9):
- the skip path writes `mov r9,0; mov r7,2` (orig 0x2148 and 0x5e70) and joins the sweep result **before** the
  `jne r7,2` test (orig 0x3c40-0x3c60 loads `r9,[0x828]; r7,[0x830]`, plus the holder phi `r1,[0x950]` and the
  skip/sharing flag `r6,[0x8f8]`, then tests the tag);
- `swept` then stays in r9 through the tail (it interferes with r6-r8 there: accounts/tag, clone dest/CPI tag,
  `pool_updated`), so the coalesced payload class lands on r9 at every Err site.

Ours threads the skip path past the tag test (`swept = phi [0, skip], [value, sweep.exit]` after the test). `swept` is
a separate vreg that is spilled at `0x968`, and the payload phi gets r8.

- IR probe e9 (event stores 0, so `swept` is dead after the sweep): the payload register moves r8 -> **r6**.
  `swept`'s live range is what pushes the payload class up the callee-saved order; it needs one more interference
  (the coalesced `swept`) to reach r9.
- Payload r8 -> r9 alone (`tools/payload.py`, rewriting the 20 Err-site loads and the exit store) is worth +0.0030
  (0.59916 -> 0.60216); the rest of the r9 gain is the tail registers it frees.
- IR e11 (skip path joins `{2,0}` into the sweep Result before the tag test, exactly the original's join) collapses
  to 0.4785 at 27,192 B: block placement re-lays the post-sweep chunk (the w13a27/w13a31 MBP mechanism). The
  payload stays r8 there. Earlier source forms (`if skip{Ok(0)}else{sweep()}?`, `match skip{..}?`) are byte-identical
  to main because JumpThreading threads the constant tag (ledger `w13a08`, `w13a09`).

### 3b. holder as a phi of constants (orig `0x950`)

Our holder is `icmp ne (and hopt,-3), 0`. CodeGenPrepare sinks that compare into each using block, so every tail use
re-derives it from the spilled `hopt` byte and the derived 0/1 is held in r9 between the curve store and the event.
The original spills a phi of constants once and reloads it.

| IR edit on dfc3693 (llc oracle) | bytes | ratio | tail plain |
| --- | ---: | ---: | ---: |
| main | 27,400 | 0.59916 | 739 |
| e1: crossed holder sources (pool CPI from holder, event from curve) | 27,408 | 0.59578 | 733 |
| e2: curve store holder before cashback | 27,400 | 0.59916 | 739 |
| e4: holder in a 1 B alloca (emulates the slot; frame shifts) | 27,312 | 0.57074 | 761 |
| e5h: holder = `phi [true bb16, false bb18, h bb19, h bb20]` at the shared/holder join | 27,384 | 0.58675 | **763** |
| e5x: e5h + crossed sources | 27,368 | 0.58423 | 756 |
| e5c: e5h + cashback phi | 27,224 | 0.51488 | 680 |
| e6: event holder from curve only | 27,392 | 0.59655 | 734 |

e5h is the original's representation and gives the tail +24 plain tokens, but it loses 66 exact tokens in the
TransferCreatorFeesToPumpV2 / sharing clone runs (orig 0x2800-0x3800: deep spill slots move by 8) and the window by
-0.012. The source form is `if shared{if holder{(true,..)}else{..(false,..)}}else{(holder,..)}` in the tuple tree
(untested as a build: the oracle loses).

### 3c. Small tail items

- Sweep start: the original keeps `amm_frozen` in r8 and spills `data_is_empty()`; ours does the reverse.
- emit_cpi: `authority_bump` in r6 / `&authority_info` spilled in the original (w13a19 covers this).
- movescan (w13a12 sink/hoist of single pure instructions, all 865 candidates on dfc3693): nothing above main at
  27,400 B. Near misses: hoist of the create_idempotent Err payload `extractvalue` (sweep token arm,
  bb108.i -> bb45.i104) 0.60114 at 27,384 B; hoist `%239` (validate) 0.60015 at 27,392 B.

## 4. Source trials (measure.sh, main dfc3693)

| trial | change | bytes | ratio |
| --- | --- | ---: | ---: |
| v01 | event `is_cashback_coin: cashback` | 27,408 | 0.59668 |
| v02 | event `new_creator: target` | 27,496 | 0.34868 |
| v03 | event `new_creator_fee_bps: fee.unwrap_or(old_fee)` | 27,424 | 0.59141 |
| v05 | pool CPI holder from the `holder` local | 27,432 | 0.59760 |
| v06 | event `is_holder_reward: a.bonding_curve.is_holder_reward` | 27,392 | 0.59865 |
| v08 | tail `let a=&*ctx.accounts;` | 27,400 | byte-identical |

v06 is the event form that main 16c10e6 now carries (as part of another lane's composite).

## 5. Conclusion and next ideas

The tail register residual (R-bound +0.035, FR-bound +0.062) is not local to the tail. Its two largest causes are
upstream representations:
1. **holder as a spilled phi of constants** (region 1, the shared/holder tuple tree);
2. **`swept` coalesced with the Err payload in r9**, which needs the skip path to join the sweep Result before the
   `?` tag test without the MBP relayout (region 2, w13a27/w13a31's mechanism).

Next:
- Combine e5h with the clone-run register levers of w13a21/w13a29 (its loss is in those runs' deep spill slots).
- For 3a, look for a sweep-exit join that keeps the original block chain (w13a31's `bw:bb104.i:20:1` restores it
  in IR; a source construct that makes the transfer_vault_tokens Err edge colder is still missing).
- Re-run `tools/bound.py` after each landing to check the tail's share.

## Tools (`tools/`; experiment only)

| tool | use |
| --- | --- |
| `side.py orig.dis cand.dis [lo hi]` | side-by-side alignment (registers, frame offsets and jumps masked) over an orig range; ` ` exact, `~` same shape, `!` unmatched |
| `tail.py <fn.bin\|.o\|.so>` | ratio + tail tokens matched plain / reg-masked / frame+reg-masked |
| `bound.py <x> [lo hi]` | R and FR remap bounds for an orig range |
| `bound2.py <x> lo hi` | spill-slot-only and spill+reg bounds |
| `regperm.py <x> lo hi [seg]` | orig->cand register pair counts per segment |
| `payload.py <x>` | Err-payload r8->r9 bound |
| `vrun.sh <name> <edit.py> <workN>` | copy the crate, apply exact-string EDITS, measure, print ratio and tail counts |

The tools import `ctoracle.py` from `../../w12a02-cto-iroracle/scripts`. `orig.dis`/`cand.dis` are
`addr  insn` listings (w13a23 `dis.sh` for llc objects). IR edit files for the llc oracle are in `edits/`
(`ctoracle.py run <m.ll> <out> --edit edits/e5.py`; `E5=h|c|x|cx` selects the e5 variant).
