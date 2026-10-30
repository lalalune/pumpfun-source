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
