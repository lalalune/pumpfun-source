# w14a88-cto-sweeptagmem: sweep Result-tag test (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a72-cto-rescan304 (#3406), next ideas 1 and 2. Base: main `95a64ba75` (#3409, 0.66986, 3,204 slots, M 2,236).
Main moved from 0d04cf4 to 95a64ba before the first trial, so every number here is on 95a64ba.
Ledger approach `sweeptagmem`, keys `0x22a10-w14-95a64ba-sweeptagmem-*`.

`M` = matched tokens (SequenceMatcher over masked tokens), `ratio = 2M / (3339 + n)` with `n = bytes/8 - 88`.

## Result: wallet `!is_writable` (-8 B, +2 M) repaid by a validate volatile placeholder (+8 B, +1 M)

| | main 95a64ba | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.66986 | **0.67076** |
| M | 2,236 | **2,239** |
| slots_diff | 3,204 | **3,123** |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses, 0 gains |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | 8efdc872cdf169ae |

Change (two spellings, line count unchanged):
- wlB: wallet `if a.current_creator.is_writable==false{` -> `if !a.current_creator.is_writable{` (-8 B; on 95a64ba it is
  +2 M on its own, M 2,238 @27,392).
- vol334: `unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};` before line 334's
  `if !st.fee_configurable` (+8 B). It is the same placeholder idiom main already has after line 338.

## C0 on 95a64ba (w14a72's lead)

| variant | bytes | M |
| --- | ---: | ---: |
| main | 27,400 | 2,236 |
| **wlB** | 27,392 | **2,238** |
| smB | 27,392 | 2,237 |
| rP | 27,392 | 2,237 |
| wlB + rP / wlB + smB / smB + rP | 27,384 | 2,234 / 2,234 / 2,233 |
| C0 = wlB + smB + rP | 27,376 | 2,236 |

After #3409 the C0 lead is gone (+0 M at -24 B). wlB alone is the lead: +2 M at -8 B.

Junk map on wlB (`junkmap.py`, pure +8 B insertion): 2,239 for most slots in ours 0x6d8-0x1910 (validate error blocks) and
at 0x180-0x198, 2,238 elsewhere in the head, and lower in the sweep head (0x22c8-0x2468 is no longer the +2 region).

IR oracle `tools/volscan.py` (post-opt wlB IR, one `load volatile i8, ptr %holder_key` at the top of each of the 280 blocks):
35 blocks reach 2,239 @27,400, i.e. the junk bound. Source placements (raw-IR capture, `capvar.sh`):

| placement (validate line) | bytes | M |
| --- | ---: | ---: |
| 298 holder arm end, 306, 307, 312, **334**, 338, 339 (`Ok(target)`) | 27,400 | **2,239** |
| 283 (fn head), 289, 298 holder arm start | 27,400 | 2,238 |
| 314 | 27,408 | 2,238 |
| 296, 326 (fee Some arm head), 330 | 27,352-27,392 | 1,272-1,419 (collapse) |

334 and 338 both give 3,123 slots in measure.sh. 334 is landed.

## The angle itself: the sweep site tag test (negative)

The original re-tests the Result tag at the 648 ConstraintSeeds and 660 CtoSharedVaultFrozen sites
(`ldxdw r9,[..]; ldxdw r7,[..]; ldxdw r1,[r10-0x950]; jne r7,2,<exit 0x28278>; ja <Ok cont 0x26678>`). Ours ends the site
with `ja LBB85`, where LBB85 is the J2 copy of `sweep.exit` (`jne r7,2`) that w14a51 mapped.

| oracle (95a64ba) | result |
| --- | --- |
| raw IR: drop / widen to [0,3) the `!range` on the transpose Err tag load `%_430.0`, or drop every `!range [0,2)` in the call/transpose/`?` region | **byte-identical (eq_main)**. The range metadata does not decide the site test. |
| post-opt IR: copy the join test (`icmp eq tag,2; br bb89/err`) into one sweep exit pred (`tools/dup.py`) | 660 site: M 2,235 (-1), **slots 3,001** (-203). Shape `jeq r7,2,ok; mov64 r8,r3; ja exit` (payload register differs, so a copy is needed and the polarity flips). 648 site: 2,185 (the PDA region moves to the function end). Both: 2,184. Other preds 988-1,702. Branch weights and `ne` polarity change nothing. |
| post-opt IR: move `sweep.exit` after each of the 279 other blocks (`tools/mvscan.py`) | only the current place keeps 2,236; all others 1,702 or less. At the function end the test is copied into 648/660 and ~10 other preds (`jeq r7,2`), but the copies are 2 instructions, below tail-merge-size 3, so BranchFolder never re-merges them into the original's shared `ldxdw r1; ldxdw r6; jne` join, and MBP pulls `bb89` behind site 648 (M 1,560). |

How the original gets the site test (consistent with w14a51 section 1): early tail duplication copies a `{PHI; JNE; JMP}`
join into predecessors that end in an unconditional branch, and only when the join cannot fall through. The original's
copies then carry the reloads of two values that are live across the join (`[r10-0x950]`, `[r10-0x8f8]`), which makes the
common tails long enough for BranchFolder to merge back. Ours has neither the non-fallthrough join nor those reloads.

Source forms of the sweep Result at line 647 (raw-IR capture on 95a64ba; w14a72 already found the ConstraintSeeds error
spellings byte-identical):

| form | bytes | M |
| --- | ---: | ---: |
| f2b `match (!skip).then(..){Some(Ok(v))=>v,Some(Err(e))=>return Err(e),None=>0}` | 27,400 | = main (eq_main) |
| f4 named `Option<Result<u64>>`, then `.transpose()?.unwrap_or(0)` | 27,400 | = main (eq_main) |
| f1 `sweep(..,&mut u64)->Result<()>` | 27,360 | 2,007 |
| f7 `Option<Result<u64>>` kept by name, `if let Some(Err(_))=o{return ..}` | 27,424 | 2,058 |
| f2 `if !skip{match sweep(..){Ok(v)=>v,Err(e)=>return Err(e)}}else{0}` / f3 `is_err()` early return | 27,440 | 1,767 |
| f6 `let r:Result<u64>=if !skip{sweep(..)}else{Ok(0)}; r?` | 27,448 | 1,701 (join laid out after site 648) |
| f5 `let mut r:Result<u64>=Ok(0); if !skip{r=sweep(..)}; r?` | 26,816 | 1,560 |

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `px.py <name> <m.ll> [edits.py]`: post-opt llc-only oracle (M, bytes, slots, eq_main). Uses w14a72's `rx.py` helpers.
- `dup.py`: copy the sweep join test into one exit pred (keeps the lifetime.ends, fixes the bb89/bb67 phis).
- `mv.py`, `mvscan.py`: move one block after every other block of execute and score each placement (needs instnamer IR).
- `volscan.py`: one volatile load of a pointer at every block head (`POS=end` for block ends): the post-opt form of a
  `read_volatile` fill.
- `pair.sh`: run `capvar.sh` captures two at a time, append to `t/res.jsonl` with M.
- `dis.sh`: disassemble execute from an llc object.
