# w13a28-cto-entrycopy2: the entry copy of `new` on the k1 frame (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 6ac6f9b (k1, 0.56291), 06e6bb8 (0.57669) and dfc3693 (0.59916).
Continues w13a03-cto-entrycopy (#2914), w13a16-cto-e32late-2 (#3009, "remove the st escape") and w13a24-cto-ctostatesroa (#3011).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a28-cto-entrycopy2/` (not in git).
Ledger keys: `0x22a10-w13-{6ac6f9b,06e6bb8,dfc3693}-entrycopy2-*`.

**Result: no zero-loss gain.** Every source form that puts `new`'s 7/9 B pieces in the frame loses 0.02 to 0.10 on
these bases. The same is true when the frame is then fixed by an IR oracle. This notes PR records the mechanism and the
evidence. Trial edit lists are in `e/` (exact `(old,new)` source substitutions, see `e/common.py`) and `x/` (raw-IR edits).

## What the original does (orig 0x22ee8..0x22fe0, and the validate arm at 0x23618)

- After the CtoState stores, `new` is copied unconditionally, with no branch on the tag:
  tag -> spill, `[1,8)` -> 7 B at T 0x658, `[8]` -> spill, `[16]` -> r9, `[24,33)` -> 9 B at T 0x668.
  Then come the sk copy (T 0x470), the holder_key copy (T 0x518) and the mayhem test.
- In validate's non-holder arm (0x23618..0x23688), `t` is built at T 0x4b8:
  - its 7/9 B ends are read from the `new` argument pointer (`ldxw [r7+3]`, `[r7+0]`, `[r1+0]` with r1 = new+0x18);
  - its `[8]` and `[16]` words come from the entry-copy SSA values (the spill at -0x900 and r3 = r9).
  So validate reads the argument, and GVN reused the copy's i64 loads for it. Only the sharing arm reads the copy's 7/9
  pieces (0x24268, into P1 at T 0x538/0x548).
- The frame from val6 down is: val6 0x651, new 7 B 0x658, 9 B 0x668, X24 0x680, holder_key 0x6a0, mint 0x6c0.
  Ours (k1) has `target.sroa.0` (7 B, the `[0,7)` piece of validate's 7/8/8/9-split target) at 0x658 and `hk` (33 B) at
  0x679 in that 40 B. In the original, the target is split 8/24 and has no 7 B piece there.

## Why the k1-style copy (`let args=&(new,)`) never reaches the frame

`new` is a `noalias` by-value argument that execute never writes, so it becomes readonly. Rustc emits
`memcpy(_27 <- %new, 33)` for `args` (raw IR). opt treats a copy from a noalias readonly argument as a copy of constant
memory, drops `_27` and reads `%new` in the sharing arm. Every plain copy form is forwarded the same way:

| form (6ac6f9b / 06e6bb8) | result |
| --- | --- |
| `let su=Some(new)` / `&Some(new)` / `&(Some(new),)` at the args position (h2/h4/h6) | tokens = main |
| the same after the CtoState literal or before validate (h1/h3/h5) | no pieces; 0.5616-0.5625, +40 / -184 B |
| `mut su=Some(new)` overwritten with `Some(None)` / `None` in the other sharing arms (s1-s6) | 0.507-0.521, no pieces |
| `nc=new.map(\|k\|k)` read only by the sharing arm (e1-e6) | forwarded or conditional; 0.48-0.556 |
| `args=&(new.map(\|k\|k),)` (c1/c2/c4) | one unsplit 32 B piece (`_26.sroa.5`), 0.510-0.527 |

Raw-IR oracle (`x/`, rx.py on 06e6bb8, main 0.57669):

- `memset(%new,0,33)` right after the validate call (x1) keeps the copy at entry, but as one unsplit 32 B piece at
  0x678 (four unaligned `ldxdw`), not 7/8/8/9: 0.51115 at 27,424 B.
- A tag-only store or a clobber just before `ret` (x2-x4) does not keep it: 0.480-0.522.

The original's 7/8/8/9 split appears in our builds only when **validate itself reads the copy**. Those forms are
y4 (`validate(..,args.0,..)`), t4 (`let new=new.map(|k|k);` before validate) and d1 (the map before `args`).

## The faithful-split forms (validate reads the copy)

| trial | 6ac6f9b (k1 0.56291) | 06e6bb8 (0.57669) | dfc3693 (0.59916) | frame |
| --- | --- | --- | --- | --- |
| a1 = y4 | 0.49342 @27464 | | 0.50179 @27496 | |
| a2 = t4 | 0.52076 @27360 | 0.54248 @27376 | 0.54292 @27392 | new1 0x660/0x670, target.sroa.0 0x658, hk 0x691, holder_key 0x6b8 |
| a3 = U5/y3 (args after CtoState) | 0.51289 @27368 | | | |
| b1 = y4 + plain `let (holder_key,_)=PDA` | 0.52394 @27464 | | 0.54605 @27496 | **pieces at 0x658/0x668**, target.sroa.0 0x650, val6 0x649, holder_key 0x688 |
| b2 = t4 + plain PDA | 0.53395 @27360 | 0.55687 @27376 | 0.55251 @27392 | new1 0x660/0x670, holder_key 0x690 |
| d2 = map before args + plain PDA | 0.52545 @27432 | | 0.53507 @27488 | **pieces at 0x658/0x668**, holder_key 0x688 |

- b1's entry sequence is the original's, instruction for instruction: `ldxb tag -> spill; ldxw [+4]/[+1] -> 0x655/0x658;
  ldxdw [+8] -> spill; ldxdw [+16] -> spill; ldxb [+0x20]/ldxdw [+0x18] -> 0x660/0x668`. It sits before the CtoState stores
  instead of after them, and the pieces are read by validate's `t` (to -0x450/-0x2d0), not by the sharing arm.
- The plain `let (holder_key,_)=find_program_address(..)` form gives the original's PDA call: seeds at -0x450, sret at
  -0x2d0 inside `_54.i`, then a copy to holder_key. On every entry-copy form it is worth +0.01..+0.03 over `hk`. On k1
  itself it loses (f6 0.51827), because `hk` is k1's 33 B stand-in for the original's 40 B (new pieces + X24).
- Skeleton ratio (registers and frame offsets masked, w13a20 `fdelta.py`): b2 0.8601, k1 0.8532. b2's code shape is
  closer. The token loss comes from frame offsets and register assignment.

### Frame oracles on the faithful forms (llc on post-opt IR, `iredit.py` + w13a16 `padins.py`; 6ac6f9b, k1 0.56291)

| oracle | ratio |
| --- | ---: |
| b2 + 24 B stand-in before holder_key + `mv:target.sroa.0:END` (pieces 0x658/0x668, x24 0x680, holder_key 0x6a0, mint 0x6c0) | 0.53417 |
| d2 + x24 / b1 + x24 | 0.53854 / 0.53762 |
| d2 + signer slice resized to 24 B before holder_key: P1 lands at the original's 0x538/0x548 | 0.52365 |

Even with holder_key, mint and new's pieces all at the original's offsets, the faithful forms stay about 0.025 below k1.
What still differs:

- the sret/spill slots are -8, because `target.sroa.0` only moves below mint;
- the original also has the outer payload P2 split 7/9 at 0x550/0x560 ahead of E32 at 0x580 (orig 0x243e0);
- register assignment changes because the copy's i64 pieces are live from entry.

## Side results

- `let holder_key;let hk=PDA;holder_key=hk.0;` moved before `shared` (the original's call order). This is w13a24's k2;
  w13a32-cto-hkfirst2 owns it.
  - 6ac6f9b: 0.56813 at 27,360 B.
  - 06e6bb8: 0.57687 at 27,384 B (+0.0002, 16 B short).
  - dfc3693: 0.59745 at 27,392 B (below main).
  - With any entry copy on top (g2/g3/g5/f1/f3/f4) it collapses to 0.42-0.45 and +40..+300 B.
- `let args=(new,)` by value (c8): 0.5596 at 27,144 B (-256 B). This is a large size lever if a later composite needs one.

## Next ideas (untried)

- Produce the original's split without validate reading the copy. A Pubkey use of the copy that needs i64 access at
  [8]/[16] would make SROA split it, for example the sharing payload built as `Some(Pubkey::new_from_array(..))` or
  by-field. Combine that with a write to `new` after validate (x1 shows a clobber keeps the copy at entry).
- Move the copy after the CtoState stores and the target to an 8/24 split together. w13a02's fee-first
  `Result<(Option<u64>,Pubkey)>` gives the 8/24 split, which removes `target.sroa.0` from 0x650/0x658.

## Tools (tools/)

- `capvar.sh <name> <edits.py|-> <slot>`: w13a24's capture + rx oracle, repointed to this lane.
  `runq.sh <slot> names..` runs a queue of them.
- `absr.py names..`: frame-abstracted ratio (r10 offsets and `add64` frame immediates masked).
- `cover.py a b [bucket]`: per-original-region matched-token coverage of two rx trials, abstracted and raw.
  It shows where a variant gains or loses.
- `rec.py name status hyp [notes]`: records an rx trial from res.jsonl into the ledger (`BASE=` env sets the main).
- `padins.py`: copied from w13a16. Inserts a stand-in alloca before a given alloca.
