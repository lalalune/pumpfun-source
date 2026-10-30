# w13a43-cto-outline306: why the original outlines `to_string` at 307/312 (holder threading)

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main a71238f51 (admin_cto 0.62103, 88 lddw, 5 outlined `to_string`: 330 334 338 660 719).
Continues w13a17-cto-outlineport (#2982) and w13a04-cto-tostring296 (#2912). Ledger keys `0x22a10-w13-a71238f-outline306-*-v1`.
Every ratio below is the raw-IR capture + `opt -O3` + extracted-`llc` oracle (`tools/src.sh`, reproduces `measure.sh`;
main reproduces 0.62103 @ 27,400 exactly).

## 1. Oracles on a71238f

| raw-IR edit on main a71238f | bytes | ratio | lddw | outlined `to_string` lines |
| --- | ---: | ---: | ---: | --- |
| none (= main) | 27,400 | 0.62103 | 88 | 330 334 338 660 719 |
| branch weights Some:None = 1:2 on validate's 306 tag switch (w13a17 oracle) | 26,976 | **0.62430** | 86 | **307 312 330 334 338 660 719** |
| 2:3 on the same switch | 27,408 | 0.60656 | 88 | 330 334 338 660 719 |
| **holder threading** (`tools/thread.py`: the 289-pass edge and the 296-pass edge jump straight to the holder arm) | 27,016 | 0.61388 | 86 | **307 312 330 334 338 660 719** |

The 1:2 oracle is now +0.0033 above main while 424 B short: the outline tax is gone on this main.

## 2. The mechanism: the original's holder tests are threaded

Validate's pre-inliner BFI (`tools/bfi.sh`, cold cut 0.02 of validate's entry):

| site | 284 | 289 | 296 | 298 | 306 | 307 | 312 | 326 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main | 0.625 | 0.117 | 0.026 | 0.040 | 0.075 | 0.0283 | 0.0287 | 0.018 |
| v2 (289 nested, below) | 0.625 | 0.117 | 0.026 | 0.081 | 0.035 | **0.0132** | **0.0134** | 0.028 |

In main's IR the holder flag is tested three times (`hr&&!(hopt==Some(true))` at 289, `holder&&..` at 296, `if holder` at 298).
The 289 test is a separate `Option::eq` call, so nothing proves that the 289-pass path is a holder path. The 298
`br i1 %holder` at the join is 50/50, and the non-holder arm (306/307/312) gets 0.151 of validate's entry instead of 0.070.

The original is threaded. Its asm (orig 0x22ff0..0x23160):

- `0x23038 jeq hr,0` -> hr false: `0x23130 jeq holder,0` -> non-holder arm (new tag test `0x23150`, 306) or `ja` to the holder arm at 0x23308;
- hr true: `0x23050 jne holder,0,+0x57` -> holder arm 0x23308 directly, else the 289 error.

So in the original the non-holder arm is reachable only from the hr-false path. Its frequency is 0.070, and 307/312 fall to 0.013 (< 0.02),
which outlines them. 326 stays inlined because the holder arm gets warmer. Raw-IR threading (`thread.py`, 2 branch retargets)
gives exactly the original outline set. No weight or heuristic is needed.

## 3. Source forms (screen; all `tools/pair.sh` + `tsites.py`)

| var | genes (`tools/genes_w13a43.py`) | bytes | ratio | lddw | outlines |
| --- | --- | ---: | ---: | ---: | --- |
| v1 | 289 `st.holder_reward&&!holder` | 27,400 | 0.61624 | 88 | no |
| v6 | 289 `match (hr,holder){(true,false)=>Err,_=>{}}` | 27,400 | 0.61624 | 88 | no |
| v7 | 289 nested but `!(hopt==Some(true))` | 27,400 | 0.62103 | 88 | no (= main) |
| **v2** | **289 `if st.holder_reward{if !holder{return Err(..)}}`** | 26,928 | 0.52697 | 86 | **original set** |
| v4 / v5 / c1 / c2 | v2 + 296 `!(hr\|\|en)` / `if holder{}else{Err}` / `su=Some(new)` / `su=&Some(new)` | 26,928 | 0.52697 | 86 | original set |
| a1 / a2 | v2 + sharing arm `Some(new)` (args dropped / kept) | 26,800 | 0.53551 | 86 | original set |
| b1 | v2 + `args` after the validate call | 26,808 | 0.53604 | 86 | original set |
| b4 | v2 + holder by ref (`hb:&bool`) | 26,992 | 0.52814 | 86 | original set |

The nested 289 (`v2`) is the threading form. rustc lowers `if !holder` to a direct `br i1 %holder` on the same SSA value
that 296 and 298 test, so the early SimplifyCFG (dominating-condition implication) threads both tests. `&&!holder` keeps
an `xor`, which is not threaded.

## 4. What blocks v2: the `args` entry copy is no longer forwarded

v2's frame has one extra object: `_27.sroa.5`, a 32 B unsplit copy of `new`'s payload (from `let args=&(new,)`), at 0x678
above `hk`. Every spill moves 0x20 deeper (arg spills -0x930/-0x8f8/-0x908/-0x950; main -0x910/-0x8e0/-0x8f0/-0x930).
In main the sharing arm's `memcpy(_502.sroa.6 <- _27.sroa.5)` reads `%new+1` directly. In v2 it reads the copy.

- IR edit on v2's opt output: forward that memcpy to `%new+1` and delete the copy alloca -> **0.61485 @ 26,984, 86 lddw, original outline set** (`ed/v2g`).
  That is the threaded source form without the copy, about the IR-threading oracle (0.61388).
- `opt -memssa-check-limit=2000` (whole module) also drops the copy (0.55288, other functions move too). The forwarding
  failure looks like a MemorySSA walk budget: the 7 outlined calls add MemoryDefs between the entry copy and the sharing arm.

## Tools (`tools/`)

- `thread.py <raw.ll> <out.ll> <x|n|nh>`: the holder-threading raw-IR edit (line anchors are for a71238f's raw IR).
- `errs.py <disasm>`: (line, error code) for every `error!` site. `jt.py <disasm> <addr>..`: branches into an address.
- `pair.sh v..`: `src.sh` two at a time, then `tsites.py`. `src.sh` now keeps the raw IR, and `bfi.sh`/`bfix.sh` reuse it.
- `genes_w13a43.py`: the source genes above, which extend w13a17's `tools/genes.py`.
- The other tools are w13a17's, with paths switched to this lane.

## 5. Wave 14 continuation on main 53abf28b1 (admin_cto 0.62672): the outline is now a net loss everywhere

Oracle (`tools/src.sh`) reproduces main 53abf28 at 0.62672 @ 27,400, 88 lddw, outlines 330 334 338 660 719.
Ledger keys `0x22a10-w14-53abf28-outline306-*-v1`.

| form on 53abf28 | bytes | ratio | masked (frame-blind) | lddw | outlined `to_string` |
| --- | ---: | ---: | ---: | ---: | --- |
| main | 27,400 | **0.62672** | 0.69712 | 88 | 330 334 338 660 719 |
| IR: weights Some:None 1:2 on validate's 306 switch | 26,976 | 0.58234 | 0.68438 | 86 | original set |
| IR: 1:3 / 1:5 / 1:10 | 26,968 / 26,952 | 0.58394 / 0.48867 / 0.48867 | | 86 | original set |
| IR: callsite `noinline` on 307/312 only | 27,024 | 0.55889 | 0.61137 | 86 | original set |
| src v2: nested 289 `if hr{if !holder{Err}}` (threading) | 26,968 | 0.51902 | 0.62319 | 86 | original set |
| src e1: w13a41 t8 (holder_key + sharing by value, validate reads `args.0`, plain PDA tuple) | 27,384 | 0.56278 | 0.62481 | 88 | main set |
| src e1n: e1 + nested 289 | 27,208 | 0.45236 | 0.43913 | 86 | original set |
| src e2: e1 + w13a41 t28 bool locals | 27,776 | 0.53518 | 0.61312 | 88 | main set |
| src e2n: e2 + nested 289 | 27,368 | 0.55229 | 0.63860 | 86 | original set |

- On a71238f the 1:2 oracle was +0.0033 over main. On 53abf28 it is -0.044. The outline tax is back, and it is not in
  validate: `tools/regcmp.py` (matched original instructions per 200/400-instruction bin of the original) shows the
  validate bins within a few instructions of main and the loss in the **CPI clone run, orig 0x2580-0x3840**
  (m3w12 -19/-27/-91/-7 per 200-insn bin). That is the clone-run register-assignment basin of w13a40/w13a44 (#3164, #3149):
  any change that shortens validate's live ranges moves the greedy-RA split of the accounts pointer, and main's current
  basin is the better one.
- v2's own source blocker on 53abf28 is smaller than on a71238f (#3155 moved `args` after the CtoState stores): the frame
  is only 8 B deeper, because `target.i.sroa.0` takes `_116.i` in stack coloring and `target.sroa.0` is left alone
  (`tools/sc.sh`). But even frame-blind v2 is 0.623 against main's 0.697.
- `tools/lendelta.py` on the 1:2 oracle: the original's validate region (0x0-0x1900) is ~70 instructions longer than our
  outlined form, which is where the 432 B gap lives. w13a41's by-value entry copies (e2n) fill it to -32 B faithfully,
  but e2n still loses 0.07 in the same CPI region.
- e2n + single size knobs (`tools/kscreen.py`, first 10 of 65 applicable knobs): 0.533-0.553. The screen was stopped,
  because single knobs move e2n by about 0.01 and the gap is 0.075.

## 6. What moved the outline basin: #3155's `args` placement

The outline oracle was +0.005 on 52c0b08 (w13a44) and is -0.044 on 53abf28. Reverting the parts of #3155/#3168 one at a time
(`tools/mkv.py` genes RSH, RPA, RAR, RTU), each without and with the 1:2 weights:

| base 53abf28 + revert | no weights | + 1:2 weights (original outline set, 86 lddw) |
| --- | ---: | ---: |
| none (main) | 0.62672 @ 27,400 | 0.58234 @ 26,976 |
| RSH (#3168 `shared` as if-expr) | 0.62663 @ 27,408 | 0.58225 |
| RPA (#3168 pool `pargs`) | 0.62412 @ 27,392 | 0.58031 |
| RSH+RPA (= 6ff770f) | 0.62403 | 0.58023 |
| RTU (#3155 tuple order) | 0.62554 @ 27,424 | 0.58208 |
| **RAR** (#3155: `let args=&(new,)` back before the CtoState block) | 0.62242 @ 27,384 | **0.62768 @ 26,920** |
| RAR+RTU (= a71238f) | 0.62103 | 0.62642 |

On main 23322b07c (0.62882): weights alone 0.58475, **RAR + weights 0.62980 @ 26,920 (+0.001, -480 B)**.
So the outline only pays when `args` is copied before the CtoState stores: with the copy after them (#3155) the shorter
validate moves the clone-run register split.

Source forms on the RAR base (all outline the original set):

| form | bytes | ratio | note |
| --- | ---: | ---: | --- |
| IR holder threading (`thread.py`) | 26,960 | 0.61724 | threading costs 0.010 against the weights; frame = main |
| nested 289 (s1n) | 26,944 | 0.52862 | frame +0x20: the `args` entry copy is not forwarded again |
| nested 289 + `args=&new` / `Some(new)` (s1na/s1nb) | 26,800 | 0.53733 | no copy, but frame -8 and the CPI run moves |
| nested 289 + by-value keys (s1e/s1eb, w13a41 t8/t28) | 27,304 / 27,408 | 0.408 / 0.387 | |
| RAR + by-value keys + weights (e3w12 / e3bw12) | 27,104 / 27,240 | 0.517 / 0.403 | the w13a41 entry forms are not a usable fill |

Bound: the best source-expressible outline (threading) sits about 0.01 under main on the RAR base before any of the
440-480 B fill is added, and every fill tried so far costs more. The angle is exhausted on current main.

Next ideas (untried):
- a source form that makes the 306 `Some` edge cold without threading (BPI has no heuristic on the `trunc` switch;
  the weights oracle is 0.010 better than threading);
- the v2g memcpy forwarding as a source form on the RAR base (the original copies `new` too, per w13a41, so look for
  a copy that GVN forwards, e.g. a copy taken inside validate);
- a 440-480 B fill that keeps the RAR+weights CPI basin. Screen it with `brw.py` on each fill's raw IR before building.
