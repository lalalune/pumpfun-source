# w14a78-cto-valerrplace: validate error-group placement (E306, 296), notes only

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 0d04cf460 (0.66507 / 3,228 slots, M 2,220, jM 2,249). Ledger approach `valerrplace`, keys
`0x22a10-w14-0d04cf4-valerrplace-*` (14 rows).

**Result: no landable change. The best zero-loss measurement is still main.** On main, nothing put E306 or 296 in the
original position without losing ratio. In w14a75's and-1 basin, E306 is already in the original position. What that
basin still needs is an IR block-order change for 296, worth +23 M, and I found no source spelling that produces it
(section 4).

## 1. Error-group map (corrects the brief's to_string labels)

Each error has its own name/msg constant. The constant comes right before the `ToString` path, which leads to the Err
block (its line is the `stw [r10-0x2b8]` immediate). Checked by following each to_string's `jeq r0,0` target:

| msg lddw | error | orig to_string / Err | ours (main) to_string / Err |
| --- | --- | --- | --- |
| 0x1b5e78 | 289 | 0x648 / 0x818 | 0x890 / 0x958 |
| 0x1b5e7c | 306 | 0x750 / 0xe60 | 0xf38 / 0x1000 |
| 0x1b5f50 | 298 | 0x910 / 0x9d8 | 0x5f8 / 0x7b0 |
| 0x1b5e08 | 326 | 0xb40 / 0x11a8 | 0xab8 / 0xe88 |
| 0x1b5db8 | 296 | 0xf40 / 0x1008 | 0x6e8 / 0xda8 |
| 0x1b5e38 / 0x1b5e04 | 312 / 307 | outlined, 0x1258 / 0x1328 | inlined, 0xce0 / 0x11c0 |

So "to_string(0x1b5e7c)" is E306's own to_string, not E289's. Its original position is the fallthrough of the
`!holder` tag test (orig 0x730: `ldxdw [-0x8f8]; and 1; jeq ->next; ja 0xc08`).

The scorer masks lddw immediates, so the to_string blocks are token-identical apart from their frame slots. The global
alignment already pairs them crosswise: orig ts289 with our ts298, orig ts306 with our ts296, and so on. On main, error
order alone is therefore worth only the line and code immediates of the Err blocks. **Original Err306 (0xe60-0xf38,
27 instructions) is entirely unmatched.**

## 2. BPF layout mechanism (why weights and placement-only moves mislead)

- `BPFInstrInfo::analyzeBranch` cannot analyse conditional branches. So in `buildCFGChains`, MachineBlockPlacement glues
  every block that ends in a conditional branch (with a fallthrough) to its **IR-order successor**. MBP can only reorder
  the chains between those glued pairs, and in a free block that ends `jcc T; ja F` it may put T next. That gives the
  original's `jeq ->next; ja far` idiom, and that idiom is a free-block choice, not a reversed condition.
- So there are two layout inputs: (a) IR block order after opt, which rustc fixes in first-reference order and which
  decides the glued pairs; (b) branch probabilities, which decide free blocks. For (b), BPI's zero heuristic applies to
  `icmp eq X,0` (12:20), but not when X is `and Y, pow2`. The original's holder and tag tests are both `and 1` (50/50),
  so a 50/50 tie goes to the first successor, the `!holder` / `None` side, as in the original. Ours are `and -3` and a
  ranged `icmp eq tag,0` (12:20), so the other side is laid out first.

## 3. Pricing on main (fixed-RA oracles + real llc)

| probe | ratio @ bytes | M / jM | errseq (first 7) |
| --- | --- | --- | --- |
| main | 0.66507 @27,400 | 2,220 / 2,249 | 298 289 296 326 306 312 307 |
| IR: tag test `and 1` (306 None side first) | 0.65618 @27,416 | 2,191 / 2,245 | 298 289 296 306 326 .. |
| IR: holder `and 1` (H1) | 0.58102 @27,360 | 1,938 / 2,078 | 289 298 296 306 .. |
| IR: H1 + tag `and 1` (H1T) | 0.65147 @27,336 | 2,172 / 2,291 | **289 298 306 296 326 312 307** (orig) |
| IR: trunc holder + tag (HT) | 0.65279 @27,400 | 2,179 / 2,300 | orig |
| H1T + curve-store chain bb38..bb46 back in place (relay) | 0.66037 @27,344 | 2,202 / 2,320 | orig |
| relay: Err306 between bb38.i and ts312 | 0.66946 @27,408 | 2,235 / 2,252 | jump distance only (jM +3) |
| rscan (any validate block, glue may break) best | | +15 M / +3 jM | = the row above |
| IR glue scan (irscan) on main: ts296 away from the holder_enabled test | 0.66477 @27,400 | 2,219 / **2,329** | |

Source forms:
- 306: let-else, `is_none`+unwrap, `&new`, `as_ref`, `is_some`+unwrap, `has:bool` forms (g2/g3 0.65488 @27,400 with
  3,203 slots, g4, f2). They are either token-equal or below main.
- The range-free tag read
  `if unsafe{*(&new as *const Option<Pubkey> as *const u8)}&1!=0{unsafe{new.unwrap_unchecked()}}else{..}` reproduces
  the IR tag `and 1` exactly (0.65618 @27,416). It is w14a39's gene `tu8`.
- 312: `!=&&` (s1/s5) glues bb38.i to bb45.i, the original fallthrough, but pulls 330/338 forward, giving 0.63301. With
  the fee chain placed back by the relay oracle it is still M 2,200.
- 296: success-first spellings are token-equal. Every CFG-changing form drops into the 26.8 K outline basin (two more
  to_strings outlined, errseq 289 298 312 306 296, 0.43-0.54).
- Holder via `unwrap_or(false)` collapses (0.42-0.50).

## 4. The lead: 296 IR order on w14a75's basin (k_st_ql_first, 0.65997 @27,352, errseq already original)

`irscan.py` moves each validate error group to every IR position and re-runs llc, so registers are recomputed. On the
basin, any block placed between `bb13.i` (the holder_enabled test) and `bb14.i` (ts296) gives **0.66687 @27,352,
M 2,224 (+23), jM 2,339 (+22)**: the same size and above main's M. It is the only positive group move. In the original
the enabled test falls into the 298 new test (0x8f8 -> 0x900) and ts296 is out of line (0xf40).

The cause is rustc's first-reference order. `switchInt(e) -> [0: Err296, otherwise: join]` creates the Err block right
after the test, because the join already exists. Spellings tried, all failing (they are token-equal or fall into the
outline basin):
- else-if 289/296;
- nested ifs;
- 296 inside the holder arm;
- `let bad` / `let ok`;
- a match guard;
- `|`;
- `let e`;
- `Err(..)?`.

Untried: a fresh, non-empty success block at the last test, i.e. an `else` arm that survives MIR SimplifyCfg but folds
in LLVM.

## Tools (`tools/`, experiment only)

Copy w14a71's `tools/` (rx.py, capvar.sh, batch.sh, llcscore.sh, asmscore.py) next to these:
- `relay.py <m.s> <out.s> <spec>`: a branch-aware relayout oracle. It makes every fallthrough explicit, places a block
  list in a new order, then re-derives `ja` the BPF way (it drops a `ja` to the next block and adds one for a broken
  fallthrough, with no condition reversal).
- `rscan.py <m.s> <out.jsonl> FIRST LAST`: a single-block move scan with `relay.py` semantics, so glued blocks may move
  too. Prints M and jM.
- `irscan.py <named.ll> <out.jsonl> --span A:B`: the IR glue-order scan for error groups. Run `opt -passes=instnamer`
  first. `irmove.py` does a single IR block-range move.
- `mm.py`: M / jM / bytes for objects or `.s` files.
- `jdiff.py`: matched jumps whose offsets differ.
- `amap.py`: orig-to-ours alignment runs over a window.
- `chk.py`: per-chunk M deltas.
- `errmap.py`: an annotated validate CFG listing with msg constants and LINE immediates. It needs w14a66's `dis.py`.

Edit sets are in `e/`: rt1 (= tu8), g3, s1, a1, ma1, le, and ba1 (basin + a1, which reads w14a75's gene file).
