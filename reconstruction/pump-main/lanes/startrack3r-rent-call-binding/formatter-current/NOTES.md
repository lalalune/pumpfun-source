# Current formatter span and the V3 compiler boundary

The source fix is upstream [PR #2272](https://github.com/lalalune/pumpfun-source/pull/2272),
lane `w7r1-v3buycosts-blockorder`, head
`fcce9275e35c1cb6685a83c40d70b84c9caa91fd`. This packet independently verifies
that change with the retained Windows v1.44 recipe and measures its contribution
to the formatter span. It does not propose or claim authorship of that source.

| Compiler output | Source revision | V3 bytes | Normalized / raw windows | Formatter span excess |
| --- | --- | ---: | ---: | ---: |
| Fresh v1.44 main | `2162b3b0041077af8593b0701c8471a157b30e08` | 2,136 | 1,027 / 273 | 640 B |
| Fresh v1.44 main after #2255 | `2b8582135d33f498db4c30d8309447573baebb9c` | 2,136 | 1,027 / 273 | 640 B |
| v1.44 PR #2272 | `fcce9275e35c1cb6685a83c40d70b84c9caa91fd` | 2,120 | 1,028 / 273 | 624 B |
| Full v1.43 recipe, root paths corrected | `2162b3b0041077af8593b0701c8471a157b30e08` | 2,288 | 241 / 72 | Original callee binding absent |

The original V3 window at `0x80df8` is 2,120 bytes. The PR #2272 output gains
exactly that normalized window, loses none, and preserves all raw memberships.
Branches, registers, stack offsets, syscalls and scalar literals remain exact;
only internal call displacements and section-pointing LDDW operands are masked.
All 17 actual call targets independently bind to complete original normalized
callee bodies, at the same caller offsets. A deliberately wrong call target
preserves normalized bytes but is rejected by the verifier. No modified image
is executed or represented as compiler output.

The original formatter is the 24-byte thunk at `0xa868`, calling the 1,088-byte
body at `0x1a25b0`; its span is 1,670,472 bytes. Binding that complete callee
selects one of seven normalized thunk candidates. Fresh main's bound thunk is
at `0xa820` and its callee at `0x1a2828`; #2272 moves only the latter endpoint
to `0x1a2818`. Complete normalized-body multiplicities partition each interval
without gaps. The span improves **640 -> 624 bytes**, and total `.text` excess
improves **568 -> 552 bytes**. A historical 112-byte measurement must not be
reported as the current main's measured span. Subtracting the known extra
512-byte rent wrapper from 624 gives 112 arithmetically; the composition with
the separate upstream #2168 source change was **not built in this packet**.

## Adjacent compiler experiment: rejected, with an instruction-level reason

The downloaded v1.43 Windows compiler and Linux target libraries are recorded
by archive SHA-256, release asset URL/ID and complete extracted file inventories.
The release API supplied no asset digest; our hashes are observations of the
downloaded bytes. They are not historical compiler authentication. Both compiler
executables print Rust 1.79.0-dev / LLVM 18.1.7, but have different driver bytes,
target names and target defaults.

The compiler-only substitution failed: v1.43 does not recognize the v1.44
`sbpf-solana-solana` target name. A separate fresh Cargo build used v1.43's
`sbf-solana-solana` target, matching standard libraries and freshly produced
dependencies. Replaying its actual root command with the same 59 filename
remaps as the control did not rescue the result: **786 normalized losses,
201 raw losses, no gains**, and `.text` grew to 90,864 bytes over the original.
This comparison changes the complete recipe, not just the compiler executable.

There is a concrete feature mismatch behind the rejected direction:

- The deployed V3 window contains 24 immediate-store instructions; its entire
  `.text` contains 8,535. Both v1.43 outputs contain zero in `.text`.
- The recorded v1.43 target defaults are `+solana`; v1.44 defaults are
  `+store-imm,+jmp-ext`. The observed feature lists are retained.
- In the associated immutable LLVM source trees, v1.43's complete
  `SBFInstrInfo.td` has register-store patterns but no `STORE_imm` class.
  v1.44 has `STORE_imm_V1` and selection patterns gated by `SBFHasStoreImm`.
  Complete source files and provider Git-blob receipts are included; the
  verifier checks those Git object hashes, including the absent terminal
  newline in both feature files.

These observations reject the tested stock v1.43 recipe. They do not identify
the deployed program's historical compiler, exclude custom compiler builds,
or prove that every byte of the regression comes from one feature. The
separate #2272 source fix succeeds with the qualified v1.44 recipe.

## Replay and retained evidence

Build outputs stay outside Git. `PRODUCTION.json.gz` records the exact source
file hashes/Git blobs, commands, environment, dependency inputs, compiler and
library inventories where measured, and before/after checks. `COMPILER-LOGS.json.gz`
retains success and failure logs. `CONTROLLERS.json.gz` retains the lane-local
build/measurement scripts; their absolute paths and externally retained caches
are requirements, not a clean-machine bootstrap claim. `SUMMARY.json` gives
exact image hashes; `MEMBERSHIPS.json` includes every matched address, not just
counts. Seven root compiler invocations include one target-name failure; the
fresh v1.43 build also runs 119 target dependency and 90 host rustc commands.
No target/VM/live-chain execution occurred.

The earlier v1.43 preflight stopped before compilation because the optional
`CC_sbf_solana_solana` path was unavailable. The retry removes that variable;
the retained AR path exists. The initial broad CC/AR wording in the ledger is
corrected here by the actual retry's `removed_unavailable_optional_tools` map.
The shared POSIX live ledger was not accessed on Windows; the 1,166-row tracked
snapshot and schema-valid local attempts were checked instead.

With the five hash-pinned images in their recorded folders, the original
allocation capture, the pinned function inventory and five scorer modules:

```text
python verify_current.py --images <pump-formatter-current> --original <deployed.so> --inventory <functions.tsv> --harness <fresh-harness> --work <new-empty-directory>
```

The script requires the existing adjacent `../verify_rent_edges.py` from this
PR. It reads compiler outputs, reruns the complete scorer, binds the V3 calls
and formatter endpoints, checks physical interval accounting and verifies
backend-source Git blobs. Normal and optimized-Python runs produce the same
report. An independent static census also checks all 1,035 memberships.

An initial replay caught truncated feature-source copies caused by dropping
the final line when there was no terminal newline. Exact provider bytes were
restored, the Git object checks then passed, and the failed local files/log
remain in the work record. `VALIDATION.json` records checks and limitations.

The measured files are raw, unstripped compiler outputs. They are not padded
allocation images. Normalized V3 equality and reduced span do not establish
whole-output identity, runtime equivalence, completeness or security.
