# Lane w13a14-cto-region2of3: admin_cto::execute region 2 of 3

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: split the original window into 3 equal byte ranges and own range 2, original relative offsets
`+0x23b0..+0x4760` (slots 1142..2283), then rewrite only the statements that produce it.
Bases: main 8f050a236 (#2921, 0.50929) and 74b31714a (#2933, 0.51348).

Everything here is notes and experiment tooling. No source change is proposed.

## What region 2 is (statement map)

Calls of the original in the range, in layout order (relative offsets):

| orig rel | call / block | source statement (line) |
| --- | --- | --- |
| 0x23c0-0x2488 | `From<AnchorError>`, `Error::with_pubkeys` | sweep dest check, ConstraintSeeds (648) |
| 0x24d0 | `token_frozen(coin_creator_vault_ata)` | `amm_frozen` (649) |
| 0x2518-0x25f0 | `token_raw_amount`, `PumpError::name`, `to_string`, `From` | 660 `require!` (CtoSharedVaultFrozen) |
| 0x2648 | `token_frozen` | 661 `else if !data_is_empty()` arm |
| 0x26e0-0x3b70 | 12 inlined `AccountInfo::clone` runs, then `transfer_creator_fees_to_pump_v2` | 661 transfer CPI (658 instructions, no calls) |
| 0x3bd0-0x3c38 | `Rent::get`, `From<ProgramError>` | 663 native arm |
| 0x3c40-0x4760 | sweep-exit `?` test, sharing payload `val` copy, 8 clone runs of the sharing CPI | 745-749 (the CPI call itself is at 0x4a78, region 3) |

The native/token sweep tail (`minimum_balance`, `ensure_rent_exempt`, `transfer_native`, `create_idempotent`,
`transfer_vault_tokens`) is in region 3 (0x59c0+), after the post-sweep code, in both builds. The call
sequence and the clone order of both CPIs in region 2 already equal the original.

## Where region 2's distance is (tools/segstat.py, main 74b31714a)

Matched tokens of region 2 (1,267 original tokens), plain and with registers and/or frame offsets masked:

| plain | regs masked | frame masked | both masked |
| ---: | ---: | ---: | ---: |
| 582 | 829 | 796 | 1,162 |

So 92 % of region 2 already has the original's shape. The rest is register allocation and frame
offsets, mostly spill slots:
- the transfer-CPI clone run (orig 0x2800-0x3400) spills the cloned fields to slots 8 B away from the
  original's (`[r10-0xb18]` vs ours `[r10-0xb20]`, ...), and keeps the accounts pointer in r6 instead of
  reloading it from `[r10-0x8d8]`;
- 0x3400-0x3800 is frame-only (plain 63/128, frame-masked 124/128).

## Mechanism 1: the sret-demotion slots of region 2/3 are exactly +3 ranks and +8 B off

`tools/sretbound.py` pairs the 33 sret-demotion slots by call layout position. Layout position -> (orig
rank / our rank), main 74b31714a:

```
1/7 2/1 32/32 3/10 7/6 29/3 30/4 31/5 4/2 5/8 6/11 8/12 9/9 19/22 15/18 16/19 17/20 18/21 22/25 25/28
26/29 27/30 28/31 0/0 14/17 23/26 24/27 10/13 20/23 21/24 11/14 13/16 12/15
```

- Every site from layout position 13 on (all of region 2 and 3) is the original's rank + 3. The three
  extra early ranks are layout positions 5-7 (orig ranks 29-31, ours 3-5): the validate `to_string` error sites
  (312/307/306). In the original they come last in RPO (w12's "... | 312 307 307wp 306"); ours visit them early.
- The whole sret block is also 8 B deeper in ours (orig 0x6d0 + 16·rank, ours 0x6d8 + 16·rank), because the
  IR-alloca area above it is 8 B larger (mint key at `[r10-0x6c8]` vs the original's `[r10-0x6c0]`).
- Bound: remapping our sret offsets to the original's slots gives 0.51348 -> **0.52996** (whole window),
  but only +10 tokens in region 2. Region 2's frame residue is spill slots, not sret slots.
- The fix therefore lives in region 1 (validate's RPO order, w13a06-cto-rpoorder) plus 8 B of IR-alloca area
  (the frame lanes). No region-2 statement can move it.

## Mechanism 2: the original threads the sweep's `?` Err edges straight to the return block

w12a07-cto-sweepthread found this first, on 20a1ae9: the block-scoped 648 `dest` reproduces the
threading but flips the Err-return block's placement. This lane re-measured it on 74b31714a.
`destscope` gives 27,560 B, 0.37605, so the placement flip still happens on the current main.

- Original:
  - The three `?` sites inside the sweep (token_frozen on the coin ATA, token_raw_amount for 660, and the
    second token_frozen) branch to one cold trampoline at the very end of the function (orig rel 0x6360,
    `ldxdw r9,[r10-0x2c8]; ja`). From there they go directly to the function's return block (rel 0x5868:
    `ldxdw r4,[r10-0x8f0]`, then store r7/r9 and `exit`).
  - The From<AnchorError> sites (ConstraintSeeds, 660) carry their own tail-duplicated
    `ldxdw r1,[r10-0x950]; jne r7,2,<return>; ja <post-sweep>` dispatch.
  - The error payload, the swept amount and the function's return payload are all one register (r9).
- Ours:
  - All of those edges jump to a shared trampoline in the middle of region 2 (rel 0x2580, `ldxdw r2,[r10-0x2c8]`).
    From there they go to the shared sweep-exit test after the Rent site (rel 0x3bd8, `jne r7,2`).
  - The Err side then needs `mov64 r8,r2; ja <return>`, and the Ok side spills `swept` (`stxdw [r10-0x970],r2`).
- In the post-opt IR the sweep's result tag is a nest of phis (`_332.sroa.0.0/.1/.2/.3`). The Ok phi mixes the
  constant 2 with the passed-through `transfer_native` tag. The Err phi mixes loaded tags already known to be
  != 2 with From results, which can be anything. So JumpThreading/LVI cannot thread the known-Err edges past
  `sweep.exit`.
- The original's structure must merge the sweep's `?` edges directly into the block that tests the tag. Splitting
  the sweep into nested head/tail functions or an immediately-called closure collapses the function
  (27,520-30,280 B, ratio 0.21-0.23).

## Oracles (tools/, no build slot after one capture)

| tool | what it does |
| --- | --- |
| `segstat.py <so\|fn.bin> [seg] [lo hi]` | per original segment: matched tokens plain / regs masked / frame masked / both |
| `sretbound.py <orig.txt> <cand.txt> <so\|fn.bin>` | sret-slot rank permutation by call layout position, and the remapped-frame ratio bound |
| `invscan.py <mod.ll> <out.jsonl>` | llc oracle: invert every conditional `br` in execute; ratio, bytes and region-2 tokens |
| `invmulti.py` | `ctoracle.py --edit` hook: `INV=k1,k2` inverts several branches |
| `grpscan.py <mod.ll> <out> lo hi` | llc oracle: move every alloca of an alloca-list range to every other position in it |
| `amv.py` | `ctoracle.py --edit` hook: `MV=name:anchor:before\|after` moves one alloca |
| `variants.py`, `run.sh` | the region-2 source variants of this lane and their measure.sh runner (`run.sh <slot> <name>...`) |
| `capture.py`, `trim.py`, `ctoracle.py`, `tokio.py`, `objdis.sh` | copies of w13a12-cto-regalloc's llc oracle (post-opt IR capture, one-function trim, scoring), so the tools above run from this directory |

Capture: `python3 tools/capture.py <crate copy> <work> <out>`, then `python3 tools/trim.py <out>/pump_recovered.ll m.ll`.
`ctoracle.py run m.ll o0` reproduces the build's tokens exactly (checked on 8f050a236: 0.50929).

## IR results (llc oracle, main 74b31714a): the 648 dest-check successor order

`invscan.py` on main 74b31714a (0.51348):
- **Best single inversion: the sweep's own dest check** (line 648, `%.not.i115 = icmp eq (memcmp key,dest), 0;
  br ok, err` turned into err-first). It gives **0.51805 at 27,392 B**: abs 0.6977 -> 0.7200, and
  region-2 tokens 505 -> 519. It changes ISel's RPO, so the ConstraintSeeds sret sites take later ranks. It
  also moves the wallet "quote token account is frozen" block out of the middle of region 2.
- Paired with a +8 B inversion it reaches 27,400 B:
  - `+inv bb44.i134` (sweep token arm, `_130`): **0.51797**;
  - `+inv bb15` (post-validate `_0.sroa.0.0.off0.i66` join): 0.51768 with only 3,265 slots_diff (main 3,334).
- The amm_frozen test inversion alone is 0.51378 at 27,400 B (+0.0003).
- No source spelling reaches these inversions. Rust's `!=` reaches the branch as `br (xor eq,true), err, ok`, and
  InstCombine rewrites `br (not X)` to `br X, ok, err`. So the successor order of a bool test is fixed by
  semantics. Moving the 648 error block later in RPO would need a CFG change, for example its error edge
  merging into a block that is also reachable from the ok path.

## IR results (llc oracle, main 8f050a236)

- **Branch inversion scan, all 147 conditional branches:**
  - 110 inversions keep 27,400 B, and none of them beats main.
  - Best overall: inverting validate's holder_reward test (line 289, `bb5.i` -> `bb11.i/bb6.i`) gives 0.51326 at
    27,392 B. It moves the 289 error block, which is region 1.
  - Pairing it with the region-2 `amm_frozen` test inversion (`bb63.i139`, +8 B) gives **0.51408 at 27,400 B**.
  - No source form found: rustc bools reach the branch as `icmp eq x,0` after InstCombine's
    `ne -> eq + swap` canonicalization, so the successor order is fixed by semantics.
- **Sweep alloca scan:** 728 moves of the 28 inlined-sweep allocas (dest, old, bump, the 664 B CPI accounts
  buffer, sret temps) within their group. Every result is <= main, so the sweep's own frame order is not a lever.

## Source trials (measure.sh, main 8f050a236 0.50929 / 3,325 slots; all 0 losses)

| variant | change | result |
| --- | --- | --- |
| dest_tuple | `let (dest,_)=find_program_address(..)` | byte-identical |
| chk_rev | `if dest!=a.holder_creator_vault.key()` | 0.50899 |
| chk_rkeq | `require_keys_eq!(a.holder_creator_vault.key(),dest,ConstraintSeeds)` | byte-identical |
| chk_hk_local | `let hv=a.holder_creator_vault.key();` reused in the check and payload | 27,368 B, 0.30276 |
| ammf_if | `amm_frozen=if empty{false}else{token_frozen(..)?}` | byte-identical |
| l660_ne / l660_let | `if token_raw_amount(..)?!=0{return err!(..)}` / `let amt=..;require!(amt==0,..)` | byte-identical |
| seeds_old_first | `let old=..;let bump=[..];` | 0.50929, 3,326 slots |
| seeds_bump_ref | `let bump=ctx.bumps.creator_vault; .. &[bump]` | 0.50929, 3,326 slots |
| seeds_old_ref | `let old=a.current_creator.key;` (no 32 B copy) | 27,320 B, 0.50645 |
| seeds_slice | `vsigner:&[&[&[u8]]]` | compile error |
| tcpi_ctx_accounts | `ctx.accounts.pump_amm` for the CPI program | byte-identical |
| oc_decl / oc_decl_only / oc_decl_top / oc_noinner | `old_creator`/`old_fee` declared before the sharing CPI (or at `let swept;`) and assigned in the curve block; or no inner `let old_creator` | byte-identical (all four) |
| val_ifreset | `if let Some(val)=sharing_update{..}` | byte-identical |
| val_clone | `val.clone()` as the CPI argument | 27,496 B, 0.47578 |
| sw_hkval | `sweep(ctx,holder_key:Pubkey)` by value | 27,464 B, 0.29713 |
| sw_accts / sw_bumps | `sweep(a:&AdminCto, cv_bump:u8 \| bumps:&AdminCtoBumps, ..)` | 27,472 B, 0.44518 |
| sv_tailfn / sv_headfn / sv_tailclosure | the sweep split into nested head or tail fns, or a closure | collapse (0.21-0.23) |
| destscope (on 74b31714a) | `{let dest=..;if key!=dest{return Err(..)}}` (w12a07's threading shape) | 27,560 B, 0.37605 |

Ledger keys: `0x22a10-w13-8f050a2-region2-*-v1` and `0x22a10-w13-74b3171-region2-*-v1`.

## Conclusion for region 2

The source statements that produce region 2 are already in the original's call order, clone order and
block shape: 92 % of its tokens match with registers and frame offsets masked. What remains is:
- spill-slot and register assignment in the clone runs;
- the sret-slot ranks and the +8 B, which are fixed by region 1's RPO and the IR-alloca area;
- the sweep's `?` Err threading (mechanism 2).

None of the 27 region-local spellings above moves them at 27,400 B.
The next untried idea is a sweep body whose `?` exits feed the tag test directly. One option is the sweep
returning `Result<u64>` through a single `match` on an inner `Result<u64>` built from the arms, with no
mixed passthrough tag. Any such idea must keep the inlining (no extra nested fn or closure).
