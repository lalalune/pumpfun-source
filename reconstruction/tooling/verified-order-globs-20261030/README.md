# Admit the maintained optional text-order recipe in the verified builder

The verified builder rejected the repository's actual
`programs/pump/link/ordered.ld` before invoking Cargo. Its selector validator
allowed neither the digest wildcard inside object names nor the bare `*`
object selector, and rejected the script's object-scoped `(.text*)` catch-all.
All 555 maintained selectors failed admission.

The change admits those existing forms while retaining the default SDK script's
exact head/tail, final catch-all, duplicate checks, and text-only selector scope.
Quoted section names retain their previous grammar. The only unquoted section
form is the literal `.text*`. Linker selection, bound inputs, receipts, response
file rejection, and attached-script rejection are unchanged.

This is builder interoperability, **not a new recovery or an improved native
recipe**. On the measured Linux build, the optional maintained ordering loses
183 raw memberships. It is not proposed as a new default.

## Actual before and after

Frozen source revision: `43daa2043fb4a87838d715ab61467e4213d76d66`.
The only product changes are the validator and its tests. The program sources,
maintained order file, SDK and scorer remain unchanged.

The unpatched real CLI used the actual source, workspace staging, native Linux
v1.44 SDK, locked registry and maintained order file. It exited 1 with
`AssertionError: unexpected linker statement`; Cargo had not started.
`before.stderr.txt` changes only the local checkout prefix to `<repo>`.

With the patch, that invocation completed a fresh cold build in 100.12 seconds,
admitted 555 selectors, and retained a linker receipt binding 123 inputs and the
actual replacement script. A separate fresh default-order cold control on the
**same source revision**, SDK, registry and checkout completed in 99.80 seconds.
Their complete primary-source hash maps are equal and both builds report source
unchanged. Both controls use the patched tooling; only the optional ordering
argument differs. The validator is not invoked on the default path.

| Same-source native Linux control | Normalized / total | Raw |
| --- | ---: | ---: |
| Default order | 1032 / 1035 | 323 |
| Optional maintained order | 1032 / 1035 | 140 |
| Membership changes | 0 gains, 0 losses | 0 gains, **183 losses** |

The full membership lists, raw-loss addresses and hashes are in the two score
files and `measurement.json`. The default ELF also equals the independently
retained earlier Linux baseline, but that cross-revision observation is not the
control used for the table.

## Reproduce

Use an authenticated native Linux x86-64 v1.44 SDK and the locked Cargo registry;
this packet neither installs a toolchain nor downloads dependencies. The archive
SHA-256, tool hashes, full build receipts and all 2,777 SDK-entry checks are
retained. The SDK inventory was unchanged after both builds.

`commands.json` preserves the three argv arrays, substituting only `<repo>`,
`<sdk>`, `<registry>` and `<python>` for local installation paths. Use fresh output
directories. The ordered invocation is:

```sh
python -B scripts/pump_build_verified.py \
  --source-directory "$PWD/programs/pump" --workspace-layout \
  --sdk "$SDK" --registry-home "$REGISTRY" --target sbpf-solana-solana \
  --text-section-order "$PWD/programs/pump/link/ordered.ld" \
  --output "$PWD/work/ordered-after"
```

For the same-source default control omit `--text-section-order` and its value,
and select `work/default-after`. Score with the unchanged official scorer:

```sh
python -B reconstruction/harness/score.py work/default-after/unstripped.so \
  --no-baseline --json work/default-after-score.json
python -B reconstruction/harness/score.py work/ordered-after/unstripped.so \
  --baseline work/default-after-score.json --json work/ordered-after-score.json
```

Ubuntu/WSL2, Python 3.12.3, SDK rustc 1.79.0-dev, Cargo 1.79.0 and LLVM
18.1.7-rust-dev were used. `measurement.json` binds exact files and tool inputs.

## Validation and limits

```sh
python -B -m unittest discover -s scripts -p test_pump_text_layout.py -v
python -B -m unittest discover -s tests -p 'test_text_layout*.py' -v
python -B -m unittest discover -s scripts -p test_tooling.py -v
python -B scripts/verify_evidence.py
```

Results: 5 canonical/admission tests, 7 existing receipt tests, 193 tooling
tests, and all 9 captures pass. The added tests consume the actual maintained
script, reject non-text selectors, arbitrary statements and punctuation, and
preserve scaffold and duplicate checks. Existing controls continue to reject
changed bound inputs, script hashes, unbound operands and attached `-T` scripts,
including optimized Python modes.

No captured binary was executed. No program-byte gain, whole-ELF identity,
runtime/VM validity, macOS equivalence, default-recipe change or post-link byte
editing is claimed. The optional script's suitability for native Linux remains
a separate recipe question; this fix makes its legitimate input syntax usable.
