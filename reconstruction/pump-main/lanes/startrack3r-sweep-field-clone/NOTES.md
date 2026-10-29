# Sweep recipient field clone

Base: `630a074126a13d4133514d599129c6ac9a3179bc`. Target: `0x72810`,
`sweep::execute`, 7,832 original bytes. This is a partial source improvement,
not a new normalized or raw window match.

The source uses the inline rent `Result` match and inline token admissions from
[PR1427's retained a37](https://github.com/lalalune/pumpfun-source/pull/1427).
That work already achieved ratio 0.78830, but left one extra out-of-line
`AccountInfo::clone`. The new change spells the recipient clone as the eight
field operations in `solana-account-info` 2.3.0's derived `Clone`, at the same
argument evaluation site. Its two `Rc::clone` operations can inline separately.
The resulting function has the original complete immediate-callee multiset.

| Measurement | Base | Candidate | Original |
| --- | ---: | ---: | ---: |
| Official normalized / raw windows, local recipe | 1023 / 273 | 1023 / 273 | 1035 windows |
| Target instruction ratio | 0.49139 | **0.78905** | 1 |
| Target bytes | 7824 | 7392 | 7832 |
| Internal calls / syscalls | 37 / 2 | 37 / 2 | 37 / 2 |
| Complete normalized immediate-callee multiset | equal | equal | reference |
| Sequence edit instructions | 557 | 276 | 0 |
| Positional differing 8-byte slots | 814 | 588 | 0 |

All normalized and raw membership sets are preserved. Ratios and positional
counts are diagnostics; the shorter target is still unmatched. Callee order
is not equal. Neither multiset equality nor these measurements establish
recursive behavior, runtime equivalence or security. The local raw count is
273; do not substitute the native host's reported 277.

Two separate candidate root compilations on this base produced the same complete
2,664,584-byte compiler output:
`a0684ea31b42a12334be3a93fdbc55d684f39e1f1f1a052aaa3b54ab7c0672fc`.
The 2,665,192-byte control is
`899b5b77da7a105b29aec334b862d39575a4e0f73b437ddb7f2d8f90353bdbd7`.
These are compiler outputs, not the 10,485,715-byte original allocation capture.
Outputs and large pass dumps remain outside Git, as required by the lane rules.

## Why the previous join failed

Passive before/after inliner captures on source cohort `2c8a7900f` reproduce
each corresponding complete compiler output byte for byte. The pinned SDK's
`opt` runs only block-frequency analysis on the complete captured modules,
retaining their target triple, globals, attributes and metadata.

The recipient clone's estimated frequency relative to function entry is:

| Source | Frequency | Below LLVM's 2% boundary? |
| --- | ---: | --- |
| Retained a37 | 0.01468658447265625 | yes |
| Serial admission `Result` match in execute | 0.01468658447265625 | yes |
| Merged helper-based control | 0.02536773681640625 | no |

The serial match still lowers to two separate admission-success checks before
inlining. It changes storage and layout without lifting that frequency; its
ratio is 0.70427 and the extra clone remains. This failed control is retained
in `SUMMARY.json`. Changing optimizer thresholds is not proposed.

The field clone copies `key`, `owner`, `rent_epoch`, `is_signer`, `is_writable`
and `executable`, and clones the existing `lamports` and `data` Rc handles in
declaration order. It does not borrow or deep-copy account data. The existing
unused `ensure_rent_exempt` definition is left in place as in a37; it emits no
additional target function. Constraint coordinates and evaluation-site lines
are retained.

## Reproduce

Build the pinned base and this branch with the normal identity recipe from
`reconstruction/README.md`, into separate work and output directories. For example,
with a separate base checkout:

```sh
python3 reconstruction/harness/fastbuild.py --src /path/to/base/programs/pump --work /tmp/sweep-base-work --out /tmp/sweep-base
python3 reconstruction/harness/fastbuild.py --src programs/pump --work /tmp/sweep-candidate-work --out /tmp/sweep-candidate
python3 reconstruction/pump-main/lanes/startrack3r-sweep-field-clone/verify.py \
  --control /tmp/sweep-base/unstripped.so \
  --candidate /tmp/sweep-candidate/unstripped.so \
  --work /tmp/sweep-static-check
```

The verifier uses the unmodified official scorer and `win.py` instruction tokens.
It checks the original capture and inventory hashes, creates a fresh original
cache, checks every original-window membership, and binds every immediate callee
to a complete original normalized body before comparing multiplicities. It also
compares syscall instructions. `--work` must not already exist. Use `--objdump`
for a local SDK executable path, `--original` for a sparse checkout's capture,
and `--repeat` to require complete candidate-output equality with another build.

Local validation passed all these checks and the byte-identical repeat. As a real
negative control, supplying retained a37 as candidate fails specifically on its
extra callee-body occurrence. No captured program, transaction or VM was run.
Exact revisions, hashes, source inventories and diagnostic limits are summarized
in `SUMMARY.json`; native-host replay remains for maintainer review.
