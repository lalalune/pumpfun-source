# w14a51-cto-sweepjoin: why ours has two sweep joins (J2), and what one join is worth

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w14a33-cto-nativejoin (#3333) next idea and w14a31-cto-knob8 (#3307) idea 2. The goal was to reach the original's
single swept join (orig 0x3c50/0x3c58, `ldxdw r1,[0x950]; ldxdw r6,[0x8f8]; jne r7,2`).
Bases: main 6e011ea42 (0.65548) for the map and oracles; key oracle re-run on main 63308119b (0.65698).
Ledger: approach `sweepjoin`, keys `0x22a10-w14-6e011ea-sweepjoin-*` and `0x22a10-w14-6330811-sweepjoin-*` (10 rows).

**Result: no source change.** Removing J2 is worth about 0 tokens (on 6e011ea) or less (on 6330811). The original's
one-join layout also depends on a block-frequency margin that our source does not have. The mechanism map below explains
both, so later lanes can skip this lever.

## 1. Mechanism: why `sweep.exit` is copied (J2)

On main, post-opt IR, `sweep.exit` (phis, `lifetime.end(_114.sroa.5)`, `icmp eq tag,2`, `br`) has exactly two
predecessors:
- `bb49.i`: the Ok-side join. It takes native amount==0, transfer_native Ok and Err, frozen Ok(0) and token zero, and
  ends the lifetimes of `_111` (`[bump]`), `_106` (seed array), `old`, `vsigner` and `dest`.
- `bb57.i`: the Err-side join. It takes the early Errs plus `bb53` (the post-vsigner Errs), and ends the lifetime of `dest`.

Both end in an unconditional `br`. In MIR, `exit` is `JNE_ri; JMP`: 2 instructions, because LIFETIME_END is a meta
instruction. Early tail duplication (LLVM 18.1.7, pre-RA, not "simple") only duplicates a block when **every** predecessor
ends in an unconditional branch (`canCompletelyDuplicateBB`). So `exit` is copied into both joins and deleted. That makes
J2 (`LBB0_324: jne r7,2,+1; ja LBB0_85`) plus the bb57 copy that the Rent::get Err block falls into.
In the original, the Ok-side preds (0x2160 `jeq r6,0`, 0x5b10 `jeq r1,2`, 0x5e88 `jeq r6,0`) branch conditionally
**straight into the join**. That gives `exit` a conditional predecessor, so it is never early-duplicated.

## 2. Mechanism: why removing J2 wrecks the layout (0.55)

Any IR form without J2 (`e/q1.py` folding bb49 and/or bb57 into exit, or w14a06's e5 empty asm `e/q4.py`) gives 0.551.
The cause is MachineBlockPlacement's `hasBetterLayoutPredecessor`. Main's chain is `Rent::get` -> Err (`bb85`, 62.5% by the
zero heuristic) -> exit -> `bb89` (post-sweep). With exit's predecessors now direct, the placement refuses the
`bb85 -> exit` fallthrough when another chain-end predecessor P satisfies `freq(P->exit)*0.8 >= freq(bb85)*0.2`.
The native amount==0 edge (`bb86 -> exit`, `icmp ugt lamports,min`, 50%) has freq 0.0000439 against a bar of
0.25*0.000146 = 0.0000365. That edge is the only offender: frozen/zero preds are 0.0000228 and 0.0000137, transfer results 0.000011.
Exit and the whole post-sweep region then move after the sweep tail (orig 0x5000-0x6000 lost: -362 raw / -418 sk).
The condition comes from P(zero)*P(rent ok) < 0.25*P(rent err)/0.8, so the original has to satisfy
P(native zero edge) < 0.417. Its CFG has the same compare (`jgt r0,r3`) and the same Rent test (`jeq r1,0`). The original must
therefore differ in frequency (or chain state) somewhere upstream, and no source form found so far reproduces that.

## 3. Oracles (post-opt IR + llc, `tools/pe.py`; main 6e011ea 0.65548 unless noted)

| oracle | J2 | bytes | ratio | vs main (raw/fm/sk) |
| --- | --- | ---: | ---: | --- |
| llc `-tail-dup-size=1` / `=3` / `-disable-early-taildup` | - | 27384 / 27504 / 27368 | 0.59065 / 0.46046 / 0.58603 | global, not source |
| `-tail-merge-size=1,2,4`, `-tail-dup-placement=false`, `-disable-tail-duplicate` | yes | 27400 | = main | byte-identical |
| q1b: bb49 folded into exit (lifetime.ends moved into exit) | gone | 27392 | 0.55101 | -362/-377/-418 (layout) |
| q1a: bb49+bb57 folded / q1c bb57 only / q1d lifetimes dropped | gone | | 0.55109 / 0.46039 / 0.2373 | |
| q4a: empty asm in exit (w14a06 e5) | gone | 27392 | 0.55101 | same tokens as q1b |
| q2/q4b: q1b or asm + `!prof` 7:5 on the native `amount>0` test | gone | 27392 | 0.65049 | layout restored; Rent slots 0x450/0x470 swap |
| **q4d**: q4b + Rent temp `lifetime.end` moved from exit into bb49/bb57 | **gone** | 27392 | **0.65438** | **-1/+0/-1**: only J2 removed + ensure-Err block moved |
| q5a: weight 7:5 alone (J2 kept) | yes | 27400 | 0.65428 | ensure-Err block moved (weight artefact) |
| q2ab: one fully merged join (the original's shape) + 7:5 | gone | 27384 | 0.64939 | -15/-1/-2; swept still r3 + `mov r8,r3` |
| q6: native zero edge carries constant 0 (orig `mov r9,0`) | yes | 27408 | 0.65389 | |
| r4d on main 6330811 (0.65698), weights 3:1..4:1 | gone | 27384 | 0.65088 | -13/-10/-3 |
| r4d on 6330811, 7:5 / 2:1 / 10:1 / none | gone | | 0.570 / 0.569 / 0.570 / 0.611 | layout |

In q4d the native arm matches the original's shape exactly: `jeq r1,2,-0x3d8` into the join and `ldxdw ..; mov r7,r1; ja -0x3db`,
the same offsets as the original. The join itself still lacks the original's r1/r6 reloads, and swept is still not in r9.
**One join is worth -1/0/-1 tokens and frees 8 B on 6e011ea, and loses 10 fm on 6330811.**
The swept-register residual (r9) does not move with J2. It needs the coalescer-order change that w14a06-cto-sweptcoal mapped (its NOTES, e1/e3), and
those changes collapse.

## 4. Source forms (raw-IR capture + oracle, `s/gen1.py`, `s/gen2.py`; main 6e011ea)

| form | bytes | ratio | note |
| --- | ---: | ---: | --- |
| d0: seeds as named locals `bb:[u8;1]`, `sa:[&[u8];3]` assigned in place | 27400 | 0.65189 | control |
| d1: d0 plus `vsigner`/`old`/`bb`/`sa` declared (deferred init) before `dest` | 27400 | 0.38017 | Ok join and the single Err join get identical lifetime.end lists, but SimplifyCFG does not merge them, so J2 stays. Frame-masked = d0: pure frame shift from the early lifetime.start |
| f1: `let r:Result<u64>=if native{..}else{..}; let v=r?; Ok(v)` | 27424 | 0.3764 | 16 tag tests, structural collapse |
| f1c: `Ok(r?)` | 27416 | 0.37646 | |
| f1d: `match r{Ok(v)=>Ok(v),Err(e)=>Err(e)}` | 27400 | = main | byte-identical |

w14a33 (native spellings, early returns), w14a06 (~30 gate spellings) and w13a49 (`#[cold]` Err helpers) already cover the other
spellings in this angle's list. Every one of them is main's tokens or a CFG change that collapses.

## 5. Next ideas (untried)

1. The one-join state needs P(native zero edge) < 0.417, or a higher Rent::get Err frequency. A source shape whose native arm adds a
   50/50 branch on the zero path *before* the join (for example a `?` on an infallible call there) would satisfy it. It is only
   worth trying together with a +8 B knob, because J2 removal frees exactly 8 B and is otherwise neutral.
2. The original also has placement-time copies of the test in three call-result preds (orig 0x24a8, 0x2610, 0x6398:
   `jne r7,2; ja bb89`). None appear in q4d. They are a layout-mode tail-dup effect that only exists once J2 is gone.

## Tools (`tools/`, text only; paths point at this lane)

`rx.py`, `capvar.sh`, `capraw.py` (w14a31/w14a38 raw-IR oracle), `pe.py` (w14a33 post-opt edit + llc), `ch.py`, `sbs.py`,
`sites.py`, `absratio.py`, `amap.py`, `dis.sh`, `disso.sh` (w14a25), `segdiff.py`, `splice.py` (w14a38), `jm.py`, `gen4.py`, `gen8.py`.
Oracle edits: `e/q1.py` (fold joins into exit), `e/q2.py` (+weights), `e/q4.py` (asm), `e/q4d.py`, `e/q5.py`, `e/q6.py`,
`e/r4d.py` (q4d generic, for main 6330811+).
Debugging recipe: `llc ... -print-before=early-tailduplication -print-after=early-tailduplication` and
`-print-after=block-placement` (MBB order); `opt -passes='print<block-freq>'` / `'print<branch-prob>'` on `m.ll` give the
frequencies that MachineBlockPlacement uses.
