# Legacy-SBPF stack and register provenance

`sbpf_provenance.py` is a conservative machine-code dataflow library.
`stack_register_provenance.py` admits two ELF functions, invokes the official
normalizer unchanged, reuses `residual_analysis.py` block correspondence, and
emits a deterministic paired JSON report.

This is a diagnostic tool. It does not establish runtime memory safety,
source-variable identity, complete aliasing, a historical compiler decision,
bytecode equality, runtime equivalence, or scorer acceptance.

## Analysis model

The fixed point operates over the maintained logical-instruction decoder and
CFG. Registers have three states:

- a proven 64-bit constant;
- a proven `r10 + signed displacement` stack pointer;
- unknown, optionally retaining bounded stack-pointer candidates solely as
  ambiguity evidence.

Facts survive a CFG join only when every incoming path justifies the same
constant or stack displacement. Conflicting stack pointers become potential
candidates; an unknown/non-stack path prevents proof. Known branch conditions
can prune an infeasible successor, while unresolved conditions retain both.
Loops are processed to a bounded fixed point.

Supported transfers include LDDW, MOV, constant ALU operations, stack-pointer
addition/subtraction, register copies, direct and derived memory operations,
and exact-width pointer spills/reloads. Overlapping writes invalidate tracked
memory. Unsupported operations destroy their encoded destination fact. Calls
clobber `r0`–`r5` and invalidate all tracked stack-memory values because unknown
arguments or an earlier escaped alias can permit writes. Known stack-pointer
arguments additionally produce explicit escape records. Only full eight-byte
pointer spills/reloads retain pointer provenance; narrow constant stores are
truncated to their actual width. Legacy shifts use the pinned interpreter's
wrapping shift semantics, and MOV32 immediates are zero-extended.

The report separates memory operations into:

- `proven`: the base is a proven stack pointer;
- `potential`: at least one incoming definition is stack-relative but the
  merged value is not proven;
- `unknown`: no stack-relative interpretation is justified.

Unknown pointers are never silently treated as `r10`. Suspected spill/reload
rows prove only an exact-range reaching store and load; compiler spill intent is
explicitly not claimed.

Register liveness uses conservative instruction use/definition sets over the
decoded CFG. It reports block live-in/live-out sets, maximum pressure, and
definitions not live after the defining instruction.

## Paired report semantics

Each image's facts are exact static-analysis results. Cross-image frame and
liveness rows are different: they depend on the existing residual analyzer's
explicitly heuristic block mapping plus local instruction alignment. Every such
row carries `classification: heuristic_correspondence`, its confidence, and the
block-match method. Unmatched operations never become exact absence claims.

The report binds both ELF hashes and the actual compiled source bytes of its
analyzer and maintained decoder/CFG/scorer graph. It reuses the private
source-only `fresh_control_inputs.SourceContext` with a scoped module list;
executable timestamp caches and preexisting canonical aliases cannot replace
that graph. Source changes are rejected before admission and after analysis.
Function selectors must resolve to complete logical
instruction boundaries; the candidate range must be an unstripped ELF function
symbol. Output paths cannot alias inputs and existing outputs are refused.

## Usage

```sh
python -B reconstruction/harness/stack_register_provenance.py \
  evidence/original/pump/deployed.so /path/to/unstripped.so \
  --original-window 0x22a10:27400 \
  --candidate-symbol _ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E \
  --expect-original-sha256 7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d \
  --expect-candidate-sha256 54344822ddef0bd4b1f7b4e8a6c80e5aae7e7fb804c5c82c67e7ebff369e9229 \
  --json /new/output/report.json
```

Selectors may be explicit `START:SIZE` ranges or exact symbol names. Optional
`--score-receipt` arguments use the existing residual-analysis admission and
bind the candidate digest and selected original window. Official score
normalization and acceptance rules are not modified.

## Author's historical Admin CTO qualification

The following measurements are retained as authored. The independent admission
repair and fresh report are recorded separately below; their source manifests
and report digests are not substituted into this historical record.

The retained run compared captured Pump Main `0x22a10` (27,400 bytes) with the
source-built candidate used by the deterministic Admin CTO fuzzer. Inputs:

- final upstream synchronization: `67e06453c887c7690c336746ee8e26156bcd8775`;
- original SHA-256: `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`;
- candidate SHA-256: `54344822ddef0bd4b1f7b4e8a6c80e5aae7e7fb804c5c82c67e7ebff369e9229`;
- report SHA-256: `7ab1ff86db35b89fd3b5f45fd350f70bf52c6e5fd9ddd22d29cd0a167cab7305`.

New exact facts beyond `stack_access.py` and `residual_analysis.py`:

| Fact | Original | Candidate |
| --- | ---: | ---: |
| proven direct stack accesses | 1,473 | 1,442 |
| proven stack-pointer formations | 456 | 462 |
| stack-pointer call escapes | 142 | 143 |
| same-range reaching store/reload patterns | 39 | 31 |
| potential stack accesses | 0 | 25 |
| unknown memory accesses | 511 | 516 |

The original entry provides one concrete proof chain: at `+0x80`, `r1` copies
`r10`; at `+0x88`, it becomes `r10-0x6c0`; at `+0xf8` that exact pointer is a
call argument, so tracked stack memory is conservatively invalidated. The
candidate's 25 potential accesses are mostly later `r8 + displacement` reads
where a stack candidate reaches the join alongside other unknown definitions;
none is classified as proven.

The paired heuristic layer found 201 moved-frame-slot rows and 252 mapped-block
liveness differences. Examples with high-confidence `unique_structure` block
matches include:

- original `+0x2830` / candidate `+0x2a30`: `-0x970` versus `-0x978`;
- original `+0x2838` / candidate `+0x2a38`: `-0x978` versus `-0x970`;
- original `+0x57c0` / candidate `+0x57a0`: `-0x488` versus `-0x470`;
- original `+0x57d0` / candidate `+0x57b0`: `-0x480` versus `-0x468`.

These pairs are actionable compiler diagnostics, not source attribution. The
real functions contain no proven memory operation whose encoded base is a
derived stack alias; that negative result is retained rather than inflated.

## Tests

```sh
python -B scripts/run_discovered_tests.py reconstruction/harness \
  'test_*provenance.py' --expect 36
```

Synthetic coverage includes MOV chains, stack arithmetic, constants, joins,
loops, branch pruning, call clobbers, pointer escape, spills/reloads, conflicting
definitions, overlap, unsupported opcodes, indirect calls, LDDW, liveness,
malformed ELFs, invalid symbol boundaries, input/output aliasing, deterministic
JSON, and false-positive rejection. A captured Admin CTO regression asserts
that every direct proven access exactly preserves `stack_access.py`'s existing
inventory before checking the newly available facts.

## Independent pass111 admission repair

Implementation `f37b06e4c584955e80dd02c48ac93e406fa2358c` independently
reproduced the real pair above using actual source-only imports. Two CLI runs
produced byte-identical reports with SHA-256
`432a280f6ee7290b52334406497c0aaf1e605ffa8b033505a3ee3ac0796b43e4` and
analyzer source manifest
`0c919662012d8a89dd851564c89adea7f797e9e0b695afb536c90b81527e1bfa`.
All real-pair inventory and heuristic counts above remain unchanged. The full
source graph now includes the report publisher, input-admission helpers, and
the reused private source context.

Six regression methods reproduced 15 false-fact subcases in the authored
engine: partial pointer spills, untruncated narrow constants, negative MOV32
immediates, shift counts at the register width, wrapping pointer arithmetic,
and memory retained across calls with unknown aliases. The repaired engine
passes those controls. The arithmetic rules are pinned to the
[legacy interpreter](https://github.com/anza-xyz/sbpf/blob/v0.12.2/src/interpreter.rs)
and [version features](https://github.com/anza-xyz/sbpf/blob/v0.12.2/src/program.rs)
of `solana-sbpf` 0.12.2; they do not claim support for later instruction sets.

The counted new suite passes 36 methods with no skips. Adjacent static suites
also pass: 108 combined execution records cover 97 unique methods, including
11 repeated records from an imported test class. Actual CLI controls first
proved malicious timestamp caches executable, then verified raw-source
analysis under normal Python, `-O`, and `-OO` without executing those caches.
Canonical alias poisoning, source edits during bootstrap, and edits before
ELF argument admission are rejected. No program VM execution or compiler build
was performed for this tooling qualification.

The independent machine-readable record is
[`sbpf-stack-register-admin-cto-pass111.json`](qualification/sbpf-stack-register-admin-cto-pass111.json).
The author's original qualification JSON remains unchanged. Per-image results
are facts under this conservative static model; cross-image correspondences
remain heuristic. Neither layer establishes runtime memory safety or changes
completion scoring.
