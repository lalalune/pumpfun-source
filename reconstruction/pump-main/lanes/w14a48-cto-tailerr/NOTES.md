# w14a48-cto-tailerr: sweep head / 648 / 719 / tail error regions of admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Bases: main 28ab23a (0.65488, 3,280 slots), then 0fbf8da (0.65578).
Angle: clean-room rewrites of the four small regions in w14a38's map: (a) sweep head 0x1d30-0x2300, (b) tail error blocks
0x5570-0x5a80, (c) 648 ConstraintSeeds 0x2330-0x2478, (d) 719 frozen/raw_amount 0x2498-0x26e8.
Ledger approach `tailerr`, keys `0x22a10-w14-28ab23a-tailerr-*` (one duplicate set under 0fbf8da; see the correction row).

## Result: no gain. Every source spelling in the four regions is either byte-identical to main or loses

Raw-IR capture + rx opt/llc oracle (m0 reproduces main exactly on both bases):

| variant | what | bytes | ratio |
| --- | --- | ---: | ---: |
| r660if / r660amt | 660 as `if raw!=0{return err!(..)}` / `let raw=..;require!(raw==0,..)` | 27400 | = main (identical) |
| ammmatch | `amm_frozen=match empty{true=>false,false=>token_frozen()?}` | 27400 | = main |
| r719nest | 719 as `if frozen{if amount!=0{return Err(..)}}` | 27400 | = main |
| d648ne | `key().ne(&dest)` | 27400 | = main |
| d648not | `!(key()==dest)` | 27504 | 0.44371 |
| h1/h2/h3 | 648 check in an inline(always) fn / closure / plain fn + `?` | 27632 | 0.36963 (all three identical) |
| ds1 | `{let dest=..;if ..{return Err}}` (dest block scope) | 27448 | 0.51751 |
| g9 / g9ds | skip-polarity gate `if skip{Ok(0)}else{sweep()}?`, alone / + ds1 | 27424 / 27480 | 0.49828 / 0.45947 |
| p1, p1ds, p1g9, p1g9ds | PDA-first head (w14a38 p1) + ds1 / gate | 27344-27496 | 0.5716 / 0.46053 / 0.5719 / 0.46053 |
| j1 / j2 (+ds) | sweep Result bound first, pool bump read before the `?` | 27400 / 27448 | 0.65368 / 0.55672 (0.516 / 0.454) |
| b1 / b2 | bump read first in sweep / `old` key read first | 27400 | = main / 0.59377 |
| n1 / n2 / n3 (+ds) | native arm `E?;T?;Ok(amount)` / `T.map(|()|amount)` else `Ok(amount)` / `amount==0` early return | 27424 / 27408 / 27480 | 0.3764 / 0.65329 / 0.37601 (ds: 0.50) |
| n5 (+ds) | `Rent::get()?.minimum_balance(0)` | 27400 | = main (ds = ds1) |
| rm1 / rm2 (0fbf8da) | `match Rent::get(){Ok(r)=>..,Err(e)=>return Err(e.into())}` | 27352 | 0.64858 / 0.64888 (main 0.65578) |

## What the four regions actually differ in (tools/tags.py on orig vs main)

1. **Register assignment, not spelling.** (a)/(c)/(d) rm misses come from one chain: the original spills
   `&a.holder_creator_vault` (accounts+0x108) to [r10-0x8e0] right after the seeds memcmp, keeps the bump in r7 (spilled
   [0x910]) and native in r9 (spilled [0x918]), adds 0x48 to the accounts register in place, and carries the sweep
   Result payload in r9. Ours keeps the vault pointer in r6 (spilled late at [0x9b8]), the bump in r9, the payload in r3.
   Every error block in the sweep then differs by its payload register (`ldxdw r9,[..]` vs `ldxdw r3,[..]`).
2. **Jump threading of the sweep Err edges.** The original threads the TCF `?` Err (orig 0x3ba0) and the amm
   token_frozen / raw_amount `?` Errs (orig 0x2528/0x2658 -> 0x6360) straight to the execute exit, and its 648 and 719
   error blocks carry their own copy of the outer `jne r7,2` test (orig 0x24a8, 0x2610). Ours sends all of them to the
   sweep join. The blocker is `lifetime.end(dest)` in the sweep early-return StorageDead chain (raw bb57): dropping it
   (IR `edits/x1.py`, or source ds1) gives exactly the original's threaded set (re-confirms w13a27-cto-seedsrpo on the
   current main) but MBP then lays the post-sweep chain after the tail: 0.48758 @27448 (0.48967 on 0fbf8da).
3. **The threaded skeleton does not beat main even with a perfect layout.** New llc-only block-move oracle
   (`tools/bmove.py`, `tools/scan.py`, 0.3 s per variant): on x1, moving `bb53.i111` (the token/native Err StorageDead
   merge) after the native-arm blocks, right before `sweep.exit`, restores the layout and gives a tag-test skeleton equal
   to the original's except the native tail-dup copy and the orig 0x60c8 TVT Ok thread: **0.61674 @27408** (0.61884 on
   0fbf8da). The best of 3,360 second moves on top of it is 0.62723 @27408. So the orig-shaped threading costs ~0.03 against
   main through RA/frame changes, and no block order of it gets to main. In the raw IR the native-arm blocks (bb86/bb30/
   bb90, Rent continuation) sit after the drop chain because a MIR pass appends them; the explicit-match Rent::get forms
   (rm1/rm2) change that but lose 48 B and 0.007 on their own and collapse with ds1 (0.47739).
4. (b) tail error blocks: the call sequence is equal; misses are the payload register (orig r1 then `mov r9,r1`, ours r8)
   with the orig tail-merging the second Rc drop into the previous block's `mov r9,r1; ja`, and the native
   saturating_sub register choice (orig result r6/min r3, ours result r3/min r6). Register-level only.

## Tools (experiment only; paths point at this lane's $OUT)

- `tools/capvar.sh`, `tools/rec.py` (w14a38's capture + recorder, repointed), `tools/batch.sh` (two captures at a time).
- `tools/tags.py <fn.bin>`: every `r7==2` Result tag test with its targets (orig/candidate threading map).
- `tools/bmove.py <m.ll> <tag> BLOCK@BEFORE ...`: post-opt block-order oracle, llc only, ~0.3 s.
- `tools/scan.py <m.ll> <jobs.tsv> <out.jsonl>`: parallel (3) block-move scans.
- `tools/ocalls.py <rx dir> [lo hi]`: calls by window offset in an rx object; `tools/rgn.py`: slice of a win.py diff.
- `edits/`: every source edit screened here (EDITS lists for capvar.sh).

## Next ideas (not tried)

- An RA-level lever for the vault-pointer spill: the original never keeps accounts+0x108 in a register. A source form in
  which `&a.holder_creator_vault` is re-derived from `ctx.accounts` at each use (ensure_rent_exempt, transfer_native,
  create_idempotent authority) instead of being one SSA value; needs a form MIR/LLVM GVN does not merge.
- Threading combined with an RA fix: bound 0.627 by layout alone, so threading only pays together with a register fix.
