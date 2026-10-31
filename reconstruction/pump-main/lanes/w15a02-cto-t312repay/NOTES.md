# w15a02-cto-t312repay: repay prices on the 312-only outline base T, and why T's 330/338 relayout happens (notes)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 90300f9d2 / ed47ac72a (admin_cto 0.67346, M 2,248, rfjM 2,810, 3,124 slots), re-checked on 86e2a6b74 (#3666,
0.67376, M 2,249): there T = 27,184 B / M 2,200, `T+dv1+le306` = 27,176 B / M 2,203, `dv1` alone = 27,392 B / M 2,248.
Continues w14a141-cto-outline312 (#3632) and w14a126-cto-origfill (#3596).
Oracle: w14a108 raw-IR capture + `opt -O3` + `llc` (`rx.py`, reproduces main exactly, `eq_main: true`), w14a141 `thr.py`,
`ibfi.py` and `inl.py`, plus the debug `llc` (`$C/llvm-dbg/build/bin/llc -debug-only=block-placement`).
Ledger: approach `t312repay`, keys `0x22a10-w15-{90300f9,ed47ac7}-t312repay-*-v1`.

**Result: no landable change.** Main is still the best zero-loss measurement (0.67346 / 3,124 slots / 27,400 B).

`T` is w14a141's trigger: `fn is_zero(t:&Pubkey)->bool` for the 307 test plus
`fn invalid_creator(t,sharing,holder_key)->bool` for the 312 test. It outlines 312 only, at 27,184 B and M 2,199.

## 1. What a repay has to do (the arithmetic)

The scorer is the difflib ratio `2M/(N_orig+N_cand)`. At 27,400 B, beating main needs M >= 2,249.
T is 27 tokens short at M 2,199. A perfect 216 B fill that matched every one of its 27 tokens would reach only M 2,226
(0.6668). So a repay must also win back about 23 tokens of T's own alignment loss. A plain fill cannot win.

## 2. Repay / spelling price table on T (rx oracle; T = 27,184 B, M 2,199, fM 2,296, rfjM 2,765)

| gene | change on T | bytes | M | fM | rM | rfjM | note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `dv1` | drop the line-334 `read_volatile(holder_key)` placeholder | 27,176 | **2,199** | 2,296 | 2,511 | 2,765 | **M-neutral on T** (on main: 27,392 B, M 2,247, -1 M); one codegen-forcing construct less |
| `dv2` | drop the line-338 placeholder | 27,176 | 2,122 | 2,197 | 2,430 | 2,627 | the 338 one still matters |
| `dv1+dv2` | both | 27,168 | 2,122 | | | 2,627 | |
| `le306` | 306 as `let Some(t)=new else{..};` | 27,184 | **2,202** | 2,296 | 2,511 | 2,765 | +3 (on main: M 2,233, -15) |
| `tnz` / `tcp` | 306 as `is_none()` + `unwrap()` / extra `t.clone()` | 27,184 | 2,202 | | | | = le306 |
| `le306+dv1` | | 27,176 | 2,202 | | | | best T variant (0.66236) |
| `fNf`, `cbi`, `mt306`, `icn`, `tref`, `tas`, `tby`, `tbx`, `frv`, `frn` | None-first fee match, `!holder&&st.cashback` local, 306 match, `valid_creator`, t by ref/as_ref/to_bytes, range spellings | 27,184 | 2,199 | | | | byte-identical to T |
| `p_ie`, `p_vc`, `p_mt`, `p_mf`, `p_le`, `p_bd`, `p_rq` | every if/else/match/let/`require!` spelling of the 312 helper test | 27,184 | 2,199 | | | | byte-identical to T (MIR canonicalizes; IR block order unchanged) |
| `ica` | helper takes `[&Pubkey;2]` + `contains` | 27,184 | 2,196 | | | | |
| `ifl` | `if let Some(f)=fee` | 27,192 | 2,113 | 2,289 | 2,427 | 2,777 | |
| `icv` | helper takes `t` by value | 27,264 | 2,115 | | | 2,746 | |
| `cbs` / `cbh` | cashback test inline (`!holder&&st.cashback`) | 27,176 | 2,049 | 2,330 | 2,369 | 2,754 | |
| `ok306` | `new.ok_or_else(..)?` | 27,088 | 2,053 | | | | 306 to_string outlined |
| `fsp` / `fspr` | split `f==0\|\|f>max` into two 338 sites | **27,392** | 1,790 / 1,688 | 2,268 | 1,948 | 2,741 | repays 208 B, but 334 moves after 410 and every arg spill slot shifts (`[r10-0x910]`->`-0x918` ...) |
| `fsp+dv1` | | 27,384 | 1,792 | | | | |
| `cav` | execute's cashback after the validate call | 26,928 | 1,705 | | | | |
| `vcb` / `vcb2` | validate takes `cashback:bool` | 27,368 | 1,570 | 1,612 | 1,796 | 2,089 | fee chain no longer duplicated per arm |
| `pcb` / `pcb2` / `pcb3` | validate returns `(target,cashback)` per arm | 26,944 | 1,206 | 2,138 | 1,194 | **2,812** | skeleton above main (2,810), but the frame shifts by 8 (see 4) |

Size knobs: of the 80 entries in `sizeknobs-cto.json`, 41 still apply on T. The positive-byte ones are all downstream and
cost 0.0004 to 0.22 on main (`w_create_rev` +272, `p_ev_ts_last` +280, `ev_nc_target` +96 ...). None of them can add the
23 tokens that section 1 requires.

## 3. Why T moves 330/338 into validate (debug-llc mechanism)

`llc -debug-only=block-placement` on main and on T:

- **BPF `analyzeBranch` cannot analyze conditional branches.** So MachineBlockPlacement pre-merges every block that ends
  in a conditional branch with its IR-order next block ("Pre-merging due to unanalyzable fallthrough"). For BPF, IR block
  order fixes most fallthroughs.
- On main, cmp2 (`bb38.i`, `t==holder_key`) is followed in IR by the 312 error block `bb39.i`, so they are pre-merged.
  The 312 success block `bb45.i` (freq 0.008) is then placed last among the leftover blocks, after 307. That gives the
  original's order: fee chain after 307.
- Under T, InlineFunction splices `invalid_creator`'s second compare (`invalid_creator.exit.i`) right after cmp1. Its IR
  successor is now `bb33.i` (the 307 error), so nothing is pre-merged. MBP picks the 62.5% success `bb46.i`. The join
  `bb75` is "not a candidate (non-cold CFG conflict)", so MBP continues `bb48` -> `bb53` -> `bb54` (330). The cashback
  test is `icmp eq i8 cb,0`, and the zero heuristic makes the error 62.5%. 330, and then 338, end up inside validate.
- The original also falls through on the 312 success (`jeq r0,0,<312>`, then 0x0d78). It chains a None-edge copy block
  (0x0e38) instead of the Some chain, because its non-holder Some chain head (0x1510) has **two** predecessors: the
  shared-override path and the non-shared path (the OV duplication, w14a89). Without OV, that head has a single
  predecessor and is always chained right behind the 312 tests.

IR bounds (`tools/reord.py`, `post.py`):

| bound | errseq | M | fM | frame census |
| --- | --- | ---: | ---: | --- |
| T | 298 289 330 296 326 338 306 312 307 334 | 2,199 | 2,296 | 215 bad / 826 ok |
| T, 312 compares weighted 5:3 or 2000:1 (error hot) | 298 289 312 296 326 306 307 330 338 334 | 2,196 / 2,193 | 2,346 / 2,343 | 221 / 840 |
| `r2` = T with the 312 error block moved after cmp2 in IR (pre-merge as on main) | same as 5:3 | 2,195 | 2,346 | **identical to main** (220 / 841) |
| T, non-holder fee-tag test weighted 2000:1 / 5:3 / 1:2000 | unchanged | 2,189 / 2,199 / 2,197 | | |
| T, reorder the 306 blocks before 296 in IR | unchanged (byte-identical) | | | |

So when the 330/338 relayout is fixed, fM and the frame census equal main's, yet M stays at 2,195. The outlined 312
block then sits right after the compares, and difflib matches it to orig 0x1258 (`tools/mb.py`). That match crosses
orig's 306/296/326 runs. Restoring 330/338 alone is therefore worth 0 M. The full repay would need the original's order
306 296 326 312 307 330 338, with 312 placed after 326. That needs the OV per-arm structure, the family that collapses.

## 4. The per-arm cashback return (`pcb`): the best skeleton, lost to an 8-byte frame shift

If validate returns `(target,cashback)` from each arm, the frame loses one `[16 x i8]` slot: the `Result<Pubkey>`
payload piece `%_48.sroa.11`, which feeds `%target.sroa.8 [9 x i8] align 1`. The 9-byte target piece becomes align 8.
Every frame offset then shifts by +8 (`-0x2d0` -> `-0x2c8`, `-0x38` -> `-0x30`). rfjM reaches 2,812, above main's 2,810,
but fM is only 2,138. Even a perfect frame fix stays below T. Adding an unused `[16 x i8]` alloca at IR level does not
restore the slot (M 1,291). This is the same 8 B CtoState colouring that w13a04/w13a38 found.

## Next ideas

- An ordinary source form whose 312 success block has a second predecessor, which makes MBP place the non-holder fee
  chain late as the original does. The only form known so far is OV. A non-OV form would also fix T's 330/338 relayout.
- `dv1` is free on any T-based candidate: drop the line-334 volatile there.

## Tools (`tools/`, experiment only)

- `g15.py`: the genes above, plus every `sizeknobs-cto.json` edit as `k_<name>`. It composes with w14a141's `g141.py`
  (`cv.sh` looks in g15 first).
- `rec15.py <results>`: ledgers each `cap.sh` row. `show.py <results>...`: one-line table.
- `reord.py <rx> <name> 'a,b>c'`: moves IR blocks of execute in a post-O3 `m.ll`, renumbering `%N` values, then runs
  llc and scores.
- `mb.py <cand>...` (`LO`/`HI` env): difflib matching blocks (orig offset, cand offset, length, shift) in a range.
- `es2.py <dis>...`: error-site order that ignores frame shifts.
