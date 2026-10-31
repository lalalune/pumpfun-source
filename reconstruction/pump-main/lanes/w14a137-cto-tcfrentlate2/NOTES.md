# w14a137-cto-tcfrentlate2: TCF program literal evaluation order (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`, line 661), pinned at 27,400 B.
Base: main ebe5387 (#3495): 1034/1035 normalized, 1034 raw, admin_cto 0.67316 / 3,123 slots, M 2,247.
Ledger approach `tcfrentlate2`, keys `0x22a10-w14-ebe5387-tcfrentlate2-*` (27 rows). This lane re-runs w14a133-cto-tcfrentlate
and w14a129-cto-tcflifeorder, which both died before writing anything. w14a133's background queue kept running after the
lane died. Its 7 results are recorded here as `tcfrentlate2-w133-*`.

All numbers come from the raw-IR capture (`capraw.py`) plus the `rx.py` opt/llc oracle. `main0` has `eq_main` true at
0.67316 / 27,400. No `measure.sh` build was run, because no form beat main.

## Result: no source change. Every evaluation-order form that moves `rent_epoch` after the accounts StorageLive collapses

w14a114 found the lead (#3512). In post-opt IR, move the first `CpiContext::new` pump_amm literal's `rent_epoch` load
(`%_60.i144`, x+32) after the first `lifetime.start` of the `TransferCreatorFeesToPumpV2` temp `_64`. That gives M 2,247 -> 2,251,
0.67436. This lane reproduced that number with `insmv`-style IR editing.

### What the lead changes (llc asm, main vs lead)

The lead changes only the spill slots of the five values in the TCF head block, `LBB0_192`, and their two reload sites
(asm lines about 1873 and 1909). No instruction is added or moved, apart from the rent/payer-key pair.

| value | orig slot | main slot | lead slot |
| --- | --- | --- | --- |
| program `is_signer` (x+40) | -0x9d8 (2520) | 2528 | **2520** |
| program `is_writable` (x+41) | -0x9d0 (2512) | 2520 | **2512** |
| program `executable` (x+42) | kept in r5, later -0x978 | 2512 | 2504 |
| program `rent_epoch` (x+32) | -0x9c8 (2504) | **2504** | kept in r5, later 2408 |
| payer key (`[r1+0]`) | -0x9e0 (2528) | kept in r5, later 2408 | **2528** |
| program owner (x+24) | loaded late (r6, then -0x970) | loaded in the first Rc block, -0x950 | as main |

So the lead is a spill-slot rotation that lines up three of the original's slots. It is not a code-shape change.
In the SelectionDAG, rent becomes chained on the `lifetime.start` node instead of the pending-load TokenFactor.
That moves it after the payer's key load, so r5 holds rent and the payer key spills first.

### Evaluation-order table (all on ebe5387, raw-IR capture + rx; main 0.67316 @ 27,400)

PROG is main's `{let x=a.pump_amm.as_ref();AccountInfo{owner,key,lamports,data,rent_epoch,executable,is_writable,is_signer}}`.
ACCTS is main's `TransferCreatorFeesToPumpV2{..}` literal.

| key | form | ratio | bytes |
| --- | --- | ---: | ---: |
| pf1 | `CpiContext{program:PROG,accounts:ACCTS,remaining_accounts:Vec::new(),signer_seeds:&[]}` | 0.67316 | 27,400 (**= main**, eq_main) |
| pf2 | `CpiContext{program,accounts,signer_seeds:&[],remaining_accounts:vec![]}` | 0.67316 | 27,400 (= main) |
| cl1 | `CpiContext{program,remaining_accounts,accounts,signer_seeds}` | 0.67316 | 27,400 (= main) |
| af2 (task a) | `CpiContext{accounts:ACCTS,program:PROG,signer_seeds:&[],remaining_accounts:vec![]}` | 0.58412 | 27,488 |
| w133-lit1 | `CpiContext{accounts,remaining_accounts:Vec::new(),program,signer_seeds}` | 0.58412 | 27,488 |
| w133-acc1 (task b) | `{let accounts=ACCTS;CpiContext::new(PROG,accounts)}` | 0.57147 | 27,328 |
| w133-acc2 | acc1 with x hoisted before `let accounts` | 0.58124 | 27,368 |
| w133-acc_fru1 | acc1 + `..*x` program | 0.57147 | 27,328 |
| def4 (task c) | `{let accs;CpiContext::new(PROG,{accs=ACCTS;accs})}` | 0.59403 | 27,296 |
| defx | def4 with x hoisted | 0.59403 | 27,296 |
| defrl | def4 + program literal with rent last (bools, then rent) | 0.60594 | 27,304 |
| def1 | `{let accs;let p=PROG;accs=ACCTS;CpiContext::new(p,accs)}` | 0.59589 | 27,264 |
| tup | `{let (p,acc)=(PROG,ACCTS);CpiContext::new(p,acc)}` | 0.59589 | 27,264 |
| tup2 | `{let t=(PROG,ACCTS);CpiContext::new(t.0,t.1)}` | 0.59589 | 27,264 |
| ctxb | `{let ctx=CpiContext::new(PROG,ACCTS);ctx}` | 0.33823 | 27,400 (frame shift) |
| w133-bindp | `{let program=PROG;CpiContext::new(program,ACCTS)}` | 0.66817 | 27,368 |
| w133-fru1 / fru4 | `AccountInfo{owner,key,lamports,data,..*x}` / `{..,rent_epoch,..*x}` | 0.67046 | 27,400 |
| w133-fru2 | `AccountInfo{lamports,data,..*x}` | 0.6348 | 27,376 |
| fru3 (task d) | `AccountInfo{owner,key,lamports,data,executable,is_writable,is_signer,..*x}` (rent read last) | 0.63252 | 27,416 (= w14a114 tp09) |
| rkey | rent right after key (first Rc block) | 0.5971 | 27,424 |
| rown / rfirst | rent before owner / `let rent_epoch=x.rent_epoch;` before the literal | 0.59739 | 27,424 |
| rmid | rent between the lamports and data clones | 0.61366 | 27,416 |

Mechanisms:
- MIR evaluates `CpiContext::new(P, A)` and `CpiContext{..}` the same way. The literal is byte-identical to main in every
  program-first field order, because both make call-operand temps: `StorageLive(_56); _56 = P; StorageLive(_64); _64 = A`.
  No program-first spelling can read a program field after `StorageLive(_64)`.
- Any form that starts the accounts before the program fails in one of two ways:
  - The accounts-first literal and `let accounts` flip the whole clone order: all eight accounts clones run before the
    program clone (+88 B or -72 B).
  - `let accs;` deferred init and the tuple temps turn `_64` into a user local, which is materialized and moved.
    Main's three 5 B tail allocas `_64.sroa.{20,21,22}.sroa.11` drop to 1 or 2 surviving 5 B allocas, out of 5 in main
    (def4/defrl 2, def1/tup 1). This costs -96 to -136 B.

  Either way the loss is 0.06 to 0.10 of ratio. The lead's chain node exists only in main's argument-temp shape.
- Inside the literal, nothing else gives a chain node between the bools and rent. The only calls are the two Rc clones,
  and putting rent after one of them is rmid / w14a114 e1. Scalar temps lose their allocas and lifetimes under SROA.
  "Rent read last" without the lifetime node is the [bools, rent, lifetime] collapse (fru3 = tp09).
- (e) Inner `program:` literal (last ACCTS field): there is no IR lead there (w14a114 irinst found only `%_60.i144`), and
  the struct's StorageLive is already before it, so its forms are not evaluation-order levers.

Conclusion: the rent-late lead (+0.0012) has no source form. It needs a chain node (store, call or surviving
`lifetime.start`) between the program flag loads and the rent load inside one block, with `_64` still an argument temp.
Rust's left-to-right operand evaluation cannot produce that without steering constructs, which the swarm forbids.

## Tools (`tools/`, experiment-only)

- `gen_evalorder.py`: writes `EDITS` files for every form above, with `WT=<worktree>` set. It anchors on line 661's
  `transfer_creator_fees_to_pump_v2(CpiContext::new(PROG,ACCTS))?;`.
- `capvar.sh <name> <edits.py> <slot>` and `runq.sh <slot> <names..>`: copy the crate, apply the edits, capture the raw IR
  and run `rx.py`. These are w14a133's, re-pathed. They need `capraw.py` and `rx.py` from w14a101/w14a114.
