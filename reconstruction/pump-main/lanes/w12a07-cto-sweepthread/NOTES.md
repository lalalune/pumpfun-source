# Lane w12a07-cto-sweepthread (wave 12, pool a)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: the sweep tail, its exit merge and JumpThreading.
Base: main 20a1ae9c0 (h1 / #2642: 27,400 B, ratio 0.43919, slots_diff 3,352). Main moved during the lane to
b5975fa67 (#2749, k4 + size knobs: 0.45147 / 3,308). Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w12a07-cto-sweepthread/`.

## Oracle (tools/)

- `capir.py --src <crate> --work <w> --out <d>` builds a scratch copy with `--emit=link,llvm-ir` (takes a build slot). On main
  the captured `candidate.so` is identical to the baseline's.
- `extract.py module.ll exec.ll` keeps only `execute`'s body (others become declarations).
- `orc.py exec.ll [--edit e.py] --name n [--ref unstripped.so]` runs v1.44 `llc -O3` on it (under 1 s) and prints
  `bytes`, the target_metric token `ratio`, `abs` (the same ratio with r10 offsets, jump offsets and frame-address
  immediates masked: a frame-agnostic structural ratio) and `opregs`. On main, `ref_equal` is true and the ratio is exactly 0.43919.
- `bsweep.py exec.ll out.jsonl`: every conditional `br` of execute at 2000:1 and 1:2000 (286 llc runs, about 70 s with J=4).
  `applyws.py in.ll out.ll i:a:b ...` applies chosen weights for greedy rounds.
- `ocalls.py <orc-name>`: call-sequence alignment of an oracle object against the original (relocation names demangled).
- `region.py <orc-name|so:path> [bucket]`: exact-token match fraction per original offset bucket (where the ratio is lost).
- `sbs.py orig_j.txt cand_j.txt lo hi`: side-by-side abstract alignment with resolved jump targets (`jr.py` makes the `_j` files).
- `runv.sh <variant> <workN>` + `variants.py`: string-replace variants of admin_cto.rs measured with measure.sh.

## Findings on main 20a1ae9 (h1)

1. **The sweep body is already in the original's order.** The call sequence from the sweep gate to the end of the native
   path (orig 0x1df0-0x3c38, 23 calls) equals the original call for call, and the post-sweep sharing/pool/event code follows
   it as in the original. Abstract (frame-masked) alignment of the sweep is near-complete. What remains in the sweep is
   register allocation in the inlined `transfer_creator_fees_to_pump_v2` AccountInfo clones (orig 0x3000-0x3800 match
   fraction 0.14, all `r`-for-`r` substitutions and spill-slot choices), and the exit merge below.
2. **Exit merge: the original threads the pre-seed sweep errors.** In the original, the `?` Err edges of
   `token_frozen(coin_creator_vault_ata)`, `token_raw_amount(coin_creator_vault_ata)` and the
   `transfer_creator_fees_to_pump_v2` CPI go straight to execute's Err return (orig 0x28d70: `ldxdw r9,[r10-0x2c8]; ja 0x28278`).
   The 648 and 660 error tails carry their own copy of the tag check (`jne r7,2 -> return; ja post-sweep`, orig 0x24eb8 and
   0x25020). Only the post-seed errors (Rent::get, ensure_rent_exempt, 719, transfer, ATA) reach the shared merge at orig
   0x26660 (`ldxdw r1,[r10-0x950]; ldxdw r6,[r10-0x8f8]; jne r7,2`). Main merges every sweep Err into `sweep.exit` (one
   `bb58.i` phi that mixes known-Err tags with the unknown `with_pubkeys`/`AnchorError::from` tags, so LVI cannot thread it).
3. **Source shape that reproduces that threading:** block-scope the 648 destination,
   `{let dest=..;if a.holder_creator_vault.key()!=dest{return Err(..)}}`. The IR then has
   `sweep.exit.thread` (preds: transfer CPI Err, both coin-ATA `?` Errs) straight to the Err return, and `sweep.exit` keeps
   the 648/660/post-seed edges, exactly the original's split. The machine code reproduces orig 0x24ee8/0x24f38/0x25068 and
   the 648 tail copy. **But** MachineBlockPlacement then chains the Err-return block right after the sweep (exit at
   +0x3fd0, orig +0x5880), so the whole post-sweep chain (sharing CPI, pool CPI, event) moves to the end of the function:
   27,776 B, ratio 0.25435. With one oracle weight (wallet executable test 1:2000) it recovers to 0.43167 at 27,552 B with
   abs 0.663 (main 0.646): structurally closer, but the layout flip costs more than the threading gains.
4. **vsigner hoist is frame-neutral but flips the same placement.** `let vsigner:&[&[&[u8]];1]=&[vaultseeds];` passed to both
   transfers stores the `{ptr,3}` element at seeds time as the original does (orig 0x24a80; main has 3 `stdw ..,0x3`, orig 2).
   Bytes 0x0-0x5000 of the function then match the original exactly as main does (identical region fractions), but the
   Err-return block again moves up to right after the sweep and the post-sweep chain goes to the end: 27,376 B, 0.32669.
   With the 306/298 weight (index 13, 1:2000) the vsig IR reaches 0.47513 at 27,400 B (main + same weight 0.47357).
5. **The skip flag.** The original's sweep gate is one spilled phi-of-constants (`[r10-0x8e0]`, 1 = skip), produced
   because JumpThreading duplicated the post-validate join per (fee None, holder) path (orig 0x23af8 holder/fee-None path
   sets r3=0 when shared). An IR-only phi-of-constants gate on main moves the post-sweep chain to the end (0.3266): the
   gate shape is tied to the validate/join threading, not to the sweep.
6. **Single-branch weight scan on main:** no sweep branch improves main; the best single weights are all in validate
   (306/298 None test 1:2000 = 0.47357, quote-locked/holder tests about 0.45). The sweep layout is at a local optimum;
   the remaining sweep differences only pay off together with a return-block placement that stays at the end.

The placement of execute's Err-return block is the bistable factor: any sweep change that adds direct Err edges into
it (threading, or fewer merges) makes MBP chain it after the sweep. The original has the threading and still places the
return near the end, so some other difference (validate/wallet frequencies) keeps it there in the original.

## Trials (measure.sh, main 20a1ae9)

| variant | bytes | ratio | result |
| --- | ---: | ---: | --- |
| main (h1) | 27,400 | 0.43919 | |
| vsig: `&[vaultseeds]` bound once | 27,376 | 0.32669 | post-sweep moves to end |
| destscope: 648 `dest` block-scoped | 27,776 | 0.25435 | original Err threading, post-sweep moves to end |
| vsig + destscope | 27,720 | 0.34753 | |
| k4 on main (control) | 27,384 | 0.4525 | reproduces k4 |
| k4 + destscope | 27,760 | 0.31245 | |

Ledger approach `sweepthread`, keys `0x22a10-w12-20a1ae9-*`.
