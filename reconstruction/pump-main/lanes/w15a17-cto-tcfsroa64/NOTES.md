# w15a17-cto-tcfsroa64: TCF padding allocas and accounts StorageLive (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 86e2a6b (0.67376, 3,124 slots, M 2,249 at 27,400 B; Pump Main 1034/1035 normalized and raw).
This lane continues w14a133-cto-tcfrentlate (#3615), next idea 1. Ledger approach `tcfsroa64`, keys
`0x22a10-w15-86e2a6b-tcfsroa64-<spelling>-v1` (61 rows). Every number below comes from a raw-IR capture (`capraw.py`)
followed by the `rx.py` opt/llc oracle (`eq_main` true on the unedited capture). No full `measure.sh` build was needed,
because nothing beat main.

**Result: notes only, no source change.** Both halves of the angle are closed:
1. The `_64.sroa.{20,21,22}.sroa.11` and `_56.sroa.11` allocas are **in the original too**. Removing them is a step away
   from the original bytes, not toward them.
2. No ordinary spelling moves the TCF accounts `StorageLive` between the program literal's flag loads and its rent load.
   That is the w14a133 IR lead, which is still +4 M on 86e2a6b (EWSLR 0.67496).

## 1. The four 5-byte padding allocas are original

The `[5 x i8]` allocas hold the uninitialised padding tail (bytes 43..48) of four AccountInfo values. Each value is built
in a call-argument temporary and then moved into the 664 B CpiContext. llc lowers each padding memcpy as
`ldxb/ldxw` + `stxw/stxb`. The original window has all four copies, at the **same frame offsets and in the same order** as
main:

| original (0x3a38..0x3b10) | main (0x3a28..0x3b00) |
| --- | --- |
| `[r10-0x450/-0x44c] -> [r10-0xad/-0xa9]` | `[r10-0x450/-0x44c] -> [r10-0xad/-0xa9]` |
| `[r10-0x38/-0x34] -> [r10-0x7d/-0x79]` | same |
| `[r10-0x4b8/-0x4b4] -> [r10-0x4d/-0x49]` | same |
| `[r10-0x488/-0x484] -> [r10-0x28d/-0x289]` | same |

Every spelling that lets SROA promote the pieces fully also deletes those copies. That costs 136 B and about 0.08 ratio
(table below), so main's form, with the literals passed as call-argument temporaries, is the original's form. Which four
fields carry a pad is decided by the layout and SROA slicing, not by literal versus `to_account_info()`:
`a.pump_amm.to_account_info()` and the all-`to_account_info()` TCF (s_taiall) still emit all four copies.

## 2. Spelling table (full table with lifetime events: `data/alloca-lifetime-table.md`, results: `data/results.jsonl`)

`IR pads` counts the TCF `[5 x i8]` allocas after opt. `events` is the post-opt order inside the TCF window:
L664 is the CpiContext, `L:p56` the program-literal pad, C* the Rc increments, R/E/W/S the rent and flag loads, and
`L:p20..22` the accounts pads (the w14a133 "L" unit).

| spelling | ratio | bytes | IR pads | events / note |
| --- | ---: | ---: | ---: | --- |
| main | 0.67376 | 27,400 | 4 | `L664 L:p56 C* R E W S L:p20 L:p21 L:p22` |
| t_ctxsplit `let cpi=CpiContext::new(P,A); tcf(cpi)?` | 0.33853 | 27,400 | 4 | same events; `cpi`'s lifetime.start is hoisted to the sweep head, so the frame is re-laid |
| t_tuple / t_tuplet / t_defer2 / t_allbind (the let-bound program, accounts or fields) | 0.59649 | 27,264 | **0** | pads gone, -136 B: the four original copies are deleted |
| t_defer `let accounts; tcf(CpiContext::new(P,{accounts=A;accounts}))` | 0.59463 | 27,296 | 1 | the accounts pads are gone, but the StorageLive does not move |
| t_progloc / t_allloc `{let x=..;let ai=AccountInfo{..};ai}` (program) | 0.66876 | 27,368 | 3 | p56 gone (= bindp family, -32 B) |
| t_subloc (the same, on the 3 sub-literals) / t_subbind (the accounts arg as a block of lets) | = main | 27,400 | 4 | IR-identical |
| lit2/lit3/lit4 `CpiContext{program:P,accounts:A,..}` struct literal, program first | = main | 27,400 | 4 | IR-identical (`new` is MIR-inlined) |
| gm* (struct update `..*x` on any subset of the 3 sub-literals; their tails are already RSWE) | = main | 27,400 | 4 | eq_main: a shorter spelling of the same bytes |
| gf* (fru1 program literal, with any sub-literal FRU subset) | 0.67106 | 27,400 | 4 | fru1 on 86e2a6b |
| p_tai `a.pump_amm.to_account_info()` = p_clone `AccountInfo::clone(..)` = p_KLDORSWE (declaration order) | 0.6499 | 27,416 | 4 | byte-identical to each other |
| p_KOLDREWS (key before owner) | 0.67376 | 27,400 | 4 | same metrics as main |
| p_KLODREWS / p_KLODRSWE (owner after the lamports clone) | 0.64271 / 0.6493 | 27,416 | 4 | collapse |
| p_KLDOREWS / p_KLDOEWSR / p_KLDREWSO / p_KLDRSWEO | 0.640 / 0.630 / 0.644 / 0.649 | 27,400-27,424 | 4 | collapse |
| s_tai0/1/2: one sub-literal as `to_account_info()` (ccva / pcva / accounts program) | 0.67346 / 0.66457 / 0.67196 | 27,400 / 27,392 / 27,400 | 3/4/4 | best is -1 M |
| joint grid: CPI program {literal, tai} x {literal, tai} for each sub-literal (jl*/jt*, 14 cells) | 0.644-0.67166 | | | none reaches main |
| token arm: k_createlet / k_tuple / k_ctxsplit | 0.3385-0.3388 | 27,400 | | let-bound Create or CpiContext: frame re-laid |
| token arm: k_allbind / k_subbind / k_lit2 | = main | 27,400 | | IR-identical |

## 3. Where the TCF program literal really costs: the owner load, not the tail order

- The original loads the program literal's fields in the order key, (lamports Rc), (data Rc), then E W S R **O**, all
  after the payer's lamports `add` (orig 0x26c8 and 0x2770-0x27a8). That is MachineSink's reversal of a declaration-order
  (derive Clone) IR. `p_tai` reproduces exactly this load order and position (ours 0x2698 and 0x2748-0x2788), and also
  keeps the p56 pad. So the original most likely spelled this field as `a.pump_amm.to_account_info()`, like the 8 other
  plain accounts.
- tai is 0.6499 at 27,416 B: -79 M, concentrated in chunks 0x2800 (-18), 0x3000 (-9) and 0x3400 (-30), which is the
  clone-run RA cascade of w15a07.
- Which IR difference decides it is shown by these: KOLDREWS, which loads the owner before the first Rc increment, equals
  main, while KLOD* and KLDO*, with the owner after it, collapse. **The main literal's lever is "owner loaded before the
  program Rc increments"**, worth +0.024. The tail order is worth at most 0.0027 (fru1 against main).
- `tools/perm6.py`: all 720 orders of O, R, S, W, E and L on the tai post-opt IR (`data/perm720_tai.jsonl`). The best is
  0.6501 at 27,424 B. No order inside the tail recovers tai, which matches w14a114's d1 finding.
- `tools/omove.py`: the tai owner load moved to each of 646 later positions, up to its store into the CpiContext
  (`data/omove_tai.jsonl`). None beats tai in place. Only owner-before-the-Rc-increments (main) reaches 0.67376.
- `tools/perm.py`'s 120-order table on 86e2a6b (`data/perm120.jsonl`) is unchanged in shape: EWSLR 0.67496 (+4 M),
  SLREW 0.67436 and WSLRE 0.67406, against REWSL = LREWS = main.

So main's TCF program literal is a register-allocation compensation for a residual upstream of the run. The faithful
spelling (tai) loses 0.024 until that residual is found. w15a07 showed it is not the three head live ranges
(holder_creator_vault GEP, bump, native).

## 4. Tools (`tools/`, experiment only)

- `gen.py`: generator for every spelling above. It extracts PROG/ACCTS from line 661 and the Create call from line 719,
  and writes exact-edit files.
- `alt.py <m.ll> [call-regex] [min-ctx-bytes]`, with `NTH=<k>` to pick the k-th call: the alloca/lifetime table. It prints
  the small padding allocas and the event sequence of one CPI window.
- `perm6.py`: the O/R/S/W/E/L permutation oracle on the tai IR (it needs `renum.py` and `px2.py` from w14a133/w14a114).
- `rec.py`: ledger rows from `rx/<name>/res.json` plus `alt.py`. `capvar.sh` / `runq.sh`: per-variant capture and rx queue.
- `side.py`: skeleton side-by-side of two dis.py listings.

## 5. Next ideas

- Treat tai (`a.pump_amm.to_account_info()`, 0.6499 at 27,416 B) as the faithful TCF program form. Look for the upstream
  residual that makes "owner late" collapse in ours but not in the original. The original spills O at 0x2830
  (`stxdw [r10-0x970], r6`) right after the payer clone. Ours keeps it in r0 and instead spills key and E at once
  (`[r10-0x958]`, `[r10-0x9c0]`), two stores the original does not have there.
- The IR-only rent-late lead (+4 M) stays unreachable from source. Rust evaluates `CpiContext::new`'s arguments fully, left
  to right, and every form that moves the accounts storage (let, tuple, deferred init, `let cpi`) either deletes the
  original padding copies or re-lays the frame.
