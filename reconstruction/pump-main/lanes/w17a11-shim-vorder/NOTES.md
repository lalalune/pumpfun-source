# w17a11-shim-vorder: validate error-block order (V1-V5) under the shim track (notes)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main d4dfb04b0 (0.67645, M 2,258) for the first oracle capture, then main fd78179b8 (0.67855, 3,220 slots).
Ledger: approach `shimvorder`, keys `0x22a10-w17-d4dfb04-vorder-<item>-v1` (and `-fd78179-` for the second base).

Angle: make the validate error blocks appear in the original's order. Measured by the PumpError::name call order
(`tools/errseq.py`, the k_u32 order of calls.json):

| | name-call order (validate) |
| --- | --- |
| original | 289 306 298 326 296 312 307 330 338 334 |
| main | 298 296 289 326 312 306 307 330 338 334 |

## 1. Why the order is what it is: BPF block placement is glued to the ISel order

`BPFInstrInfo::analyzeBranch` returns "cannot analyze" for every conditional branch. Two consequences, both visible
in `llc -debug-only=block-placement` on the slim module (`fx/m0/mbp.txt`, 303 "Pre-merging due to unanalyzable
fallthrough" lines):

- `MachineBlockPlacement::buildCFGChains` pre-merges every block that ends in a conditional branch with a fallthrough
  into its ISel layout successor. ISel order is the post-opt IR order, which descends from rustc's first-reference
  order (RPO codegen; for a bool `switchInt [0: F, otherwise: T]` the F block is created first).
- MBP can only order whole chains. After a chain ends in an unanalyzable `jcc X; ja Y` block, the next chain comes
  from the work list by highest block frequency, so error chains sort by frequency (w15a02's observation).

So two levers move an error block: its probability (MBP successor choice and frequency order) and its IR position
(glue). Both are reachable with shims: `expect_p` for the first, MIR first-reference order for the second.

## 2. The 1-second oracle on current main

`tools/capraw.py` (one identity build that also writes the pre-opt IR, about 1 minute) + w17a06's `preslim.py`
(survivor list `surv-1647da0.txt` still exact) + `fx.py` (opt -O3, slim, llc): token-identical to main
(d4dfb04b0: M 2,258 @27,400; fd78179b8: see section 5). About 1 s per run when the machine is not saturated.

- `tools/vx.py name "B289:0.5,Bf45:0.47"`: inserts `llvm.expect.with.probability` on named validate branches of the
  pre-opt IR (the IR a source `if unsafe{expect_p(c,..)}` produces). Branch ids are listed in `vx.BR`.
- `tools/pmv.py`: pre-opt validate block moves (`A>B` = put block A right after block B), i.e. the IR order a
  first-reference change produces.
- `tools/px.py`, `tools/ro.py`, `tools/mv.py`: post-opt (llc-only) weights, full reorders and moves.
- `tools/errseq.py <fn.bin|so|orig> [-v]`: name-call order and From (line-imm) order.
- `tools/mm.py`: exact M and masked M (registers, r10 offsets and jump offsets masked).
- `tools/sweep.py`, `tools/hc.py`: parallel sweeps and a batch hill-climb over weights + moves.

## 3. Results on main d4dfb04b0 (M 2,258)

| trial | name order | M | bytes | note |
| --- | --- | ---: | ---: | --- |
| main | 298 296 289 326 312 306 307 330 338 334 | 2,258 | 27,400 | |
| 1:2000 on every validate error edge (the angle's recipe) | (errors pushed to the tail) | 1,535 | 26,368 | collapse: lddw 83, every to_string outlined |
| same + 284 | | 1,402 | 26,032 | |
| each single error edge 1:2000 | | 2,056-2,257 | | all lose (289 2,162; 298 2,138; 306 2,223; 307 2,056; 312b 2,257) |
| B289 0.5 (and-1 50/50 on hr && !holder) | 289 296 298 ... | 2,163 | 27,400 | llc-only 1:1 on bb7.i identical; loss spread over 0x0 (-21), 0x4800 (-33): spill weights |
| single expect_p, 20 branches x 15 p (300 runs) | | max 2,260 | 27,400 | only Bf45 (holder-arm fee None) 0.47/0.5, a spill-slot permutation of -0x908..-0x928; 0.49 = 2,250, 0.51 = 2,063 |
| greedy pairs from Bf45 0.5 (217 runs) | | 2,260 | | no pair adds |
| source `if expect_p(fee.is_some(),true,0.5){raw payload}` (fee50, measure.sh) | | 0.6218 | 27,360 | collapse: the MIR call sits after the cashback join, so the fee switch is no longer duplicated per arm |
| post-opt reorder to the original layout order | 289 284 306 298 330 326 296 338 312 307 334 | 2,072 | 27,392 | ISel order is RA's input order |
| pre-opt moves, 11 error blocks x 42 positions (451 runs) | | max 2,258 | | every code-changing move loses |
| pre-opt B5 = `bb10>bb7;bb23>bb14;bb27>bb23;bb22>bb16;bb80>bb22` | **289 306 298 326 312 296 307** 330 338 334 | 2,244 | 27,400 | masked M 2,787 vs main 2,765 (+22 structural), exact -14 |
| 312 after 296 (B5 + any 312 move) | unchanged | 2,237-2,244 | | 312 needs the to_string outline to move |
| holder_key-first 312 memcmps (+ p 0.375..0.9) | | 2,240-2,251 | | loses |

Reading B5: the original order costs only 14 exact tokens because error blocks differ from one another in just two
tokens (line and error-code immediates), so difflib already matches them out of order. The 22 structural tokens it
gains are lost to frame naming inside the moved blocks: the name-result slot of {289, 298, 296} is -0x470 in ours and
-0x488 in the original; 306 uses (-0x4d0, string -0x488) in the original, while ours puts 306 with 312/307 at
(-0x488, -0x470). In the original -0x470 holds the sharing-key copy and -0x518 the holder_key copy (ours: sharing key
at -0x518, holder_key read at -0x6a0). That is entry-frame work (w17a09 pdaslot, w17a10 newpieces). Once those slots
move, B5 should be retested: its structural gain is there.

## 4. Source realisation of B5 (not built)

B5 needs rustc to create, during RPO codegen of validate, the 306 test and 306 error right after the `!hr` holder test,
the 289 error right after the `hr` holder test, and the 298 test and 298 error right after the holder_enabled test.
In today's MIR they are created late, because the 306/298 tests hang off the `let target=if holder{..}else{..}` join
(bb21), which is codegen'd only after all its predecessors. A spelling that tests `new` inside each arm of the head
(`if st.holder_reward {..} else if holder {..} else {..}`) creates them early, but needs the 298 check on both holder
arms with one line immediate (a closure or `#[inline(always)]` helper defined on line 298).

## 5. Results on main fd78179b8

(see below)
