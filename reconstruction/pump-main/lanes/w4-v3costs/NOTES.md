# Lane w4-v3costs: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Base: origin/main 630a074 (1023 normalized / 277 raw). **The source is unchanged.** No source trial moved the
target, and the analysis below shows why ordinary source on this toolchain cannot reach the IR-level match.

| Build | Bytes | ratio | '-' / '+' slots | calls | normalized / raw |
| --- | ---: | ---: | ---: | ---: | --- |
| base 630a074 (IR capture, sha 5d661a63) | 2,136 | 0.920 | 19 / 21 | 17/17 | 1023 / 277 |
| coldaiclos, coldai2, ai375 | byte-identical ELF | | | | 1023 / 277 |
| coldclos, coldiclos | 1,728 | 0.543 | 126 / 81 | 15/17 | 1023 / 276 (raw loss 0xa868) |

## IR-oracle findings (one-function module, SDK llc, reproduces the base exactly)

1. **Exact decision rule.** The residual (sret pointer split into r6 instead of spilled everywhere and reloaded into
   r3) flips exactly when the MBFI frequency of the line-375 `to_string` panic block (`bb3.i.i39`) exceeds the
   frequency of the first `protocol_fee_split` try_from panic block (`bb5.i27`).
   * `%43` (375 Display::fmt failure branch) weight `1:N`: N <= 262000 matches (0 diff, 2,120 B), N >= 263000 does
     not. The boundary is 2^18 = 2^20 * freq(bb29)/freq(bb3.i14) = 2^20 * 0.09375/0.375.
   * `%_15.i17` (first split try_from) cut `1:N`: N >= 6e6 matches, 4e6 does not.
   * At the boundary, adding 1:2e5 or cutting 1:1e8 on each of the other four front panic edges and on the 371
     `to_string` edge never changes the outcome. Only these two blocks matter. With the 371 and 375 panic blocks
     merged into one block (frequency 371+375), the sret allocation becomes the original's, though the merged block
     changes layout (2,112 B). So the rule compares block frequencies.
2. **Why source cannot reach it on this toolchain.** Without `!prof`, every panic edge gets the BPI NORETURN estimate
   1:0xfffff (2^-20). The original therefore needs freq(bb29) > freq(bb3.i14). freq(bb3.i14) = P(is_mayhem == 0) =
   0.375 (zero heuristic, its lowest possible value). The path to bb29 passes four branches that have no BPI
   heuristic (`%_54.1` overflow, add3#1 Result, post flag / add3#2 Result, `%or.cond`): 0.5*0.5*0.75*0.5 = 0.094.
   The add3 results are call returns, so no weight can be put on them, and the cap without metadata is far below 0.375.
   Cold estimates propagate up to bb29 and make it colder (all 1,023 subsets of cold on the 10 non-panic call sites
   were tried: no match). So the original IR carried branch metadata on this function, or merged panic blocks.
   rustc 1.79 emits `!prof` only for MIR `Assert` (1:2000 on a panic_const edge), and no Assert can land on the fmt
   branch without adding code.
3. **Not a uniform toolchain policy.** Putting 1:2000 on all 372 `to_string` expect branches in the whole module (full
   module llc) changes 7 currently-matched functions: admit_associated_token_account, initialize_metadata,
   get_token_distribution_amounts, extend::execute, require_ata, update_schedule and __idl_set_buffer. A compiler that
   weighted these branches everywhere would break those windows. Caveat: the weights here were added to the
   optimized IR. A real toolchain would add them before opt, and opt could drop them in some contexts.
4. **Not a host artifact at the llc stage.** The official Linux x86_64 v1.44 llc (archive sha256 6719b889..., run under
   podman linux/amd64) gives instruction-identical output to the macOS llc on the same IR. Platform-tools v1.43 llc does
   not know +store-imm/+jmp-ext, so v1.43 is ruled out.

## Source trials (ledger keys `0x80df8-main-630a074-<trial>-v1`)

* coldclos / coldiclos: `#[cold]` (with or without `#[inline]`) on the 375 `ok_or_else` closure. This rustc accepts
  attributes on closures; the closure is outlined (15 calls, 0.543) and raw window 0xa868 is lost.
* coldaiclos: `#[cold]#[inline(always)]` closure for 375. Byte-identical ELF (cold is dropped on inlining).
* coldai2: the same on both the 371 and 375 closures. Byte-identical ELF.
* ai375: `#[inline(always)]` closure for 375. Byte-identical ELF.

Analysis rows: 063a2b17 (decision rule + global weighting + cold combos), 5cfd7e63 (only two leaks matter, heuristic
cap), e082faf1 (panic merges), 5d1490c4 (Linux llc).

## Oracle tools (`oracle/`)

* `capture_full.py` lane-local build with `--emit=llvm-ir`; `mkone.py` one-function module; `irexp.py` edit + llc +
  diff vs `win.py orig` (jumps normalized); `fn.sh` disassembler helper.
* `bwg.py` (`BRS=cond:a:b,...` arbitrary branch weights), `merge.py` (`MERGE=from:to` redirect panic blocks).
* `coldcombo.py` every subset of cold call sites; `globw.py` module-wide weights on every to_string expect branch;
  `fndiff.py` per-function diff of two objects.
* `ctrial.sh` source trial: patch, IR capture build, official score, target metric, `!prof` count, IR equality.

## Next ideas

* A full Linux x86_64 host build of the current source (opt stage on Linux, not only llc). The earlier
  linux-host-control (b4448f7bc^) predates the current v3_buy_costs source. Low prior: LLVM opt is host-deterministic.
* Look for code in the original that is not in the reconstruction and reaches v3_buy_costs's IR: an Assert or
  `likely`/`unlikely` whose weight survives on `%43` or on the mayhem branch. Nothing in the visible source does this.
* Treat the target as blocked unless another window shows a matching metadata signature.
