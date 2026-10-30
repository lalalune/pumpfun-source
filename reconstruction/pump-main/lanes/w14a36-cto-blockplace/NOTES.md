# w14a36-cto-blockplace: call-skeleton displacements and a placement-only block-move oracle

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 06967d3 (0.64649) → 81d3d9a (0.65069) → faf9962 (0.65129). Ledger keys `0x22a10-w14-<sha7>-blockplace-*`.

**Result: no zero-loss source change. One placement lever is worth +0.0075 (E334), but its mechanism is a split
fee-Some exit block that the original gets from register-allocation edge copies; no source spelling tried (36)
reproduces it without a bigger loss elsewhere.**

## Call skeleton (157 calls, absolute callee targets; `tools/dis.py`, `tools/lcs.py`, `tools/errs.py`)

Decoding the real call immediates (the `win.py` diff prints the original's imm on matched lines) and taking an LCS
over absolute callee addresses gives 146/157 matched calls. The per-site map with error line/code is in
`callmap-06967d3.txt`. The displacements from the angle, resolved:

| id | original | ours | callee / site | source | verdict |
| --- | --- | --- | --- | --- | --- |
| P | +0xf8 | +0x220 | `find_program_address` (holder_key PDA) | line 339 | excluded (RA-limited, #3234/#3227) |
| A | +0xf20 lone `From` | +0x10e8 (`name`+`fmt`+`From`) | E306 `CtoNewCreatorNotAllowed`-group | 306/312/307 to_string split | excluded group (#3223/#3166/#3224); the original hoists 306's inlined to_string before the 3 memcmps and outlines 312/307, ours hoists 312's |
| B | +0x1730..0x17f8 (`name`,`to_string`,`From`) | after the 410 block | E334 `CreatorFeeNotConfigurable` (6077) | line 334 | **+0.0075 placement bound**, RA/structure-limited (below) |
| C | +0x4be8 `memcmp`, +0x4c10 `data_is_empty` | swapped | pool gate `pool_updated` | line 761 | owner-first is the original call order but costs -0.0018 (RA renaming r6/r7/r8), re-screened 12 forms |
| D | +0x5110 `clone` | 0x40 earlier | uniform shift after C | - | no separate block; follows C |

## Placement-only oracle (`tools/blkscan.py`, `tools/mvblk.py`, `tools/asmscore.py`)

`llc -filetype=asm` of rx.py's slimmed post-opt module → move one block (or one fallthrough chain) to another
point where nothing falls through → `clang -cc1as -triple sbf +store-imm,+jmp-ext` → rx metric. The unedited asm
round-trips to the exact build (`eq_main: true`), ~0.2 s per variant. Registers and frame stay fixed, so a result is
the most that moving only that block can be worth. `blkscan.py m.s out.jsonl --chains -j 4` tries every chain at every
legal insertion point (110 chains x ~110 points, 2.5 min on 4 cores). Full table: `chainscan-81d3d9a.json`.

| chain (IR block) | error line | best insertion | ratio delta |
| --- | --- | --- | ---: |
| `LBB0_64` (`bb59.i`) | 334 | before `bb76` (right after E338, the original's +0x1730) | **+0.00749** |
| `LBB0_39` | 306 | before `bb76` | +0.00359 |
| `LBB0_40` | 312 | before `bb76` | +0.00270 |
| `LBB0_341` (`bb81.i`, wallet `token_frozen ?`) | - | before `LBB0_334` | +0.00090 |
| `bb76`, `bb19`, `bb63.i` | - | | +0.0003 each |
| all other 103 chains | | | <= 0 |

After E334 is moved, 306 and 312 drop to +0.0009 / 0, so the whole placement-only ceiling is about +0.009.
On faf9962 the E334 move is 0.65129 -> 0.65878 (3,115 slots).

## Why E334 is placed after the 410 block (debug llc `-debug-only=block-placement`)

`~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc` produces the same object and logs MachineBlockPlacement.
BPF conditional branches are unanalyzable, so every conditional block is pre-merged with its ISel fallthrough
(`bb54.i -> bb58.i -> bb66.i(E338)`). When the E338 chain ends, MBP takes the hottest ready block from the worklist:
`bb76` (the post-validate join; freq .039 = fee-Some exit + both fee-None exits) beats E334 (freq .0092).
In the original the fee-Some exit is its own block (+0x1800: `stxdw [r10-0x918],r4; stxdw [r10-0x948],r3;
mov64 r7,1`, one predecessor). Its frequency (~.0077) is below E334's, so E334 comes first, then the split block.

IR proof (`tools/dup76.py`): giving the `bb58.i` edge its own copy of `bb76` reproduces the original order
`330 338 334 410` (0.64403 @27,480; +80 B for the duplicated target-piece memcpys). The original's split block holds
spill copies and the fee-tag phi constant (`r7=1`, used for the line-757 `if let Some(f)=fee` store), so it comes from
register allocation, not from the CFG.

What does not split the edge:
- a phi-of-constants fee tag at `bb76` replacing the line-757 test (p1). The copy is hoisted into `bb58.i`: 0.57036,
  and the order is unchanged.
- `-phi-elim-split-all-critical-edges`: the split blocks are empty and get folded.
- sinking the target memcpys below the shared test (t1 IR): 0.64572 @27,464, order unchanged.

## Source screens (raw-IR capture + rx opt/llc oracle = build tokens; `edits/*.py`, `tools/batch.sh`)

- 334/338 spellings (b1-b15): `if c{}else{..}`, `require!`, else-if chain, `match bool`, `!(..)`, ranges,
  `wrapping_sub`. They are byte-identical, except `==false`/`!=true`/`(!c)==true`, which give 0.6437-0.6395 @27,408 with
  order `330 410 334 338`.
- fee match forms (n1-n8): None-first arm, `if let`, `let..else`, `_=>{}`, `None=>()`. They are byte-identical or
  lose (0.635 / 0.550).
- validate returns the fee as `Option<u64>` rebuilt per arm (f1-f3): 0.336 (frame shift), order unchanged.
- validate result through a local, target assigned per tree arm (t1-t5, t6-t10): t2/t4 do give errseq `330 338 334 410`
  but cost 0.38 (frame +8/16 B, fm 0.637 vs 0.698, sk 0.741 vs 0.789); the rest are unchanged or lose.
- pool gate owner-first (c1-c14): 0.6466-0.64949, all below main.

## Tools

- `tools/blkscan.py <m.s> <out.jsonl> [--chains] [--blocks L1,L2] [-j N]`: placement-only block/chain move scan.
- `tools/mvblk.py in.s out.s LABEL BEFORE_LABEL`, `tools/asmscore.py x.s`: a single move, and scoring.
- `tools/llcscore.sh m.ll [llc args]`: llc → asm → score plus error-site order (`tools/eord.py`).
- `tools/dup76.py`, `tools/irmv.py`: post-opt IR join-duplication / block-order edits.
- `tools/fm.py fn.bin..`: ratio / frame-masked / skeleton ratio; `tools/chunks.py a b [n]`: per-original-chunk matches.
- `tools/capvar.sh`, `tools/capraw.py`, `tools/rx.py`: the w14a30 raw-IR oracle, repointed to this lane.
- `tools/dis.py`, `tools/lcs.py`, `tools/errs.py`: absolute-callee call streams, LCS, and the per-site error map.
