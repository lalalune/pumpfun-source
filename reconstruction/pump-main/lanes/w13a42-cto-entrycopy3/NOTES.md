# w13a42-cto-entrycopy3: entry copy of `new` after the CtoState stores (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 52c0b087c (0.62103, 3,306 slots). Continues w13a28-cto-entrycopy2 (#3103) and w13a33-cto-keyslots (#3087).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3/` (not in git). Ledger keys `0x22a10-w13-52c0b08-entrycopy3-*`.

## Result

| build | ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 52c0b087c | 0.62103 | 3,306 | 27,400 | 1034 / 1034 | |
| g5 (this PR) | **0.62403** | 3,325 | 27,400 | 1034 / 1034 | none |

Runtime differential: 363 cases, 0 mismatches. Unstripped sha256 prefix `946b912b999620b4`.

Source change (one line, newline count unchanged):

1. `let args=&(new,);` moves from before the `let (holder,..)={` block to just before `let sk=..`, after the CtoState
   literal. That is the original's copy order (CtoState stores, then `new`, then sk, then holder_key).
   Alone (m1): 0.62345 at 27,424 B (+24 B). Any position between the CtoState literal and `let sk` gives the same tokens (m2).
   Right before validate (m3) gives 0.61825 at 27,200 B.
2. The inner skip-tree tuple in (collect_old, sharing_update, skip) order (w13a30's `t_cus` gene). It is -24 B and pays
   for step 1: 0.62403 at 27,400 B.

The copy is still forwarded (no 7/9 pieces in the frame). The gain is register-allocation and frame churn from the
later `_27` lifetime.

## Mechanism: the original's 7/8/8/9 split without validate reading the copy

w13a28 found the split only when validate reads the copy. The raw-IR oracle here (`x/`) shows why the split happens and that
validate does not need to be involved:

- The 7/8/8/9 split is the layout of a `Result<Pubkey>` / niche `Result<Option<Pubkey>>`. The tag is at 0, the payload is at
  1..33, and the Err `{i64,ptr}` is at [8]/[16]. Any alloca that the copy is memcpy'd into, and that has i64 accesses at
  [8]/[16], makes SROA split the copy 1/7/8/8/9.
- **xs**: the sharing arm's `_59 <- _27` copy is rewritten piecewise (i8 tag, 7 B memcpy, i64 [8], i64 [16], 9 B memcpy).
  Validate is not touched and nothing writes `%new`. The entry then shows the original sequence
  (`ldxw [+4]/[+1] -> -0x655/-0x658`, `ldxdw [+8]`, `ldxdw [+16]`, `ldxb [+0x20]/ldxdw [+0x18] -> -0x660/-0x668`), at the
  original's piece offsets. The split itself stops the copy-from-constant forwarding, so no write to `new` is needed.
- It still loses. All oracle numbers are on 52c0b08 (main 0.62103) and on v1 (0.55254):

| oracle | main | v1 |
| --- | ---: | ---: |
| xs: split only (copy before CtoState) | 0.52548 @27368 | 0.5221 @27376 |
| xsc: split + memset(%new) after validate | 0.5323 @27496 | 0.52204 @27536 |
| xcl: clobber only | 0.54074 @27400 | 0.49948 @27392 |
| xsm: split + copy after CtoState (before sk) | 0.55774 @27408 | 0.52848 @27368 |
| xm: copy after CtoState, no split | 0.62345 @27424 | 0.55254 @27360 |

- Stack reloads: original 537, main 509, xm 505, xs 493, xsm 511. The faithful split does not add the missing pressure,
  and entry copy + v1 never beats main. **Blocker:** the split pieces are only worth having once whatever else raises the
  original's register pressure (~30 more reloads) is reproduced. Copy and v1 both lower pressure on our build.

## Source carriers tried (all on 52c0b08)

| trial | form | result |
| --- | --- | --- |
| t1 | `Some(Ok::<_,Error>(args.0)?)` | byte-identical (MIR folds to ControlFlow::Continue) |
| c1/c2 | plain `fn pass(n)->Result<Option<Pubkey>>{Ok(n)}` at entry / in sharing arm | byte-identical (MIR-inlined) |
| k1/k5 | `#[cold] fn pass` at entry | execute collapses to 9,064 B (the cold call makes the rest cold) |
| k2 | `#[cold] pass` in the sharing arm | 0.52196 @27360 |
| t3/t4/c5 | `mut new` + `new.take()` into validate (a real write to %new) | copy kept but unsplit (4 unaligned ldxdw), 0.54417 @27416 |
| t5/v1 | validate takes holder_key:Pubkey by value | 0.55254 @27360 |
| t2 | plain `let (holder_key,_)=PDA` | 0.54793 |

Size-compensation combos (m1 + genes30): t_cus 27,400/0.62403; t_cus+e_reset or u_sand 27,392/0.62412;
e_reset+u_sand 27,408/0.62423.

## Next ideas

- A source construct with an i64 [8]/[16] use of the sharing payload that survives MIR. A non-cold, non-leaf helper
  returning `Result<Option<Pubkey>>` is the remaining carrier (leaf helpers are cross-crate-inlinable and MIR-inlined).
  It only pays together with a pressure source.
- On g5, m1+e_reset+u_sand is 0.62423 at 27,408 B: an -8 B neutral knob would give about +0.0002.

## Tools

`tools/capvar.sh` (now reads a pristine `basecrate` copy), `runq.sh`, `rec.py`: w13a28's raw-IR capture + rx oracle.
`x/xc.py` holds the IR edits (piecewise split `SPL`, `clob`, `mv`/`mv2` copy moves).
