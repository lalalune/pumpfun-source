# w17a13-shim-pool-gate: the pool CPI gate in the original's call order (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Wave 17 SHIM track. Region P1 of the w17a01 Ghidra map (pool CPI gate, original 0x4aa8-0x4e50).
Ledger: approach `poolgate`, keys `0x22a10-w17-af6ca66-poolgate-<mechanism>-v1`.

## Result

One edit on line 761 (no line added). Main's volatile `ctx.accounts` reload (w17a06 #3961), which fed the pool
**owner** test, now feeds the pool **data_is_empty** test, and the two tests swap:

```rust
// main
let pool_updated=!a.pool.data_is_empty() && unsafe{read_volatile(transmute::<&&mut AdminCto,*const &AdminCto>(a))}/*shim: ..*/.pool.owner==&AMM;
// this lane
let pool_updated=a.pool.owner==&AMM && !unsafe{read_volatile(transmute::<&&mut AdminCto,*const &AdminCto>(a))}/*shim: reload the accounts pointer for the pool data_is_empty test*/.pool.data_is_empty();
```

The P1 call order is now the original's: `memcmp`, `data_is_empty`, `sol_log_`, 8 x `AccountInfo::clone`, `memcpy`,
`admin_cto_pool`. The number of `read_volatile` constructs is unchanged (one moved).

| build | admin_cto ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main af6ca66a2 | 0.67825 (M 2,264) | 3,220 | 27,400 | 1034 / 1034 | - |
| af6ca66a2 + this edit (measure.sh) | **0.67855** (M 2,265) | 3,220 | 27,400 | 1034 / 1034 | 0 / 0 |
| main ae14cbeb4 (#3985, #3991, #3992 landed meanwhile) | 0.67945 (M 2,268) | 3,170 | 27,400 | 1034 / 1034 | - |
| ae14cbeb4 + this edit (merged branch, measure.sh, unstripped b3c99da10fd249e6) | **0.67975** (M 2,269) | 3,170 | 27,400 | 1034 / 1034 | 0 / 0 |

Runtime differential on both builds: 388 cases, 0 mismatches.

## Why the task's shim spelling loses, and why this one does not

The angle proposed one volatile `accounts[0xe]` load used by both tests, owner first (the original keeps the pool
pointer in r7 across `memcmp` and passes it to `data_is_empty` with `mov64 r1,r7`).

- That form (`pA`) is byte-identical to the plain owner-first spelling (`mpo`, `pB`) and to a plain
  `let pool=a.pool.as_ref();` binding (`pC`): `memcmp` is readonly, so GVN merges the second `a.pool` load anyway.
- All three give M 2,131 at 27,424 B (main 2,264). The gate itself takes the original's shape
  (`ldxdw r6,[r8+0x70]; ldxdw r1,[r6+0x18]; .. memcmp; jne; mov64 r1,r6; call data_is_empty`), but the pool CPI arm
  now uses the entry accounts value, so the accounts pointer stays live across the gate in a callee-saved register
  (r8). The post-opt IR differs from main's only in the gate (name-normalised diff), yet the RA change flips the
  **sweep layout**: the TCF CPI result block ends in `ja` instead of falling into the post-sweep `jne r7,2` check, and
  the 110-insn AMM collect arm (main 0x5580, original 0x55b8) is placed right after it (0x3c38). That costs about
  -100 M in 0x5400-0x5c00 alone. Call this the sweep-layout collapse.
- In this lane's form the volatile reload sits in the `data_is_empty` block, which dominates the pool CPI arm, so GVN
  forwards it into every later `a.*` load of the arm and the entry accounts value dies at the gate (as on main). The
  sweep layout stays in main's mode and the gate gains +1 M.

## Other forms tried (slim pre-opt oracle, w17a06 `preslim.py` + `fx.py`; main M 2,264 @27,400)

| key | form | M | bytes | note |
| --- | --- | ---: | ---: | --- |
| pA | volatile single pool load, owner-first (task form) | 2,131 | 27,424 | collapse |
| pB / pC | plain owner-first / plain single binding | 2,131 | 27,424 | = pA byte for byte |
| pAn | pA + n1 (event reads `creator_fee_bps`) | 2,130 | 27,400 | collapse |
| pD1 | owner-first + volatile accounts reload at the CPI arm head | 2,125 | 27,456 | `pargs` (before the `if`) keeps the entry accounts live; collapse |
| pD1n / pD1h / pD1e | pD1 + n1 / + `pargs.1=holder.unwrap_or(false)` / + event timestamp first | 2,125 / 2,075 / 2,088 | 27,432 / 27,472 / 27,448 | |
| pF | single pool pointer + arm-head reload + `pargs` inlined at the call | 2,137 | 27,440 | collapse |
| **pE** | owner-first, accounts reload moved to the `data_is_empty` test | **2,265** | **27,400** | landed form |
| pEn | pE + n1 | 2,258 | 27,376 | |
| pEL / pEh / pEhn | pE + `pargs.1` read at the call / + holder local / + both and n1 | 2,132 / 2,132 / 2,132 | 27,432 / 27,432 / 27,408 | collapse |
| m0n | main + n1 | 2,257 | 27,376 | event gains the original's `ldxdw r4,[r3+0x70]`; old_fee takes r6 |
| m0h / m0L / m0nh / m0Ln | main + holder local / late `pargs.1` / with n1 | 2,131 | 27,408-27,432 | collapse |
| m0e | main + event literal `timestamp` first | 2,228 | 27,392 | curve loads scheduled before the mint copy |

IR single-edit screens (w17a06 `gen.py`/`screen.py`, about 500 edits each, stopped early):
- on pA, nothing restores the sweep layout at 27,400 (best 2,239 @27,296 from a wallet fence);
- on m0n, nothing reaches 27,400 above main (best 2,261 @27,384).

## Reading

- The sweep layout is bistable, and the pool tail decides it through the RA: any change that keeps a value live across
  the gate or the clone run in a different register (entry accounts across the gate, the holder byte read at the call
  instead of at the arm head, the holder local passed as the CPI arg) flips it. Every tail change has to be priced
  with the layout in mind; keep a volatile reload dominating the pool CPI arm.
- The original keeps the sharing tag in r6 and swept in r9 over the whole tail (see w16a19 / w15a33), so its holder
  flag is a spill (`ldxdw r4,[r10-0x950]` at the call) and its pool pointer gets r7. Ours spills the tag and swept and
  keeps `nf` in r9; that is the remaining P1/EV naming gap.

## Incident

At about 22:57 PDT a too-broad `pkill -f tools/screen.py` (meant for this lane's two screens) also killed lane
w17a10-shim-newpieces' pair screen (`irbeam/tools/screen.py ir/e79v.s.ll ex/e79v_edits.jsonl ex/scr_e79v_pairs.jsonl`,
187 of 276 jobs done). It was restarted from w17a10's out dir with the same files (`3 - --combo ex/e79v_pairs.txt`;
screen.py resumes from its output file), appending to `ex/scr_e79v_pairs.log`.
