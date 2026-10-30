# w14a12-cto-tagreg: the `sharing_update` tag register in admin_cto::execute (0x22a10)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main cef0574cf (0.63421, 3,178 slots) and f8dc9016f (0.63481, 3,172 slots).
Angle: w14a01-cto-acctlive next_idea 2 (#3211), using the w13a36-cto-tailregs tail map. Keep the `sharing_update` tag
(the `Option<Option<Pubkey>>` phi of 2/0/1) in a callee-saved register from the sweep exit to the event, as the original
does in r6.
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w14a12-cto-tagreg/` (not in git).
Ledger: approach `tagreg`, keys `0x22a10-w14-{cef0574,f8dc901}-tagreg-*` (about 60 rows).

**No source change is proposed.** No form beat main at 27,400 B. This PR holds the tag-register bound, the oracles and
the screens.

## 1. Bound: the tag register is worth at most about +0.0027

`tools/tagbound.py <fn.bin|so> <dis> [slot]` measures the tag-register residual with the code shape held fixed. It
FR-aligns ours to the original (registers, frame offsets and jump offsets masked). Inside the original's tag-in-r6 ranges
(orig 0x1d30-0x20f0, 0x3c58-0x3d28, 0x4a90-0x4c50, 0x4d48-0x4f38 and 0x60d8-0x60f8), it replaces each aligned ours token
with the original token when the original token reads or writes r6. It then deletes ours' unaligned tag-slot traffic
(`[r10-0x8e8]`) and re-scores the plain ratio.

| main | ratio | r6 tokens fixed | bound (r6) | tag reloads/re-spills deleted (after 0x2000) | bound (r6 + deletions) |
| --- | ---: | ---: | ---: | ---: | ---: |
| cef0574 | 0.63421 | 6 | 0.63601 (+0.0018) | 14 (incl. 5 non-tag / def stores) | 0.63735 (+0.0031) |
| f8dc901 | 0.63481 | 6 | 0.63661 (+0.0018) | 9 (0x30f0 0x3cc0 0x3cc8 0x3ce8 0x4ed8 0x5938 0x5a08 0x5e88 0x6378) | **0.63747 (+0.0027)** |

The deletions also shrink the window by 72 B, so a real form would have to repay that size. The tag's instruction shapes
already equal the original's:
- sharing match: `and 0xff; jne 2`, the Some-arm `stxb [r10-0x651]`;
- event: `and 0xff; mov r2,1; jne 2; mov r2,0`.

Only the register and the reloads differ. On main, ours reloads the tag from `[r10-0x8e8]` at 0x3cc0, 0x3ce8 and 0x4ed8, and
re-spills it in place at 0x30e8/0x30f0, 0x3cc0/0x3cc8, 0x5b28/0x5b30 and 0x5e80/0x5e88. Those `ldxdw r1,[X]; stxdw [X],r1`
pairs are SplitKit copies between two spilled split pieces that StackSlotColoring put in the same slot.

## 2. Why the tag has no register in ours (tail register map, f8dc901)

| value | original (0x4a90-0x4f38) | ours (0x4ae0-0x4fe0) |
| --- | --- | --- |
| r6 | tag (reloaded at the sharing-CPI join 0x4a90 and in the pool-CPI arm at 0x4d48, after the last clone) | accounts pointer in the clone run, then pool_updated (`mov r6,0` / `mov r6,1`) |
| r7 | clone destination / CPI Result tag | same |
| r8 | pool_updated (`mov r8,0` / `mov r8,1`) | pool-CPI holder arg (`ldxb r8,[curve+0xa5]` before the clones), then the accounts pointer |
| r9 | swept | `nf` (the #3200 event-fee local) |
| spilled | accounts pointer (reloaded per use), old_fee `[r10-0x8e0]` | tag `[r10-0x8e8]`, old_fee `[r10-0x8f8]`, swept `[r10-0x968]` |

Debug greedy (`-debug-only=regalloc` on the slim module) shows that after coalescing, `%60` has uses only at the sharing
match (`%1201` merged in, AND tied-def), the Some-arm `STB` and the event (`%1370` merged in). Its RS_Split round picks
`$r9` over 99 bundles (wallet and sweep regions). The pieces at the three uses then lose to the values above and are
spilled. In the original, at the sharing-section entry (orig 0x3c68), three predecessors carry r6 = tag and r9 = swept:
- the skip path (0x1d28 `mov r9,0; ldxdw r6,[0x8f8]`);
- the sweep exit (0x3c40-0x3c58);
- the native exit (0x60d8-0x60e0).

That is the swept/sweep-join CFG (w13a36 3a, w14a06), not a tag representation.

## 3. Oracles (post-opt IR + llc, `tools/llco.py`; cef0574)

`fm`/`frm` = difflib ratio with frame offsets / frame offsets + registers masked. Treat them as hints only: on p_own_nf the
+0.010 fm comes from a difflib realignment in orig 0x800 (`tools/regdiff.py`: 0x800 fm +40), while the tail loses 6
plain tokens.

| oracle | bytes | ratio | fm | frm | effect |
| --- | ---: | ---: | ---: | ---: | --- |
| main (null) | 27,400 | 0.63421 | 0.68544 | 0.80647 | |
| o1 event reads `creator_fee_bps` late (no nf) | 27,376 | 0.63000 | 0.69264 | 0.81672 | old_fee takes the freed register; pool_updated r6->r9; tag still spilled |
| o3 tag dead after the sharing match | 27,360 | 0.62539 | 0.67666 | 0.80378 | |
| o2 tag in its own i8 alloca, reloaded at the event | 27,376 | 0.57545 | 0.67526 | 0.80084 | |
| o4 event reset = entry `shared` bool | 27,312 | 0.58515 | 0.66287 | 0.81530 | |
| o5 pool-CPI holder arg loaded right before the CPI call | 27,392 | 0.62921 | 0.68075 | 0.80539 | |
| o15 = o1 + o5 | 27,368 | 0.62860 | 0.68016 | 0.80426 | |
| a1 `asm "{r6}"` pin of the tag at the event | 27,264 | 0.59408 | 0.65085 | 0.78630 | the cascade costs far more than the bound |
| a2 pins at the sharing match and the event | 27,272 | 0.58739 | | | |
| a3 tag {r6} + pool_updated {r8} at the event (the original's pair) | 27,288 | 0.58811 | | | |

Forcing the original's tag register into ours' code shape re-lays the whole allocation (-136 B, -0.04). The tag register
follows from the shape; it is not a lever by itself.

## 4. Source forms (raw-IR capture + opt/llc = build tokens; `edits/`)

On cef0574 (0.63421):

| form | bytes | ratio |
| --- | ---: | ---: |
| tuple order: sharing_update first / last in the inner tuple (v1, v2) | 27,400 | = main (same tokens) |
| `Ok((..))?` re-wrap: sharing_update last (v4b) | 27,400 | = main |
| `Ok((..))?` re-wrap: sharing_update first (v4) | 27,400 | 0.63241 |
| `Ok((..))?` re-wrap without sharing_update (v3) | 27,400 | 0.55123 |
| event `matches!(sharing_update,Some(_))` (v5), reset last in the literal (v12) | 27,400 | = main |
| event `sharing_update!=None` (v6) | 27,392 | 0.62262 |
| `let reset=is_some()` right after the sharing match (v8) | 27,384 | 0.63290 |
| `let reset` before nf / before the event (v14, v15) | 27,400 | = main |
| `match sharing_update{None=>{}Some(val)=>..}` (v10) | 27,400 | = main |
| `match sharing_update.as_ref(){Some(&val)=>..}` (v13) | 27,376 | 0.62311 |
| reset carried in pargs / `(nf,reset)` / `(reset,pool_updated)` tuples (t1, t3, t4; #2766 tuple mechanism) | 27,400 | = main |
| event reads `creator_fee_bps` (no nf; s_nf) | 27,376 | 0.63210 |
| s_nf + 6 size knobs (+8/+16) | 27,376-27,392 | 0.62322-0.63150 |
| pool test owner first (`owner==&AMM && !data_is_empty()`, the original's call order; reverts #3207) (p_own) | 27,400 | 0.63241 |
| p_own + s_nf (p_own_nf) | 27,376 | 0.63270 |
| p_own_nf + each of the 47 applicable `sizeknobs-cto.json` knobs | 26,424-27,656 | <= 0.63270 |
| p_own_nf + {g_w_clock_local, g_fee_unwrap} (pc1) | 27,400 | 0.63002 |
| curve store holder before cashback (c_hfirst; the original's 0xa5-then-0xa3 order) | 27,400 | 0.62972 |

On f8dc901 (0.63481):

| form | bytes | ratio |
| --- | ---: | ---: |
| s_nf | 27,376 | 0.63270 |
| p_own | 27,400 | 0.63301 |
| p_own_nf | 27,376 | 0.63330 |
| v4 | 27,400 | 0.63301 |
| c_hfirst | 27,400 | 0.63032 |
| v8 | 27,384 | 0.63350 |
| v8 + g_w_clock_local / wl_ts_clockvar | 27,400 | 0.63241 |
| v8 + ev_cb_local | 27,392 | 0.63281 |

Every tag-representation spelling either folds back to main's tokens (GVN/CSE fold `icmp ne tag,2`, SROA/CopyProp move
the tuple fields) or loses 0.001-0.08. The task's three ideas are all covered:
- re-deriving the tag at the event (o4 / v6);
- a u8 slot or tuple field (o2 / t1-t4);
- pool_updated losing r6 (o1 / a3).

## 5. Conclusion and next ideas

- The tag register is a consequence of the sweep-join CFG (swept and tag as r9/r6 live-ins of the sharing-section entry, w13a36 3a,
  w14a06) and of the holder phi (w13a51). Expect at most about +0.0027 from it once those land, and only if the 9 tag
  reload/re-spill tokens disappear at the same time.
- Re-run `tagbound.py` and the `a1` pin on any candidate that coalesces swept or carries the holder phi. If the tag then
  sits in r6 with no pin, the bound is collectable.
- `nf` late (the original reads `creator_fee_bps` at the event, orig 0x4fd8) and owner-first (the original calls memcmp
  before `data_is_empty`, orig 0x4be8/0x4c10) are both faithful forms. Each loses about 0.002 on today's shape plus 24 B
  to repay. Try them again together with any swept-coalescing candidate.

## Tools (`tools/`; copy `w14a03-cto-liverange/tools/{rx.py,dis.sh,capvar.sh,capraw.py,q.sh}` next to them)

- `llco.py <name> <edits.py> [--base m.ll] [llc args]`: post-opt slim-module edit + llc + ratio / fm / frm, with the disassembly in
  `rx/<name>/dis.txt`.
- `tagbound.py <fn.bin|so> <dis.txt> [slot]` (env `DELLO=<hex>`): the tag-register bound above.
- `regdiff.py <a> <b> [seg]`: per-orig-region plain and frame-masked matched-token deltas. Use it to check fm gains for difflib
  artifacts.
