# w14a121-cto-delwin: delete-window candidates for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base: main
**ebe5387e1** (M 2,247, ratio 0.67316, 3,123 slots). Angle: w14a111-cto-tag660's next ideas (#3499). Delete instructions
that ours emits and the original does not, then use the shiftmap alignment value (k=+2: +16 B in the sweep body
0x1d28-0x3400 plus -16 B in 0x3be0-0x5de0 is worth about -200 slots at equal M).
Ledger approach `delwin`, keys `0x22a10-w14-ebe5387-delwin-*` (31 rows).

**Result: no source change, notes only.** The delete-window store-backs come from the `sharing_update` tag, not from the
accounts pointer. They are produced by a greedy region split, and every source form that changes that split costs at least
5 M. Every source form that leaves the split alone is byte-identical to main.

## 1. What the delete-window pairs are (correcting #3499)

`tools/sb.py` lists adjacent reload/store-back pairs (`ldxdw rX,[r10+o]; stxdw [r10+o],rX`):

| build | pairs |
| --- | --- |
| original | 3, all at `[r10-0x950]` (-2384): 0x1d48, 0x44c8, 0x5b30 |
| main ebe5387 | 4, all at `[r10-0x8e0]` (-2272): 0x3108, 0x3ce0, 0x5940, 0x5b18 |

- In the greedy MIR (`-stop-after=greedy`), all four pairs belong to one spill slot, `%stack.186`. Its defs are the
  head-tree phi `%_553.sroa.0.0 = phi i8 [new tag, bb20], [2, bb21], [2, bb22], [0, bb18]`, the **`sharing_update` niche tag**
  (2 = None, 0 = Some(None), new's tag = Some(Some)).
  - Its uses are the sharing match (`bb88`, `and 255; jne 2`), the `val7` tag store (`bb35`) and the event's
    `sharing_config_reset` (CodeGenPrepare sinks the `icmp ne 2` back to the event, so the tag lives until the event).
  - The pairs sit in the inlined-sweep blocks `bb60.i`, `_ZN71_`, `bb85.i`, `bb88`. The `bb94.i` pair is not adjacent.
    There are 7 more dead reloads of the same slot.
- Debug llc (`-debug-only=regalloc`, pre-RA vreg `%59`): the tag is **region-split for $r9 over 97 edge bundles**
  (cost r9 0.0524 < r4/r7/r8 0.0634 < r6 0.0672). bb.269 (`bb88`) is "stack-out, spill after last use"; later evictions in the
  sweep re-split the r9 product. The split pieces that are reloaded and live out are re-spilled to the same slot, which
  leaves the store-backs.
- The original's store-back slot `[0x950]` is the **holder-reward flag** (the tree phi of constants that tag660 identified
  as the curve +0xa5 store and pool-CPI r4 source). The original's tag is `[r10-0x8f8]`, reloaded cleanly into r6 at block
  heads 0x1d30 / 0x3c58 / 0x4a90 / 0x4d48 / 0x60e0. So the two programs **swap RA roles between two tree phis**. Ours has no
  long-lived holder flag, because it uses `holder.unwrap_or(false)` and re-reads the curve for pargs, so the tag takes the
  role.
- The 0x5938 insert (`stxdw [r10-2488],r6` before the pair) is the accounts pointer spilled at the head of sweep block
  `bb85.i`. It is laid out post-sweep. The original has r6 dead there, because `a` lives in `[r10-0x8d8]`.
- Dead reloads are not an ours-only artifact (`tools/deadld.py`): original 16, ours 14.

## 2. Exact value of the deletions (`tools/pairgain.py`: delete ours instructions, insert the same count of junk slots)

| delete (ours) | insert at | M | slots |
| --- | --- | ---: | ---: |
| 0x3ce0/0x3ce8 (bb88 pair) | 0x1d28 / 0x2400 / 0x3000 | 2,247 | 2,926 / 2,928 / 2,929 |
| 0x5940/0x5948 (bb85.i pair) | 0x1d28 / 0x2400 / 0x3000 | 2,247 | 2,917 / 2,919 / 2,920 |
| 0x5b18/0x5b20 | 0x1d28 / 0x2400 / 0x3000 | 2,247 | 2,917 / 2,919 / 2,920 |
| 0x5938-0x5948 (3 insns) | 0x1d28 / 0x2400 / 0x3000 | 2,247 | 3,054 / 3,115 / 3,124 |
| 0x3108/0x3110 (sweep pair) | 0x1d28 | 2,247 | 3,120 |

The shiftmap prediction holds: one tag pair removed plus 16 B of M-neutral sweep-body fill is worth about -200 slots.

## 3. What moves the tag split (post-opt IR + llc, `ix/`, `px.py`)

| probe | M | bytes | store-backs |
| --- | ---: | ---: | --- |
| x1 hoist the reset `icmp` into the phi block | 2,247 | 27,400 | eq_main (CGP sinks it) |
| x2 event reset from its own head phi-of-constants i1 (tag dies at the match) | 2,182 | 27,352 | **0** |
| x3 x2 + sharing match on that i1 | 2,181 | 27,336 | 0 |
| x4 / x5 val7 tag store constant / `tag&1` (probe only) | 2,238 / 2,240 | 27,392 / 27,408 | 4 |
| llc `-split-spill-mode=speed`, `-disable-spill-hoist`, `-enable-local-reassign`, `-restrict-statepoint-remat` | 2,247 | 27,400 | eq_main |
| llc `-split-spill-mode=size` | 1,829 | 27,312 | |

Only shortening the tag's live range to the sharing match removes the pairs, and that costs 65 M (the r9 split carried the
whole sweep's colouring).

## 4. Source screens (raw-IR capture + rx opt/llc, main M 2,247)

| variant | bytes | M |
| --- | ---: | ---: |
| b4 `swept=(!skip).then(..).unwrap_or_else(\|\|Ok(0))?` / m3 bump read after `native` / m4 bump first / s9 `amm_frozen=if amm_present{..?}else{false}` | 27,400 | 2,247 (eq_main) |
| a7 `let reset=sharing_update.is_some()` before the match | 27,392 | 2,242 |
| i6 (w14a119 I6 alone) | 27,416 | 2,246 |
| vb (vol334_back alone) | 27,392 | 2,246 |
| a6 `if let Some(&val)=sharing_update.as_ref()` | 27,376 | 2,210 |
| a8 `sharing_config_reset:sharing_update!=None` | 27,392 | 2,208 |
| c1 `curve.is_holder_reward=holder==Some(true)` | 27,408 | 2,204 |
| t_v_h1 / t_v_h6 (tag660 tree holder flag into the curve store; re-priced) | 27,408 | 2,204 (store-backs unchanged, loss spread, -17 at orig 0x4800) |
| t_v_h3 / t_v_h7 (+ pool arg from the flag) | 27,472 / 27,448 | 2,071 / 1,904 |
| m1 / m2 `current_creator.key()` read before the AMM CPI | 27,400 | 2,042 |
| a1 `sharing_update.map(..).transpose()?` / a5 `for val in sharing_update` / a9 `map_or` | 27,280 / 27,384 / 27,376 | 1,817 / 1,747 / 1,466 |
| s4 `else if amm_present` (reuse binding) / s8 nested `if amm_present{if token_frozen..}` | 27,320 / 27,440 | 1,730 / 1,570 |
| b5 `swept=..map_or(Ok(0),\|r\|r)?` | 26,616 | 1,584 |

Delete candidates 2 (near-exit `ja; mov64 r8,r3`) and 3 (J2) were not re-screened. #3499 and w14a51/w14a33 already
cover them.

## 5. Reading for other lanes

- The delete-window store-backs are worth about -200 slots each, but they belong to the tag's r9 region split, which is the
  backbone of the sweep colouring. Removing them means giving that role to the holder flag, as the original does: a tree
  phi of constants used by the curve store and pool CPI r4. Every spelling of that so far loses 43+ M, because the rest of
  main was hill-climbed around the current data flow. It would need a joint re-tune, not a single edit.
- The tie-break route needs M-neutral non-zero-size knobs. On ebe5387 the only ones found are w14a119's vol334_back+I6
  family (+8 B, M 2,247). No M-neutral -16 B post-sweep knob is known.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

`sb.py` (store-back pairs), `deadld.py` (dead frame reloads), `pairgain.py` (exact delete/insert pair price),
`sbsc.py` (side-by-side by ours offset), `unm.py` (pure inserts/deletes in a window), `mc.py` (M/bytes/slots of rx outputs),
`binm.py` (per-bin M delta between two rx outputs), `screen.sh` + `rec.py` (capvar loop + ledger rows), `dis.py`.
`ev/*.py` are the source edits, `ix/*.py` the post-opt IR probes. The capture/oracle pair is w14a84's `capraw.py`/`rx.py`/`capvar.sh`.

Addendum: sharing match re-priced on ebe5387. `match sharing_update{None=>{}Some(val)=>..}` is byte-identical.
`match &sharing_update{..*val}` gives M 1,828 at 27,392 and keeps 4 store-backs. The `if let` form was not finished
because the machine was contended; w14a109 and w14a119 already price it at -5 M.
