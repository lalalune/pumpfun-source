# Lane migrate-execute-arith

Target: `0x77940` `migrate_v2::execute` (8,832 B). The callgraph census records
diagnostic_similarity 0.201 for this window — the lowest among the large
handlers — and no committed lane documented its arithmetic semantics. This lane
is a static opcode census of the committed capture; it builds nothing and runs
nothing from the binary.

## Corrections

1. **First pass (b93f2a708).** Claimed the window's odd opcodes were a SBF
   reassignment of the eBPF register-jump family to 128-bit ALU operations, and
   committed a `census.json` that was a Python traceback. Both retracted: the
   standard eBPF/SBF encoding with register-form jumps is correct (the sbpf
   VM's own `JEQ64_REG`/`JLT64_REG` definitions; the `0x78e28` control-flow
   test leaves the guard branch live under the standard reading and dead under
   the reassignment reading), and the census now writes its own artifacts.
2. **Second pass (d0276f428, pre-squash and bec926d1).** The census derived
   each `lddw`'s high word from the instruction *index* rather than the
   instruction's own address, which misattributes constants after any 16-byte
   `lddw` pair; and its error-constant scan covered only `lddw`/`mov`,
   missing the store-immediate codes entirely. This inflated the "error
   sentinel" story to six sites and hid the real finding. Both fixed here; the
   bit-63 error-ABI hypothesis is retracted.

## Tool (Rust, zero dependencies)

`tool/` is a standalone Cargo crate (excluded from the repository workspace):
`sbf_census <capture.so> <capture.json> <vaddr> <length> <listing-out> <census-out>`.

- verifies the capture SHA-256 against `capture.json`'s `payload_sha256`
  (hand-rolled SHA-256, no external crates);
- maps the virtual address through the ELF `PT_LOAD` headers;
- decodes with the standard eBPF/SBF encoding (register jumps included,
  `lddw` paired) and **refuses to census a window that contains an opcode
  outside its tables** instead of guessing;
- classifies compare-guarded checked arithmetic, saturating skip-guards,
  division sites, and error-code immediates via `lddw`, `mov` **and the store
  family** (`stw`/`stdw`/`stb`/`sth`);
- writes the listing and census JSON directly (no shell redirection); two
  consecutive runs are byte-identical.

Regeneration from `tool/`:

```sh
cargo run --release -- ../../../../../../evidence/original/pump/deployed.so \
  ../../../../../../evidence/original/pump/capture.json 0x77940 8832 \
  ../listing.txt ../census.json
```

## Findings

1. **The original raises three PumpError variants that the reconstruction
   never raises anywhere.** The window builds four error values as
   store-immediates in the standard 6000+N range:
   - `0x780b8`: `stw [r10-568], 6064` → `InvalidQuoteTokenProgram` (6064−6000)
   - `0x78260`: `stw [r10-568], 6010` → `AccountTypeNotSupported`
   - `0x78c58`: `stw [r10-568], 6076` → `InvalidCashbackRecipient`
   - `0x795e0`: `stw [r10-568], 6010` → `AccountTypeNotSupported` (second site)
   Each store sits inside an error-object construction that also stores
   call-site location metadata (e.g. `stb 2; stw 305; stdw 60` at `0x780c0`
   — line 305, column 60; `stw 342` at `0x78c40` — line 342, column 60),
   consistent with anchor `error!()` construction. A repository-wide grep
   finds `AccountTypeNotSupported`, `InvalidQuoteTokenProgram` and
   `InvalidCashbackRecipient` **only in the enum definition** — no source
   raises them — so the original's `migrate_v2::execute` performs three
   validations the reconstruction does not implement. This is a concrete
   semantic gap and a structural part of the 0.201 similarity; locating the
   exact checked conditions is the follow-up.
2. **The original's overflow-checked arithmetic in this window is
   compare-guarded, matching the reconstruction's combinator style.** Exactly
   two sites carry the guard shape:
   - `0x78e18`: `add r6, r1` guarded by `jlt r6, r0, +1` at `0x78e28` — a u64
     add whose result is compared against the first operand; the taken branch
     reaches an error path. Position and operands are consistent with the
     source's `real_quote_reserves.checked_add(post_complete_quote_in)`.
   - `0x786d0`: `sub64` guarded by `jgt` (reg) at `0x786e8`.
   The source expresses three checked operations in `execute` (one add, two
   sub); the third's lowering does not use this guard shape within the census
   window and is flagged for follow-up rather than claimed.
3. **No division, modulus or 64-bit multiplication anywhere** in the window,
   so the migration math performs no curve recomputation — consistent with the
   source, which only adds/subtracts and delegates pool creation to the
   pump_amm CPI.
4. 70 call sites, 1 exit: one function with heavy helper/CPI fan-out. The
   saturating_sub sites of the source live in `init_pump_amm_boost_v2`, which
   is `#[inline(never)]` with its own window — their absence here is
   consistent, not a discrepancy.
5. 34 `lddw` instructions carry 18 distinct 32-bit values: 16 values in the
   0x1b5xxx–0x1bdxxx range (uninterpreted — Anchor discriminators/hashes by
   shape) plus two full 64-bit constants whose low halves are 0x1a and 0x17:
   `0x800000000000001a` at `0x77ef8` and `0x8000000000000017` at `0x78740`,
   each compared by a following `jeq` (register form). Their purpose is
   **uninterpreted** — they are not error codes (the error codes are the
   store-immediates above), and no higher-level meaning is claimed.

## Comparison table

| Source claim (`migrate_v2.rs` @ main 094a06f1) | Original census (this window) |
| --- | --- |
| `checked_add(real_quote_reserves, post_complete_quote_in)` → Overflow | guard-shaped checked add at `0x78e18` |
| `checked_sub(fee)` (native), `checked_sub(quote_before)` | one guard-shaped checked sub at `0x786d0`; the second sub's shape unresolved here |
| `saturating_sub` ×2 in `init_pump_amm_boost_v2` | absent — consistent (`#[inline(never)]` helper, own window) |
| no division in `execute` | zero div/mod/mul64 sites |
| (no occurrences of `AccountTypeNotSupported`, `InvalidQuoteTokenProgram`, `InvalidCashbackRecipient` in source) | three variants constructed at four sites with location metadata — a missing-validation gap |

## Limits

Static census of one window of the committed capture; nothing is executed and
no SBF build is performed. Window bounds from
`reconstruction/pump-main/prior-swarm/TARGETS-20261029.json`; similarity 0.201
quoted from `reconstruction/pump-main/lanes/callgraph-census`. The purpose of
the two full 64-bit `jeq` constants and the 0x1b5xxx range is uninterpreted,
and the exact checked conditions behind the three missing validations are not
reconstructed here. This lane makes no equivalence or security claim.
