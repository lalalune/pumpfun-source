# Evidence and reconstruction tooling

Python 3.12 is supported. Capture, structural analysis, evidence verification and
comparison require only the standard library. Optional local execution uses pinned
`solders==0.27.1` from `requirements.txt`; pyelftools supports independent ELF checks.
No command here signs or sends transactions to a network. LiteSVM uses local test keys.

## Verify the saved snapshot

The maintained entry below runs the frozen saved-capture verifier with its
assertions enabled. It refuses Python optimization (`-O`, `-OO` or
`PYTHONOPTIMIZE`) rather than report evidence it has not checked. The historical
`scripts/verify_evidence.py` stays byte-identical and must not be run optimized.

```sh
python3 repro/capture-verification-mode/verify.py
python3 scripts/test_tooling.py
python3 repro/capture-verification-mode/test_verify.py
python3 scripts/analyze.py
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/local_validation.py
```

The validation script regenerates `audit/local-validation.json`. Evidence verification
is distinct from reconstruction verification. Evidence CI checks captures, source manifests,
saved candidate executables and bounded regressions, and builds native fragments. The
separate dependency workflow builds selected pinned dependency candidates. Routine
evidence CI does not clean-build all four recovered SBF programs. The verification matrix allows up to twelve concurrent jobs: four disjoint Pump groups, three Mayhem groups, and the five other checks. Every previous differential command remains represented; Pump groups retain receipt hash, runner-script and candidate immutability, and mismatch checks. The partial curve runner has an explicit 56-case failure gate. Available hosted concurrency and fixture cost determine wall time.

## Capture a new deployment snapshot

```sh
python3 scripts/capture.py --output work/new-capture
```

This captures the four addresses in `repro/programs.json`. It refuses existing program
output directories. Keep failed/partial captures separate and use a fresh output root
when retrying. Optional `--rpc` accepts another RPC; its URL is not written to evidence
to avoid disclosing credentials. Record the provider separately if needed.

`repro/dependencies.json` lists external captures. To capture one dependency, call
`scripts.capture.capture(rpc_url, name, address, fresh_output_path)` from Python.
The loader-v2 branch handles immutable legacy Program accounts. The upgradeable
branch preserves both Program and ProgramData accounts. Other loader formats are
not supported and must not be silently parsed as upgradeable programs.

## Inspect original machine code

```sh
python3 scripts/disassemble.py --objdump /path/to/platform-tools/llvm/bin/llvm-objdump \
  --output work/disassembly-new
```

This records the tool hash, version, input hashes and output hashes. The output
is original-derived disassembly for analysis, never a rebuilt executable.

`scripts/disassemble.py` is pinned by SHA-256 in saved checkpoints and the P27
guard, so it stays unchanged. It does not check that the listing covers the
input. For new captures, use the byte-checked generator
`research/disassembly-coverage/disassemble_checked.py`, which takes the same
arguments. It verifies every executable file-section byte against the listing,
requires contiguous decimal eight-byte SBF instruction slots, and accounts for
sixteen-byte LDDW rows. Empty, truncated, byte-mutated, misaddressed, unknown or
unparsed executable rows prevent a success manifest. Input and tool hashes are
rechecked after capture. Repository-relative binary arguments keep LLVM's listing
preamble independent of the checkout's absolute path. Historical manifests remain
unchanged.

To independently check a canonical LLVM SBF listing:

```sh
python3 research/disassembly-coverage/verify_disassembly.py \
  evidence/original/pump/deployed.so work/disassembly-new/pump.asm
python3 research/disassembly-coverage/test_disassembly.py
```

Coverage verifies listing bytes and addressing. It does not prove mnemonic/operand
semantics, reachable control flow, inferred function boundaries, source recovery,
or rebuilt binary identity. The [v1.44 checkpoint](../repro/disassembly/2026-10-26-v144/README.md)
records complete executable-byte coverage for all four captured core programs.

## Compare an independently compiled candidate

Pinned recipes for the current partial candidates are documented in the program
READMEs and indexed by `repro/status.json`. After building a candidate, compare its
complete output as follows:

```sh
python3 scripts/compare.py pump /path/to/independently-built/pump.so \
  --pad-zero-to-allocation --output work/comparison-pump
```

Without `--pad-zero-to-allocation`, this is a raw whole-file gate: exit status is
zero only when the unmodified candidate file equals the complete captured payload,
including its allocation suffix. With the padding flag, exit status zero means only
that the comparator-synthesized, zero-padded allocation image equals the capture.
That is padded allocation equality, not byte identity of the compiler output (the
unmodified candidate is shorter), and must be reported with that label. In that
mode the top-level comparison fields describe the padded image;
`candidate_input_sha256` still identifies the unpadded input.
Omit the padding flag when the candidate already contains the complete allocation.
The optional padding step appends newly allocated zeros only; it never copies data
from the original. It first checks that the original's bytes beyond all ELF file
extents are zero. Original bytes are used only for validation and comparison.

The report records both hashes, original/candidate lengths, changed positions,
first difference and whether zero padding was requested. It deliberately sets
`source_provenance_verified` to false: the comparator cannot prove how a caller
obtained a candidate. A future release needs source/compiler manifests and a clean
build trace in addition to this comparison. Passing the original as the candidate
would prove nothing about source reconstruction.

`scripts/compare.py` is bound by SHA-256 in saved promotion checkpoints and in the
current P27 guard, so it stays unchanged. For a strict raw comparison that also
lists every changed, missing and extra byte range of the two unmodified files, use
`research/byte-diff/byte_diff.py` (see `research/byte-diff/README.md`). It never
pads either input and exits zero only on complete raw equality.

## Local compiler inputs

`build_partial_candidate.py` records crate Rust sources/manifests, the owning workspace manifest and lockfile, ancestor `idls/` JSON files used by Anchor `declare_program!`, and repository-local Cargo/toolchain configuration before and after compilation. `--extra-input <path>` adds a repository-local path dependency or other build-script/include asset; repeat it for additional inputs. The before/after maps must be identical. This is an inventory of known local inputs, not a hermetic toolchain/dependency closure. Registry archives, environment and toolchain identity require their separate build records.

The current PumpSwap source has a local path dependency outside its standalone
crate: `crates/native-transfer-fee`. Generic build helpers require it explicitly,
along with the retained Pubkey source directory. Run this from the repository root:

```sh
python scripts/build_reconstruction_candidate.py \
  --manifest programs/pump-amm/Cargo.toml --program pump_amm \
  --artifact-name pump_amm_recovered.so --tools-version v1.44 \
  --extra-input programs/pump-amm/vendor/solana-pubkey \
  --extra-input crates/native-transfer-fee --output work/amm-research-build --dry-run
```

Remove `--dry-run` only when ready to run a new research build with the required
SDK and locked cache. The native flag includes both `Cargo.toml` and `src/lib.rs`;
without it, the historical helper can compile the dependency without recording
its bytes. The supported-target adapter instead rejects unrecorded local path
dependencies. These input inventories do not by themselves authenticate registry
sources, tools or runtime behavior.

Use the [current AMM version 3 workspace recipe](../repro/pump_amm/v2-mint-clone-recovery-20261028/workspace_recipe_v3.py)
when staging the standalone AMM and native crate as a workspace. Version 3 binds
56 canonical and 57 workspace inputs without changing Rust. Its `stage` and
`verify` commands are shown in the [AMM README](../programs/pump-amm/README.md).
The version 2 recipe is retained for checkpoints that predate this dependency.

Older saved builds keep their original manifests; their scope is not retroactively expanded. Fees workspace experiments explicitly bind their root manifest/lock and IDLs in separate provenance records. Run `python3 scripts/test_build_source_manifest.py` to verify that workspace-lock, IDL and explicit-asset changes are detected.

The manual [controlled Linux Fees workflow](../repro/pump_fees/linux-v144-build-plan/README.md) performs one fixed-source build using the official Linux v1.44 distribution. Its comparison is separate from runtime acceptance; changed bytes do not inherit the current candidate’s saved receipts.

The first Linux attempt stopped before compilation because a locally modified SDK installer had supplied the original expected hash. The [official SDK correction](../repro/pump_fees/linux-v144-sdk-correction/README.md) preserves that failed attempt and pins the unmodified official archive; the explicit v1.44 compiler selection and all source/dependency inputs stay fixed.


Later retained SDK analysis distinguishes compiler selection from stripping. The current Darwin Pump and Fees recipes compile with v1.44 but their retained SDK installer selects v1.52 `llvm-objcopy` for post-compilation stripping. Before/after files and SDK selection are recorded; a complete historical process invocation trace is not available. The official unmodified Linux SDK instead defaults to v1.43 for that phase. Two early hosted attempts stopped before compilation. The corrected fixed-source workflow subsequently completed [run 40166255149](https://github.com/lalalune/pumpfun-source/actions/runs/40166255149), with retained compiler-entry traces and a separate Linux candidate. [Linux/Darwin attribution](../repro/pump_fees/linux-darwin-v144-attribution/README.md) finds no additional original body matches and fourteen matching original standard-library diagnostic tuples. This applies to the frozen earlier Fees source, not current candidates or a uniquely recovered historical recipe.


The current Pump/Fees immutable package verifiers have an optional `--current-main` mode designed for the original research checkout. It includes historical scratch harness paths and, for Pump, the recorded Darwin Surfpool executable. A clean clone does not contain those local paths. CI runs each immutable verifier in portable mode, then `scripts/verify_current_bindings.py pump` or `fees`: this checks every current source/helper/documentation/runtime binding, maps exactly four historical harness names to their byte-identical published copies, and rechecks the complete Pump serializer/calls/literals. The historical Surfpool executable remains identified by its saved hash; the Linux check does not claim that executable is installed or that Surfpool was replayed. New runtime CI suites still execute against the current candidates.


The [reviewed Linux pipeline correction](../repro/pump_fees/linux-recorded-pipeline-correction/README.md) is now integrated into the manual workflow. It preserves the baseline of 22 frozen source inputs, exact 53-file recorded SDK and unchanged build command, verifies both Cargo cache namespaces against all 252 locked crate archives, checks executable modes, and traces process lifecycle plus actual compiler/stripper execution. Thirty focused preparation/retention tests pass locally; the manual job reruns them on its host. The first action requiring native tooling is a tiny strace readiness probe before downloads or compiler-attempt counting. That hosted run subsequently passed readiness and produced the bounded comparison linked above. Current source revisions have not inherited its binary identity or runtime evidence. No untraced or installation fallback is automatic.


## Compiler identity audit and research builds

[The build identity audit](BUILD_IDENTITY_AUDIT.md) supersedes section-size-based claims that v1.43 is proved or that a binary-size ratio is source completeness. Fresh backend and exact helper comparisons favor v1.44 as the measured older-family research candidate; historical compiler identity remains unresolved.

Use `python3 scripts/build_reconstruction_candidate.py` with the same manifest/program/output arguments as the historical helper. It supplies explicit v1.44 for Pump/AMM/Fees or v1.52 for Mayhem unless `--tools-version` is provided. The byte-preserved historical helper retains its original v1.52 fallback to keep accepted source-build package hashes valid; existing published commands already specify their version. An explicit alternate experiment remains separate evidence and does not promote an artifact automatically.
