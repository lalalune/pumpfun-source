# w8-profile-flags: profile and codegen flags (wave 8, build inputs)

Question: do the original's profile or codegen flags differ from the current recipe
(`[profile.release] panic="abort", overflow-checks=true, lto=false, codegen-units=1`,
opt-level 3 by default, target RUSTFLAGS `-Zremap-cwd-prefix=`), and could a flag close the
8 remaining windows (regalloc ties such as `v3_buy_costs` 0x80df8, scheduling and block layout)?

Answer: no. The current profile and flags are the original's wherever they affect code. Every flag
that changes code loses matched windows, and no flag gains anything. The remaining
residuals come from source or IR, not from flags.

Bases: main ce53d867a (1027/276, unstripped 31ec6381) for the global trials; main 2b8582135
(1027/276, unstripped ec660de7) for the root-only trials. About 78 real builds or exact relinks, plus 59 llc function-diff screens. All of them are in the ledger
(53 rows, `--lane w8-profile-flags`).

## 1. Method

- **Global flags** (`tools/trial.sh`): a copy of `programs/pump`, a changed `[profile.release]`
  or extra target RUSTFLAGS through the new `PUMP_EXTRA_RUSTFLAGS` knob in `fastbuild.py`
  (empty by default, so the recipe output does not change), a full build (dependencies rebuild),
  then `score.py` and `target_metric.py` on the 8 targets. A control build reproduces the
  baseline sha exactly.
- **Root crate only** (`tools/mainonly.py`, `tools/t2.sh`): fastbuild with `cargo rustc --lib -- <flags>`,
  so the flags reach only `pump-recovered` and no dependency is rebuilt (about 30 s). The control build
  is byte-identical to the baseline (31ec6381).
- **Codegen-stage LLVM knobs** (`tools/capture.py`, `objfuncs.py`, `screen.py`, `relink.sh`, `kscore.sh`):
  capture with `-Csave-temps --print=link-args`, run `llc` on rustc's optimized per-CGU bitcode with a knob,
  and relink with rustc's exact `rust-lld` command. Relinking rustc's own object reproduces the
  unstripped ELF byte for byte (ff22af68). `llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext
  -function-sections -data-sections` reproduces 1338 of 1342 root functions (4 untargeted functions differ:
  rustc sets some TargetMachine option that llc does not). So knobs are scored against the llc base
  (1023), about 15 s per knob.

## 2. Evidence from the original binary (no build needed)

- No `unsafe precondition(s) violated` strings: debug-assertions/ub_checks were off. `dbgassert`
  confirms it (386 losses).
- Overflow-check panics (`attempt to add/multiply with overflow`) are present: overflow-checks on.
- cargo-build-sbf 2.1 (strings of the installed binary) adds only `-Zremap-cwd-prefix=` to the target
  RUSTFLAGS (plus `-g` for `--debug`, sbfv2 flags only for `--arch sbfv2`). That is the current recipe.

## 3. Global profile and RUSTFLAGS trials (base ce53d86, 1027/276)

| trial | normalized | raw | verdict |
| --- | ---: | ---: | --- |
| control (harness copy) | 1027 | 276 | sha 31ec6381 = baseline |
| `-g` (cargo build-sbf `--debug`) | 945 | 152 | debuginfo changes codegen: original had none |
| `-Cdebuginfo=1`, `opt-level="s"`, `incremental=true`, `-Zinline-mir=no`, `-Zcross-crate-inline-threshold=never` | – | – | build fails: SetCreator/BuyV2/AdminCto try_accounts frame > 4096 |
| `-Ctarget-cpu=v1` / `v2` | – | – | link fails (solana-zk-sdk) |
| `-Ctarget-cpu=generic`, `-Cno-vectorize-loops`, `-Cinline-threshold=225`, `-Cforce-frame-pointers=yes`, `-Zcross-crate-inline-threshold=200` | 1027 | 276 | byte-identical (no-ops / defaults) |
| `-Zcross-crate-inline-threshold=50` | 1027 | 276 | sha changes, no window changes |
| `opt-level=2` | 760 | 128 | -267 |
| `codegen-units=16` | 599 | 120 | -428 |
| `debug-assertions=true` | 641 | 115 | -386 |
| `-Zshare-generics=y` | 535 | 114 | -492 |
| `-Zmir-opt-level=3` | 985 | 171 | -42 |
| `-Zinline-mir-threshold=25` / `100` | 947 / 1006 | | -80 / -21 |
| `-Cno-vectorize-slp` | 1026 | 276 | -1 (0x11d950) |
| `-Zmutable-noalias=no` | 761 | 126 | -266 |
| `-Zmir-enable-passes=-JumpThreading` | 791 | 129 | -236 |
| deps `overflow-checks=false` / deps `opt-level=2` / deps `codegen-units=16` | 955 / 973 / 910 | | dependency code changes |
| `pump-token-ext` `overflow-checks=false` | 1026 | 189 | -1 (0x17bc48) |
| `lto="fat"` / `"thin"` / `"off"` | 1027 | 276 / 273 / 270 | **code-neutral**; raw +3-3 / +1-4 / +1-7 from symbol-hash reorder only |
| no `panic="abort"` (target default) | 1027 | 280 | **code-neutral**; raw +9 -5 (hash reorder) |
| Anchor template `[profile.release.build-override]` | 1027 | 275 | **code-neutral**; raw +4 -5 (hash reorder) |
| `-Csymbol-mangling-version=v0` | 1027 | 165 | code-neutral; legacy mangling order confirmed |

None of the 8 targets changes size or ratio in any code-neutral trial, so their residuals do not
depend on symbol hashes or on the module's function order.

### Which inputs feed `-C metadata` (symbol hashes, U/D order)

- Profile fields do. `lto`, `panic` and `build-override` (through the proc-macro dependencies' metadata) each re-roll
  every 17h hash, and the U/D same-generic groups land in a new random order (exact U groups 2..5/18,
  D 20..23/27; base 2/18, 21/27).
- Target RUSTFLAGS do **not** (cargo 1.79 here). `-Zcross-crate-inline-threshold=50` and `-Cno-vectorize-slp`
  keep the symbol set identical to the base (0 of 1084 names differ). The census note "RUSTFLAGS in cargo 1.79's
  metadata" is wrong for this recipe, so a flag added there never disturbs raw order.
- Several profiles are code-neutral (lto false/off/thin/fat × panic set/unset × build-override). Code cannot tell
  them apart, and the hash order can only tell them apart once every other metadata input (root name, path, host,
  lock, features) is exact. Ordered link scripts (w8-sibling-recipes) make this moot for layout.

## 4. Root-crate-only MIR and LLVM IR thresholds (base 2b85821, 1027/276)

Byte-identical: `-Zinline-mir-threshold=60`, `phi-node-folding-threshold=1/3`,
`two-entry-phi-node-folding-threshold=3`. Losses only: inline-mir-threshold 40 (-73),
inline-mir-hint-threshold 90 (-7; 0x80df8 0.920 -> 0.904) and 110 (-58), mir-opt-level 3 (-32),
LLVM inline-threshold 200/300 (-116/-48), two-entry-phi 5 (-1), jump-threading-threshold 5/7 (-2/-6),
simplifycfg hoist/sink off (-257/-71). `-Zmerge-functions=disabled` grows .text by 0x1d068 (not the original).

## 5. Codegen-stage knobs (llc + exact relink)

22 knobs scored and 37 more diffed function by function (lists in `tools/llc-knobs-*.txt`): RA split/spill modes, deferred
spilling, reverse local assignment, split-hint thresholds 0/74/76/100, region budget, schedulers (list-burr, source,
post-RA, misched variants, sched-priority switches), tail duplication (size 1/3/4, placement thresholds), tail merge
(size/threshold), block placement (ext-tsp, precise rotation, exit bias, static-likely-prob 79/81, likely-branch-weight),
machine CSE/sink/LICM/copyprop, early taildup, SSC, CGP branch opts, `-O2` codegen.

- Zero gains. Every knob that changes any target also changes 4..1274 other functions.
- No knob changes 0x80df8 alone. The closest, `split-threshold-for-reg-with-hint=74`, changes 6 other functions and makes
  0x80df8 bigger (2144 B). This agrees with w4-v3costs: the sret split is an MBFI tie set by IR-level
  frequency leakage, and RA heuristics do not settle it.
- Best diagnostic signal: `-tail-dup-size=3` (also confirmed as a root-only real build) raises create_v2 (0.851 -> 0.892 on the
  ce53d86 source) and buy_exact_quote 0x1489f8 (0.851 -> 0.915) but loses 21 windows. In those two functions the original looks
  like it tail-duplicated blocks that ours keeps shared, which points to smaller blocks (different source) at those joins,
  not to a different threshold.

## 6. Conclusion and next ideas

The build recipe's codegen-relevant flags are settled: opt-level 3, codegen-units 1 (root and deps), overflow checks on
(root and deps), debug-assertions off, no debuginfo, not incremental, target-cpu generic, default MIR/LLVM thresholds,
no share-generics. The 8 residuals need source or IR changes.

- Source lanes for 0x1e7c0/0x1489f8: find the joins that `-tail-dup-size=3` duplicates (diff `out/m-taildup3` against base)
  and shrink the shared tail block in source (the original duplicates it at size 2).
- Metadata lanes: profile fields, not RUSTFLAGS, are hashed. If the root identity is ever reproduced, enumerate the
  16 code-neutral profiles (lto false/off/thin/fat × panic set/unset × build-override) on the D/U group-agreement metric.
- `PUMP_EXTRA_RUSTFLAGS` (fastbuild) and `tools/mainonly.py` give later flag lanes a reproducible global or root-only knob.
