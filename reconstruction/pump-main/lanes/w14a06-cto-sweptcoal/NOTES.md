# w14a06-cto-sweptcoal: swept / Err-payload coalescing map (step 1 of the clone-run chain)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: continue w13a40-cto-clonera7fb (#3164) next ideas 1-2, w13a44 (#3149) next idea 1 and w13a48 (#3193).
This lane owns only step 1: getting `swept` (the sweep result) to coalesce into the Err-payload register class.
w14a01-cto-acctlive owns the `%0` accounts-pointer live range (step 2).
Bases: main 308b545f1 (0.63062, 3,287 slots) for all trials; key oracles re-run on main 769f331fe (0.63241).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w14a06-cto-sweptcoal/` (not in git).
Ledger: approach `swept-coalesce`, keys `0x22a10-w14-308b545-sweptcoal-*` (13 rows).

**No source change is proposed.** Nothing beat main, so nothing was built with `measure.sh`. This PR holds the coalescing
map, the oracles and the tools.

## 1. Oracle check

The w13a40 raw-IR capture (`tools/capvar.sh` -> `tools/capraw.py`) plus the opt/llc oracle (`tools/rx.py`) reproduce the
baseline exactly. On 308b545 it gives 0.63062 / 3,287 slots / 27,400 B with `eq_main=true`, and on 769f331 it gives 0.63241 with `eq_main=true`.
`tools/coal.py` (debug llc `-debug-only=regalloc`) and `tools/payreg.py` agree on main:

| main | payload class | loads | swept in class | payload reg | `%0` split | clonefeat | event swept from |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 308b545 / 769f331 | `%1668` | 22 | no (`%1639`, spilled) | r8 | `$r8` in 94 bundles | 2/6 | r1 (reload) |

## 2. Why swept does not coalesce on this main (coalescer order)

The CFG at the sweep exit has changed since w13a40's notes. The Err edge is now IR `bb80`
(`%565 = inttoptr i64 %_384.sroa.18.4`). Early tail-duplication copies the tag test (`sweep.exit`) into `bb51.i` (the
native-arm end), so in MIR `bb.270.bb80` has 2 preds and 1 succ. `tools/blk.py mi0.txt '<pattern>'` prints each payload copy with its block's pred and succ counts:

| block | copy | preds+succs | visited |
| --- | --- | ---: | --- |
| `bb.361.bb61` (post-sweep Err join: sharing CPI, pool CPI, `bb59` = Clock/emit_cpi Errs; ends the `signer_seeds` temporaries) | `%1668 = COPY %386` | 3+1 = 4 | **first** |
| `bb.270.bb80` (sweep Err edge) | `%1668 = COPY %290` (= swept `%1639`) | 2+1 = 3 | later: `interference at %1668:29@64464r` |

64464r is the sharing-CPI payload copy, which sits before the tag branch where `swept` is live on the Ok edge.
RegisterCoalescer orders blocks by loop depth, then pred+succ count, then block number. `join-splitedges` is off by default,
so a 1-pred/1-succ copy-only block gets no priority. For swept to join first, bb80 needs degree 4 or more (it wins a tie at 4 on block number,
270 < 361), or bb61 needs degree 3 or less. **Both are CFG changes.** No source form keeps main's CFG and still changes this order.

## 3. Map: what coalesces swept, and what it costs (post-opt IR oracles `tools/pe.py`, edits in `edits/post-opt/`)

| oracle (308b545) | swept in | payload reg | `%0` split | cf | bytes | ratio | R-bound | FR-bound |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| main | no | r8 | r8 / 94 | 2/6 | 27,400 | **0.63062** | 0.73307 | 0.85051 |
| e1: pool CPI Err -> `bb59` (bb61 degree 3) | yes | r6 | r8 / 100 | 1/7 | 27,448 | 0.52529 | 0.62197 | 0.80066 |
| e2: sharing CPI Err -> `bb59` | yes | r6 | r8 / 100 | 1/7 | 27,448 | 0.52529 | | |
| e3: sweep AMM `transfer_creator_fees_to_pump_v2` Err threaded straight into `bb80` (what the original does; bb80 degree 4) | yes | r6 | r8 / 99 | 2/6 | 27,408 | 0.54276 | 0.6431 | 0.83331 |
| e3 + `asm "{r8}"(swept)` at the event store | yes | **r8** | **r6 / 83** | 2/6 | 27,536 | 0.48977 | 0.62005 | 0.78918 |
| e3 + `asm "{r9}"(swept)` (the original's register) | yes | r9 | r6 / 83 | 2/6 | 27,536 | 0.50471 | 0.62005 | 0.78918 |
| e1 + `{r8}` / `{r9}` | yes | r8 / r9 | r6 / 83 | 2/6 | 27,552 | 0.495 / 0.51023 | | 0.79462 |
| main + `{r8}` pin (no coalescing) | no | r9 | r9 / 98 | 2/6 | 27,256 | 0.6176 | | |
| e5: empty asm in `sweep.exit` (no tail-dup, bb80 1+1) | no | r8 | r8 / 94 | 2/6 | 27,392 | 0.58577 | 0.69124 | 0.80509 |

On 769f331, e1 is 0.52709, e3 is 0.54456, and e3+{r8} / e3+{r9} are 0.49156 / 0.5065, with the same classes, registers and splits.

What the table shows:
- **Coalescing is reachable only through a CFG change, and it puts the class on r6, not r8.** With swept inside, the class is the
  largest interval (size 16,800 against 4,384 on main). It evicts `%60` (the `sharing_update` tag, tested `and 255; jne 2` in
  bb81) from r6 (`tools/asg.py ra.log` lists the long intervals and their registers).
- **The premise "swept in the payload class with the class on r8 gives 6/2" does not hold on this main.** When the class is held on r8 (or
  r9), the `%0` region split moves to `$r6` in 83 bundles and the clone run still keeps the pointer in a register (2/6). Step 1 does not
  pull step 2 along. `%0`'s split follows whichever callee-saved register is cheapest in the validate use blocks
  (w13a44's R2), and on this main that is r6 once the class leaves it.
- **Coalesced states are structurally worse, not just renamed.** `tools/frseg.py` (per-0x800 plain / frame-masked / frame+reg-masked
  matches): e3 loses 30-68 plain tokens per region in 0x2800-0x3800 where the frame-masked counts are equal, because swept's spill slot
  disappears and the frame shifts. It also loses 36-47 frame-masked tokens in 0x4800 and 0x5800. Even with a perfect frame, e3 sits
  108 frame-masked tokens below main (2,316 vs 2,424). The FR bound of every coalesced state (0.79-0.83) is below main's
  0.85051.

## 4. Source forms (raw-IR capture + oracle, `edits/src/`, newline counts and `line!()` sites kept)

| form | swept in | bytes | ratio |
| --- | --- | ---: | ---: |
| f2 `(swept,)=(gate.transpose()?.unwrap_or(0),)` | no | 27,400 | 0.63062 (same tokens) |
| f3 `Ok::<u64,Error>(gate.transpose()?.unwrap_or(0))?` | no | 27,400 | 0.63062 |
| f5 `gate.transpose().map(\|o\|o.unwrap_or(0))?` | no | 27,400 | 0.63062 |
| f6 `match gate.transpose(){Ok(v)=>v.unwrap_or(0),Err(e)=>return Err(e)}` | no | 27,400 | 0.63062 |
| f1b wallet Result bound at 556, `w?;` on the sweep line | no | 27,392 | 0.62921 |
| f1 wallet and sweep Errs through one `?` (`w.and_then(\|()\|gate.transpose())?`) | no | 26,384 | 0.5439 |
| f4 `gate.map_or(Ok(0),\|r\|r)?` | no | 26,472 | 0.5378 |
| f7 `gate.unwrap_or(Ok(0)).and_then(\|v\|Ok(v))?` | no | 26,400 | 0.59869 |

The ledger already holds about 30 other gate forms (if/else, `mut`, `match skip`, `then_some`, `unwrap_or(Ok(0))?`, closures, `dest` and
`signer_seeds` scopes, `nat_q`, `ss_scope`). After opt, every gate spelling either produces main's tokens or changes the
sweep's inlining or size by about 1 KB. Only forms that change the Err-join CFG (`nat_q`, `ss_scope`, dest scope, i.e. e1/e3 at the source level)
coalesce swept, and all of them cost 0.08-0.19.

## 5. Conclusion and next ideas

Step 1 alone is not a lever on 308b545 / 769f331. Coalescing needs an Err-join degree change. Every such change re-lays the post-sweep
code, puts the class on r6 by eviction, removes swept's spill slot (frame shift), and leaves clonefeat at 2/6 even when the class is
forced onto r8 or r9. The bound for the whole clone-run shape is still about +0.01-0.014 (w13a40 / w13a44).

Untried ideas, in order of plausibility:
1. A joint step-1 + step-2 state. Coalesce through e3's AMM-Err threading (the original's own shape at 0x3b98) and at the same time make
   r6 expensive for `%0` in validate. That is acctlive's validate-region interference, the w13a44 R2 coupling. Screen with
   `tools/coal.py` + `tools/asg.py`, not with clonefeat alone.
2. Rebuild the frame around a coalesced state. Swept's spill slot vanishes, so an 8 B frame object at swept's old slot
   position (a size and frame knob) would show how much of e3's 0x2800-0x3800 loss is pure frame shift (about +100 plain tokens at most).
   e3 is still 108 frame-masked tokens below main, so this alone cannot win.
3. `bwscan.py` on e3_769 (the most local coalesced state so far), with the objective set to ratio rather than clonefeat.

## Tools (`tools/`, text only)

- Ported from w13a40: `rx.py`, `capraw.py`, `capvar.sh`, `coal.py`, `clonefeat.py`, `bwscan.py`, `ctoracle.py`, `obj.py`, `run.sh`,
  `segstat*.py`, `tokio.py`, `genes.py`, `bound.py`, `bound2.py`, `tail.py`. Ported from w13a44: `payreg.py`, `llcb.py`, `radbg.sh`, `sodis.py`, `llcdis.sh`.
  Paths point at this lane.
- New: `pe.py <m.ll> <name> <edits.py>` (post-opt IR edit -> llcb + coal in one line), `batch.sh <slot> <names...>` (source
  form -> capture -> rx -> coal, to `screen.jsonl`), `blk.py <mi0.txt> <regex>` (MIR copies with their block's pred/succ degree,
  the coalescer's visit key), `asg.py <ra.log> [n]` (final register of the n longest intervals), `frseg.py <o>...` (per-region
  plain / frame-masked / frame+reg-masked token matches).
- The `edits/post-opt/e*r8.py`-style files load `pe/e3.py` / `pe/e1.py` relative to the scratch dir; run them from there.
