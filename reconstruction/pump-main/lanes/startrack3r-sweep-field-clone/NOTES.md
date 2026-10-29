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

## Follow-up: newer source and the Rent-result boundary

Qualified newer main `03fa4494f36449cd8fd63e121f12ca40bf57090f` with the
same local recipe: **1024 normalized / 273 raw**, adding only `0x14a8a8`
from merged upstream #1549. There were no normalized or raw losses.

Independently replayed upstream [#1548](https://github.com/lalalune/pumpfun-source/pull/1548)
at `60914be2d6167a7e9a981e33cbccae696b0cc6fc`, applying its sweep file to
that newer main. Its p1 source is a stronger sweep candidate than this PR's
field clone. Both complete immediate-callee multiplicities and all local
window memberships are preserved. Credit for p1 belongs to #1548; its
reported native-host raw loss at `0xa868` remains unqualified here.

| Sweep source on newer main | Bytes | Ratio | Internal calls / syscalls | Original callee multiset |
| --- | ---: | ---: | ---: | --- |
| Merged main | 7824 | 0.49139 | 37 / 2 | equal |
| Upstream p1 | 7768 | 0.82199 | 37 / 2 | equal |
| Explicit Rent Result argument, inline(always) helper | 7800 | 0.82027 | 37 / 2 | equal |
| Same helper without inline attribute | 7592 | 0.80191 | 34 / 2 | differs |

The first new hypothesis passes `Rent::get()` by value to a helper that
matches the result and returns the existing top-up/error Result. It moves
the error branch after protocol-native handling, but its Rent payload
still copies only after the tag test. Actual ELF bytes show three stack
stores before that test in the original and zero in p1 or this helper.
The original branch is `jne r1, 0`; p1 uses `jeq r1, 0`; the helper restores
`jne r1, 0` but still has a different destination and missing stores.

Removing the attribute leaves an out-of-line helper: its first conditional
after Rent::get tests the helper's returned Result, so it is not the Rent
tag test. This variant fails the direct-callee multiset requirement. Both
variants retain all 1024/273 memberships, but neither is promoted. The
branch improvement alone does not establish the required copy placement.

`RENT-RESULT.json` retains exact source mutations, revisions, output/log
receipt hashes, all-window results and instruction bytes. Four isolated
root builds completed without stack-offset warnings; static source/tool/
dependency checks and official/independent scorer replays passed. Existing
source and the original SUMMARY remain unchanged. No target/VM execution,
native-host replay or new full normalized/raw window match is claimed.


## Follow-up: exact accounting for the raw formatter call span

The earlier local no-loss checks do not qualify the native raw `0xa868`
barrier. On the retained main `604917c16410d67d9b981305e28e160a93728f50`
control, **none of the seven normalized thunk matches is raw-equal**.
Only one calls a complete normalized body matching the original 1,088-byte
callee (`AccountInfo::fmt` in the candidate). Its span is already 112 bytes
short, before applying sweep changes. Both images still score **1024
normalized / 273 raw**, with every membership unchanged.

The original thunk at `0xa868` calls `0x1a25b0`: a span of 1,670,472 bytes.
The bound local thunk starts at `0xa820` in both outputs:

| Retained compiler output | Callee address | Span | Difference from original |
| --- | --- | ---: | ---: |
| Main `604917c` | `0x1a24f8` | 1,670,360 | -112 |
| Same main + upstream #1548 s6 | `0x1a2530` | 1,670,416 | -56 |

Every byte in each interval is accounted for by physical function bodies:
788 original bodies and 787 candidate bodies, with no gaps or overlaps.
Their multiset intersection contains 775 bodies / 1,534,192 bytes.

| Remaining contribution to span difference | Main | s6 |
| --- | ---: | ---: |
| Eleven unmatched function bodies, total size difference | -184 | -128 |
| 232-byte account-name helper inside candidate span, outside original span | +232 | +232 |
| 112-byte normalized formatter class: one fewer occurrence inside candidate span | -112 | -112 |
| 48-byte normalized formatter class: one fewer occurrence inside candidate span | -48 | -48 |
| **Total** | **-112** | **-56** |

The three matched classes have unchanged whole-image multiplicities. The
232-byte helper matches original `0x2bc0`; the 48-byte body matches original
`0xa8f0`. The 112-byte class has six whole-image occurrences, so this is a
**class multiplicity statement**, not an invented one-to-one assignment of
generic formatter identities. No historical generic type is established.

This explains why unchanged local membership cannot prove native raw
preservation: the local baseline lacks that raw match. It also separates
the remaining body-size work from the +72-byte boundary contribution. A
sweep-size change alone cannot be treated as a complete explanation of
the original/local span. This does **not** relax the official no-loss gate
or propose padding, emitted-byte editing, or metadata/hash fishing.

Credit: #1548 already identifies the sweep call-displacement interaction;
#1518 and #1555 document the same barrier in other lanes. The
`layout-order-census` / #1260 and `w3-raw-layout` / #1423 work already
identifies generic hash order and the account-name helper's wrong block.
This follow-up adds the complete two-image interval partition, callee
disambiguation and exact byte equation for our qualified local recipe.

`RAW-CALL-SPAN.json` retains all seven thunk matches, complete callee shape
hashes, the eleven unmatched bodies, boundary-class occurrences and input
hashes. Replay with Python's standard library and the existing scorer:

```sh
python3 reconstruction/pump-main/lanes/startrack3r-sweep-field-clone/verify_call_span.py \
  --original /path/to/original-allocation.so \
  --inventory reconstruction/base/functions.tsv \
  --control /path/to/retained-604917c-unstripped.so \
  --s6 /path/to/retained-604917c-with-s6-unstripped.so \
  --harness reconstruction/harness \
  --objdump /path/to/llvm-objdump
```

This is a **fixed-evidence verifier**: it requires the recorded local image
hashes and pinned scorer bytes, then recomputes the entire report. It
does not claim that a different host will reproduce these output hashes.
An independent ELF reader agrees on both partitions. Standalone and
optimized-Python replays pass; a real wrong-image input and a tampered
byte equation are rejected. This increment executes no compiler, target
program or VM, changes no reconstructed source, and claims no new raw or
normalized match. The original remains an allocation capture, not a raw
compiler image.
