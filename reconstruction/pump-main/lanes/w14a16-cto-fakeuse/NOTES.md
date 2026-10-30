# w14a16-cto-fakeuse: live-range-extension oracle for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w14a03-cto-liverange next idea 1 (#3210 generalised). #3210 gained by adding a late use of one value
(`coin_present`), which lengthened its live range and flipped greedy's eviction choice. w14a03's oracles only
shorten or split ranges. This lane builds the opposite one: it lengthens ranges.
Bases: main cef0574 (0.63421) for the first scans, main b174038 (0.63571, after #3241 and #3250) for the pda map, and
main 7e6aa9c (0.6414, after #3267) for a final re-scan.
Ledger: approach `fakeuse`, keys `0x22a10-w14-{cef0574,b174038}-fakeuse-*`.

**Result: no zero-loss gain and no source change.** Across 80,000+ extension variants, none that a source spelling
could produce beats main at 27,400 B. The only finding other lanes can use is a partner map for the pda-first front
(see below). Even that front stays below main in the IR oracle.

## Oracle (`tools/`, experiment only)

| tool | what it does |
| --- | --- |
| `irext.py <m.ll> <out.jsonl> --mode M` | **Extension oracle.** Input is the post-opt `m.ll` that `rx.py` writes. The tool parses execute's CFG, dominators and SSA liveness. For a value V and a block B that V's def dominates and where V is dead, it inserts `call void asm sideeffect "", "r"(T V)` at the start of B (`start`) or before B's terminator (`end`). The asm emits no instructions. The variant then goes through llc (about 0.15 s) and is scored with the rx tokens. LLVM 18 has no `llvm.fake.use`, so the oracle uses asm. Modes: `start`/`end` (frontier blocks, `--depth K`), `all` (every dominated, dead, non-`unreachable` block; filter types with `IREXT_TYPES`, cond-branch blocks only with `IREXT_CONDONLY`, end position with `IREXT_POS`), `impl` (the real #3210 shape: `br i1 %c` -> `br i1 (and/or %c, V)` for every dominating dead i1 V), and `calib`/`calib2` (asm at an existing use). `IREXT_WIN=n` skips the ratio when the size is more than n bytes off 27,400. It runs about 8 variants/s on 10 processes. |
| `combo.py <m.ll> v@blk[@end] ...` | Applies several insertions at once. `--keep` writes `var/combo/keep.o`. |
| `rank.py <jsonl>...` | Per-value ranking: best delta at 27,400 B and best delta at any size. |
| `chunks.py <o>...` | Exact-match instruction counts per 0x800 orig region (difflib on masked tokens). |
| `capvar.sh`, `rx.py`, `capraw.py`, `q.sh`, `dis.sh` | w14a03's raw-IR capture and opt/llc oracle, re-pointed at this lane. `eq_main` holds on cef0574 and on b174038. |

Calibration: an asm use placed at a value's existing last use is byte-identical for only 205 of 1,559 values. The other
1,354 change because a sideeffect asm in mid-block is a scheduling barrier, or because a folded GEP has to be
materialised. An asm at the start of a block where V is already live-in is byte-identical for 274 of 4,539 placements:
when V is spilled there, the use adds a reload. So **the "zero-instruction" use is zero-instruction only while V stays
in a register.** In practice an extension almost always changes the size.

## Map on main (cef0574 and b174038)

`map-cef0574.txt` (37,195 variants: frontier start/end, all dominated blocks for scalars and pointers, cond-branch
end mode) and `map-b174038.txt` (22,063 variants) hold the per-value ranking.

| main | variants | at 27,400 B | gain at 27,400 | loss at 27,400 | byte-identical |
| --- | ---: | ---: | ---: | ---: | ---: |
| cef0574 (asm, all modes) | 37,195 | 3,499 | 55 | 2,669 | 433 |
| cef0574 `impl` (and/or merge) | 6,618 | 949 | 1 | | 416 |
| b174038 (asm, all scalars + ptrs) | 22,063 | 1,621 | 29 | 1,355 | 182 |
| 7e6aa9c `impl` (and/or merge) | 6,618 | 900 | 1 (Rc clone check `%cond.i2.i243`, +0.0015) | | 416 |

The best extensions at 27,400 B are the same on both mains. None of them can be written in source:

| value | block | delta | why it cannot be source |
| --- | --- | ---: | --- |
| Rc strong count `%val.i.i.i.i249` (emit_cpi event_infos drop) | drop_in_place blocks | +0.0015 | library drop glue |
| holder mask `%44` (`hopt & 0xfd`) | curve-store block (bb38; bb34 on cef0574) | +0.0009 | moves the holder reload to the block top. That gives a token coincidence with the original's curve-box reload `ldxdw r3,[r10-0x8d8]`. The original stores 0xa5 before 0xa3, and that order is worse (w14a12 c_hfirst 0.62972) |
| Rent::get tag `%_234.i122` | Ok arm bb86.i | +0.0006 | the tag is a known constant there |
| clone-run owner pointers, `strong1` | Rc inc_strong abort blocks | +0.0003..0.0006 | panic paths in Rc::clone |
| `authority_bump` | past the event invoke_signed | +0.0003 (-1 slot) | inside the emit_cpi! expansion |

Three of them combined (`%43@bb34 + %_237.i116@bb86.i + %authority_bump@bb121`) add up to +0.0018 on cef0574.

The `impl` scan applies `a&&b` / `a||b` merges of any dominating dead i1 into any conditional branch, which is the
shape #3210 had (`brmerge = or %_26.i, !do_coin`). Its only gain at 27,400 B is one Rc-overflow check (+0.0006,
+2 slots). The #3210 family is used up on current main. The remaining gates either have no implied flag behind a phi,
or the merge adds an `and`/`or` and moves the size.

## pda-first partner map (the useful result)

w14a09 (#3234) showed that the holder-rewards PDA before `shared` (`pda`, plus creator-left `hL`) is the original's
front. It costs 0.07, because `cashback` takes r8 and the accounts-pointer split moves, which reshuffles the
0x3000-0x3800 clone runs. No source partner had undone that. The extension oracle on pda+hL (captured on b174038:
0.56663 @27,360) finds single extensions that do (`top-pda-b174038.txt`, `map-pda-b174038.txt`):

| extension on pda+hL | ratio | bytes |
| --- | ---: | ---: |
| none | 0.56663 | 27,360 |
| `new` Option tag (`load i8 %new`) at the post-tuple join bb26 | **0.62704** | 27,424 |
| `new` tag at validate bb72.i | 0.62543 | 27,408 |
| max_fee `%_33` at bb72.i | 0.62522 | 27,400 |
| sharing-config ptr `%_377` at bb26 | 0.62474 | 27,416 |
| curve bools `%29`/`%31`/`%35`, global ptr `%_255` | 0.620-0.624 | |
| + greedy 2nd extension (bump `%ctx.val57` at bb86.i) | 0.62992 | 27,408 |

Exact-match instructions per 0x800 orig region (`chunks-pda.txt`):

| | 0x0 | 0x2800 | 0x3000 | 0x3800 | 0x4800 | total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main b174038 | 99 | 155 | 160 | 177 | 173 | 2122 |
| pda+hL | 112 | 135 | 32 | 111 | 165 | 1890 |
| pda+hL + new tag @bb26 | **114** | 147 | **159** | **174** | 167 | 2094 |

- One live-range extension of the `new` tag across the shared/holder tuple restores the tail RA, and the pda front
  gain (+15 exact) survives.
- The tag must reach exactly the join. Extending it further, into the wallet, the sweep or the curve block, gives only
  about 0.585.
- Even with two extensions, pda stays 0.006 below main. The remaining losses are at 0x2800 and 0x4800 and in the
  +24..+48 B.

Source forms tried for these partners (all on b174038, ledger `...-b174038-fakeuse-pda-srcforms-v1`):

| form | on pda+hL | on main |
| --- | ---: | ---: |
| mf1 (`max_fee:&'g u64`, global ptr into validate) | 0.55309 @27,336 | |
| `fee_configurable:&'g bool` | 0.26489 | |
| sharing CPI passes `new` instead of `val` (`Some(_)=>..,new`; equal because validate forces `new==None` on the holder arm) | 0.43412 | 0.51225 @27,216 |
| `val.and(new)` | 0.43865 | |
| `let holder=new.is_none();` after the tuple (on the Ok path, holder <=> new is None) | 0.56339 @27,440 | 0.49641 @27,432 |
| `curve.is_holder_reward=new.is_none()` | | 0.49641 |
| `curve.is_cashback_coin=cashback&&new.is_some()` | | 0.57422 @27,296 |
| `let cashback=cashback&&new.is_some();` after the tuple | 0.46551 | 0.45926 |

Each source use of the `new` tag also moves the holder/cashback values or the CPI payload, so none of them is a pure
extension.

## Next ideas

- pda-first stays capped below main until a source form keeps the `new` tag (or max_fee, or a curve bool) live across
  the shared/holder tuple and changes nothing else. One option is a `new.is_some()` that only feeds a value already
  computed at the join, such as the tuple's `skip`/`collect_old` phi (sharing_update tag and pool_updated belong to
  tagreg).
- Combine the extension oracle with size knobs: the off-size main hits (`!holder` into bb6.i +0.0017 @27,408, ctx
  into bb39.i +0.0008 @27,408) would need a -8 B partner that is source-expressible.
- `irext.py --mode impl` is the fastest screen for any new `a&&b` implied-use idea: run it on the capture first.
