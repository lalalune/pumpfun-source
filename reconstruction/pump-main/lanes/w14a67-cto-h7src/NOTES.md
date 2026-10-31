# w14a67-cto-h7src: no source form gives the h7 hoist, and the h7 gain was a slot coincidence (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. This lane continues
w14a54-cto-feetag (#3375), section 3 and next idea 2: find a source form for **h7**. h7 is an IR edit that stores the
7-byte target piece straight into execute's `target.sroa.0` in validate's arms (`bb44.i`/`bb45.i`) and drops the join's
7-byte copy.

- Bases: main 2e1379de9 (0.65728 / 3,192), then 304b03a82 (0.65788 / 3,223) after #3378, #3379 and #3361.
- Ledger: approach `h7src`, keys `0x22a10-w14-2e1379d-h7src-*` (29 rows).
- **Result: notes only, no landable change.** The best zero-loss measurement is main.

## 1. h7 re-measured (raw-IR capture + rx/px oracle, `eq_main` true on both bases)

| probe | 2e1379d | 304b03a |
| --- | --- | --- |
| main | 0.65728 @27,400, fm 0.70431, sk 0.78850 | 0.65788 @27,400, fm 0.70282, sk 0.78820 |
| h7 (`tools/hoist.py m.ll out seven`, `JOIN=bb74`) | 0.65857 @27,368, fm 0.71613, sk 0.80066 | **0.65827 @27,368, fm 0.70204, sk 0.78747** |
| h7 both (7+9 pieces) | 0.61592 @27,272 | 0.58441 @27,352 |
| per-exit join copies (7+9 copy moved onto all 3 bb74 edges, `tools/pexit.py`) | 0.65122 @27,504 | 0.64575 @27,536 |

On 304b03a, h7 is worth only +0.0004 at -32 B, and its frame-masked and skeleton scores fall *below* main. In the asm,
h7 drops only the 4-instruction join copy (`[r10-0x53d]/[r10-0x540]` to `[r10-0x655]/[r10-0x658]`) and makes the arms
store at `0x655/0x658`.

## 2. Why h7 matched: 0x655 is not the original's target slot

In the original, `[r10-0x655]/[r10-0x658]` (7 B) and `[r10-0x660]/[r10-0x668]` (9 B) are the **entry copy of `new`**:

- They are written at 0x22f00-0x22f48 from `[r7+1..]`, before the mayhem test.
- They are read once, at the fee-Some exit (0x24268), and copied into the validate join slot `[r10-0x535]/[r10-0x538]`.
- The other per-exit copy into that join slot is at 0x23b50, from `[r10-0x44d]/[r10-0x450]`.
- The join slot is copied on to `[r10-0x54d]/[r10-0x550]` at 0x243e0.

The original's arms never write `0x655`. Our `target.i.sroa.0` (`0x53d/0x540`) is the original's join slot `0x535/0x538`
in all but name.

So h7 scores by placing our arm stores in the original's entry-copy slot. It is not the original's data flow. The original
does three things instead:
1. an entry copy of `new`;
2. per-exit copies from each source into the join slot, the fee-Some exit included (that block is the edge block the
   feeedge lane wants);
3. a later copy into execute's target.

## 3. Source forms tried on 2e1379d (every row keeps validate's signature and its `Result<Pubkey>` return)

| form | ratio @ bytes | fm / sk |
| --- | --- | --- |
| d1 deferred init `let target; if holder{..;target=*holder_key;}else{..;target=t;}` | = main (tokens) | = |
| d4 arms return `Pubkey::new_from_array(x.to_bytes())` | = main | = |
| d6 `Ok(Pubkey::new_from_array(target.to_bytes()))` | = main | = |
| d7 target as `[u8;32]`, `Ok(Pubkey::new_from_array(target))` | = main | = |
| d12 per-arm fresh local `{let k=*holder_key;k}` / `{let k=t;k}` | = main | = |
| d14 `holder_key.clone()` / `Ok(target.clone())` | = main | = |
| g2 `#[inline] fn validate` | = main | = |
| g3 execute `let mut target;target=validate(..)?;` | = main | = |
| g5/g6 `match (holder,new){(true,Some(_))=>Err,(true,None)=>*holder_key,(false,..)=>{..;t}}` | = main | = |
| d9 `let mut target=Pubkey::default();` assigned in the arms | 0.65689 @27,432 | 0.70389 / 0.78802 |
| d8 `let mut target=*holder_key;` before the holder test | 0.64702 @27,480 | 0.69578 / 0.78133 |
| d3 `let r:Result<Pubkey>=Ok(if holder{..}else{..});` fee checks; `r` | 0.50532 @27,376 | 0.61591 / 0.77237 |
| g1 `#[inline(always)] fn validate` (MIR inlining) | 0.53434 @27,224 | 0.62359 / 0.77566 |
| e2 `let v=validate(..);let mut target=v?;` | 0.38095 @27,416 | 0.65439 / 0.74573 |
| d13 target as `&Pubkey`, `Ok(*target)` after the fee checks | 0.32440 @27,112 | 0.59669 / 0.73524 |
| e1 `match validate(..){Ok(t)=>t,Err(e)=>return Err(e)}` | 0.28091 @22,648 | validate duplicated, not inlined (as w14a66 m1-m4) |
| f1/f2/f3 fee checks split into `fn fee_check(..)->Result<()>` called after `validate(..)?` | 0.09334 @9,080 | `sweep` is no longer inlined; fee_check's to_strings are inlined (they sat on cold call sites in validate) |

The arm-copy spellings are all token-identical to main: MIR and SROA reduce each of them to the same
`target.i` → `target.sroa.0` hop.

## 4. Mechanism: why no spelling reaches h7

The join copy `memcpy(target.sroa.0 <- target.i.sroa.0, 7)` copies a whole 7-byte alloca into a whole 7-byte alloca.
The only LLVM 18 transform that can merge the two is MemCpyOpt's stack-move (`performStackMoveOptzn`).

- On main it bails because the fee-check error exits mean the join does not post-dominate the arm writes, while
  `target.sroa.0` is read and written later.
- It also bails with those exits removed. In the IR test (`pd.ll`), bb44.i/bb45.i branch straight to bb74 and bb58.i
  goes to its error block, then `opt -passes=memcpyopt` runs, and `target.i.sroa.0` survives. The reason: the
  reachability check on dest's later uses (`isPotentiallyReachableFromMany`) gives up after 32 blocks, and execute has
  hundreds, so the check conservatively answers "reachable".

So in a function the size of execute, stack-move cannot fire for any spelling. The hop disappears only when validate's
target and execute's target are the same source variable. That means hand-inlining validate into execute, which also
makes the 9-byte piece direct (the `both` row, -0.04 to -0.07).

## 5. Related IR bounds (`tools/ecopy.py`, `tools/pexit.py`)

- Entry copy of `new`'s pieces into fresh allocas before the mayhem test, read by the non-holder arm:
  - on main: 0.44248 (7 B) / 0.44082 (7+9) / 0.44182 (all pieces);
  - on h7: 0.44275 / 0.44109 / 0.44119.
  - sk falls to about 0.59. The long-lived copy sets off a register-allocation cascade across the whole function.
- Per-exit join copies (section 1 table) lose 0.006-0.012, plus 72-136 B.

## 6. Next ideas (not tried here)

- The original's three-hop target flow (entry copy, per-exit copies into the join slot, then a copy into execute's
  target) needs both an entry copy of `new` that survives SROA and JumpThreading of the join per exit. Every isolated
  piece of it costs 0.01-0.2 on today's skeleton, so it only pays as one combined rewrite, sized with the knob catalog.
- The feeedge lane should stack its edge block on main rather than on h7: h7's extra fm/sk margin is gone on 304b03a.

## Tools (experiment only; never source proposals)

These are w14a54's `capvar.sh`, `capraw.py`, `rx.py`, `px.py` and `eseq.py` (paths retargeted), plus:

- `hoist.py`: the join block name now comes from the `JOIN` environment variable (default bb74).
- `batch.sh`: two workers, capture and rx, then px with fm/sk/err.
- `rec.py`: ledger recorder.
- `ecopy.py`: entry-copy oracle.
- `pexit.py`: per-exit copy oracle.

Edit sets are in `gen/` and results in `results.jsonl`.
