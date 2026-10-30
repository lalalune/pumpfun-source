# w13a49-cto-colderr: colder sweep Err edges, the sweep-exit join and the skip gate

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 52c0b087c (0.62103, 3,306 slots). The raw IR of w13a42's main capture (`ir/main.ll`) reproduces it
exactly through the w13a23 `rx.py` oracle (`eq_main: true`).
Angle: continue w13a36 (#3133) cause 2 and w13a31 (#3073) idea 1. Find a source construct that makes the
transfer_vault_tokens / sweep-exit Err edges colder, so that the skip path can join the sweep Result {2,0}
before the `?` tag test without the MachineBlockPlacement relayout. The aim was to coalesce `swept` with the Err
payload in r9, as in the original.
Ledger keys: `0x22a10-w13-52c0b08-colderr-*`.

## 1. Correction: the original does not join the skip path before the tag test

The premise of cause 2 does not hold. Jump-target tables of the original window (`orig.ann`) against main show:

| what | original | main |
| --- | --- | --- |
| skip gate | `0x1d28 mov r9,0` (swept = 0), `ldxdw r6,[0x8f8]`, `ldxdw r1,[0x8e0]`, `0x1d40 jne r1,0,+0x3e4` -> **0x3c68**: past the `0x3c60 jne r7,2` tag test, with sweep as the fallthrough | `0x1d10 mov r2,0`, `jne r9,0,+1` (sweep), `ja` -> 0x3bf8: also past the tag test (`0x3bf0`) |
| `mov r9,0; mov r7,2` sites (0x2148, 0x5e70) | token-arm `amount==0` Ok(0) paths **inside** the sweep (`jeq amount,0` -> 0x3c58), not the skip path | same paths: `mov r2,0; mov r7,2; jeq r9,0` -> copy B (0x60b0) |
| sweep-exit join | one test block: 0x3c50 (`ldxdw r1,[0x950]` holder phi slot; preds 0x3bb0, 0x62f8, 0x6388, 0x63b0 plus the Rent `::from` fallthrough), 0x3c58 (`ldxdw r6,[0x8f8]` sharing tag; 6 preds: amount0 x2, native Ok, native Err, native amount0, token `require!` `::from`), 0x3c60 `jne r7,2` -> 0x5868 (global Err exit, payload r9) | two copies of the test: copy A after the Rent `::from` (0x3bf0, `jne r7,2` -> `mov r8,r2` -> exit), copy B at 0x60b0 (the same 6 preds plus transfer_vault_tokens Ok) |
| transfer_vault_tokens Ok | threaded past the test: `0x60d8 mov r9,r6; ldxdw r6,[0x8f8]; ldxdw r1,[0x950]; ja 0x3c68` | to copy B (`jeq r1,2` -> `jne r7,2; ja`) |
| with_pubkeys Err (0x24a8), token `::from` (0x2610) | their own duplicated tests (`ldxdw r1,[0x950]; jne r7,2,exit; ja 0x3c68`) | to copy A |

The original gate is `if skip {..} else {sweep}`: the IR branch is `br skip, post, sweep` (BPF cannot reverse a
branch, so `jne skip,0 -> post` with sweep falling through shows the IR polarity). Ours branches on the sweep flag
(`br sweep_on, sweep, post`). n11 (skip joins {2,0} before the test) is therefore not the original's form. Colder
Err edges that keep the MBP layout under n11 would only chase a proxy.

## 2. The Err payload in r9 comes from the holder phi (cause 1), not from the skip join

`tools/payreg.py` counts the Err-site payload register (`ldxdw rX,[r10-..]; ldxdw r7,[r10-..]` pairs):

| build (llc oracle, main 52c0b08) | bytes | ratio | fm | sk | payload |
| --- | ---: | ---: | ---: | ---: | --- |
| original | 27,400 | | | | **r9 x20** |
| main | 27,400 | 0.62103 | 0.7121 | 0.8544 | r8 x20 |
| n11 (skip joins {2,0} before the test) | 27,184 | 0.50414 | 0.60881 | 0.72973 | r8 x20 |
| n11 + `bw:bb23.i:20:1` (validate weight, w13a36's best) | 27,360 | 0.60381 | 0.73452 | 0.85624 | r8 |
| n5h (holder = phi of constants at the shared/holder join, w13a36 e5h) | 27,384 | 0.58556 | 0.70063 | 0.85046 | **r9 x20** |
| n5hp (n5h + pool CPI holder from the phi) | 27,376 | 0.59014 | 0.69744 | 0.85029 | **r9 x20** |

The holder phi alone moves all 20 Err sites to r9. The swept value itself stays in r2 and is spilled (`0x968`) in
n5hp, so the r9 value/payload coalescing still needs the holder phi plus the original join. **The holder phi is the
lever. w13a38-cto-cbflagphi works on its source forms; use the 20-site r9 count as a quick check that a candidate
has the original holder representation.**

## 3. Edge coldness with source-reachable weights

`bwfm.py sweep` (w13a31) over the 23 sweep-region branches (gate `bb32`, the sweep blocks, `sweep.exit`), with the
weights source can produce: 20:12 / 12:20 (zero/pointer heuristic, memory-bool tests) and 16:1 / 1:16 (cold call):

| base | best at 27,400 B | note |
| --- | --- | --- |
| main | `bw:bb32:20:12` (= `bb10.i89:20:12`, `bb13.i92:16:1`, `bb66.i95:20:12`) 0.62133 (+0.0003), fm 0.7118 | **proxy**: it moves the native ensure_rent_exempt Err payload block `[0x838]` and swaps the `[0x768]`/`[0x808]` blocks **away** from the original tail order, which main already has |
| main | `bw:bb106.i:12:20` / `1:16` 0.62152 at 27,384 B | transfer_vault_tokens Err made **hotter**, not colder |
| n5hp | best fm `bw:bb32:20:12` 0.58633 @27,368 (fm 0.70054); best plain `bw:bb13.i92:16:1` 0.59032 @27,360 | no sweep-edge weight repays the holder phi's clone-run frame cost |

Every colder-Err weight on the tvt/create_idempotent/native Err edges is byte-identical to its base or worse.

## 4. IR structure probes (main 52c0b08)

| probe | change | bytes | ratio | fm | sk |
| --- | --- | ---: | ---: | ---: | ---: |
| t1 | thread the transfer_vault_tokens Ok edge straight to the post-test block (orig 0x60f0) | 27,392 | 0.31131 | **0.7164** | 0.85453 |
| t1 + n5hp | | 27,344 | 0.2996 | 0.69846 | 0.8505 |
| t2 | one sweep return join (Ok/Err cleanup lifetime.ends moved into sweep.exit) | 27,376 | 0.5242 | 0.60962 | 0.72981 |
| g1 | gate as a skip-polarity phi, `br skip, post, sweep` (the original's 0x1d40 form) | 27,392 | 0.62082 | **0.71251** | **0.85483** |
| inv:bb32 | sweep-flag polarity inverted (`jeq r9,0`) | 27,392 | 0.62082 | 0.71221 | 0.85423 |
| g1 + n5hp | | 27,496 | 0.4674 | 0.52751 | 0.65012 |

t1's plain loss is a frame reshuffle: the args spill to 0x948/0x918/0x928/0x968 against main's 0x910/0x8e0/0x8f0/0x930.
g1 no longer collapses on this main (w13a08 saw it collapse on 74b3171). It is the original gate, -8 B, and above main
on fm and sk.

## 5. Source trials (raw-IR capture + rx oracle, = identity build)

| trial | change | bytes | ratio | fm | sk | note |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| c1 | `transfer_vault_tokens(..).map_err(cold_e)?`, `#[cold]#[inline(never)] fn cold_e(e:Error)->Error{e}` | 27,432 | 0.55928 | 0.71168 | 0.85329 | +1 call (158 vs 157), new fn: not landable; payload r8 |
| c2 | c1 + `transfer_native(..).map_err(cold_e).map(..)` | 27,464 | 0.56224 | 0.71035 | 0.85248 | +2 calls |
| s1 | `swept=if skip{0}else{sweep(&ctx,&holder_key)?};` | 27,384 | 0.53132 | 0.62032 | 0.74019 | gate is the original `jne skip,0 -> post`, but MBP swaps the post-sweep chunk and the error/native/token chunk (w13a31's lv3 swap) |
| s2 | `skip.then_some(0).map_or_else(\|\|sweep(..),Ok)?` | 17,416 | 0.22455 | | | sweep no longer inlined |

## Tools

- `tools/ed.py <m.ll> <edit.py[,edit2.py..]> [spec] [--keep DIR]`: apply `edit(fn_text)` IR edits to execute's post-opt
  IR, then w13a31 `bwfm.py run` (plain, fm, sk, errseq). It needs w13a31 `bwfm.py`, w13a26 `bwx.py` and w13a18
  `absratio.py` next to it.
- `tools/payreg.py <ann>..`: Err-site payload register counts (original r9 x20).
- `edits/n5.py` (w13a36 e5/n5 adapted to 52c0b08 names, `E5=h|hp|c..`), `edits/t1.py`, `edits/t2.py`, `edits/g1.py`.
- `src_edits/*.py`: `EDITS` lists for w13a23 `capvar.sh`.

## 6. Wave 14 continuation on main 53abf28b1 (0.62672, 3,305 slots, fm 0.72588, sk 0.8541)

The lane died at ~19:30 UTC in wave 13. Its last batch (k1-k8: s9 plus size knobs on 52c0b08) peaked at 0.62013
(below that main's 0.62103), and s9 already collapsed on 6ff770f (n9 0.4779). Re-measured on 53abf28 with the raw-IR
capture + rx oracle (`eq_main: true` for the unmodified capture):

| trial | change | bytes | ratio | fm | sk |
| --- | --- | ---: | ---: | ---: | ---: |
| m3 | main capture | 27,400 | 0.62672 | 0.72588 | 0.8541 |
| m3s9 | `swept=if skip{Ok(0)}else{sweep(&ctx,&holder_key)}?;` | 27,392 | 0.4794 | 0.51925 | 0.65169 |
| g1m3 | IR skip-polarity gate phi (`edits/g1m3.py`) | 27,392 | 0.4794 | 0.51925 | 0.65228 |
| g1m3 + `bw:start:16:1` (or `bb1:16:1`) | | 27,240 | 0.61899 | 0.71454 | 0.85427 |
| g1m3 + `bw:bb31:20:12` (gate) | | 27,360 | 0.53485 | 0.64998 | 0.82027 |

The collapse moves the 753-insn sweep token-arm chunk (main 0x2478-0x3dd0) after the post-sweep code. A
588-run weight sweep over g1m3 (`sw_g1m3.jsonl`) restores the layout (sk 0.854) only with weights at the function head
(`start`/`bb1`, the #3168 `shared` && chain; `global_quote`; `bb15`), never with sweep-edge or gate weights. The
skip-polarity gate is therefore a whole-function block-frequency near-tie that #3155/#3168 tipped. It is not a
sweep-edge coldness problem, and no single weight brings it above main.

Source-reachable weights on main (`bwfm.py sweep`, 147 branches x {20:12, 12:20, 16:1, 1:16}, `sw_m3.jsonl`):

| spec | bytes | ratio | fm | what |
| --- | ---: | ---: | ---: | --- |
| `bb10.i98:20:12` / `bb66.i104:20:12` | 27,400 | 0.62732 | 0.72558 | amm-arm token_frozen Ok / `require!(token_raw_amount(..)?==0)` pass made likely |
| `bb106.i:16:1` | 27,400 | 0.62732 (3,370 slots) | 0.72558 | transfer_vault_tokens Err colder (this lane's original lever) |
| `bb18:1:16` | 27,352 | 0.62759 | 0.72504 | |
| `bb79.i:12:20` (best fm) | 27,400 | 0.62223 | 0.73397 | to_string unreachable edge, not source-reachable |

The +0.0006 entries lower fm, so they are positional proxies, and none of them is reachable from source:
- q1/q5 `.map_err(#[cold]|e|e)` on transfer_vault_tokens / transfer_native, q2 `if let Err(e)=..{return Err(e);}`,
  q3 `match ..{Err(e)=>return Err(e),Ok(())=>{}}` are byte-identical to main (the cold closure is inlined and its
  attribute is gone before BPI).
- q4/q6 (`map_err(#[cold]..)` on token_frozen / the amm token_raw_amount) grow execute to 27,608 B (0.30115 / 0.525).
- r1-r4 (`x<1`, `x.leading_zeros()==64`, `x.checked_sub(1).is_none()`, `x.count_ones()==0` in the amm `require!`)
  are byte-identical: InstCombine folds each back to `icmp eq x,0`, so the zero heuristic stays 12:20.
- A real cold call (c1/c2) adds a call and a function (not landable). `core::intrinsics::unlikely` cannot reach LLVM
  on 1.79-dev (y1-cto-llvm ledger row).

Conclusion: edge coldness is exhausted as a lever for admin_cto on current main. The Err-payload r9 / swept
coalescing belongs to the holder phi (section 2) and the coalescer block order (w13a40/w13a44, #3149/#3164). The
skip-polarity gate needs a head-of-function frequency change that source cannot express without losing elsewhere.
