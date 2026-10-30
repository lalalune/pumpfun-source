# V2 rent call binding beyond window membership

This research packet explains an extra 512-byte function and three mismatched
immediate callees in actual compiler output from main
`fd8b94dfa3a0ec671e018a5418c4b5009e26da6a`. It changes no program source,
compiler, scorer or captured binary. The retained source experiment is credited
to **Oz-0s, [PR #1384](https://github.com/lalalune/pumpfun-source/pull/1384)**,
head `bb23029765d838728e50ad3abdc5b7e14117bfc7`; we did not invent the zero-only
type. Our contribution is a current-main rebase, fresh compiler/repeat evidence,
actual call-target verification and accounting for the formatter span.

## Finding

Main contains the alternative rent representation from merged #1383: a
416-byte matching twin and a separate 512-byte helper. The original function
at `0x3b598` is 416 bytes. All three actual V2 callers in our current-main
compiler output call the **512-byte** helper at `0x442e0`, although the twin
at `0x44140` satisfies the scorer's normalized window membership. Sell V2's
caller is itself normalized-exact. Normalized window membership masks direct
call immediates and does not establish which complete function a call reaches.
This is an observed reconstruction difference, not a security finding.

The experiment rebases only #1384's `ZeroRentSize` helper and its three call
arguments. The helper's bytes are identical to Git blob
`2f94c35629c3a492d5f89454db260ead24fae803` from #1384. Both caller files retain
their current-main line counts and all other main source remains unchanged.
`pr1384-rebase.patch.gz` retains this source experiment for review; it is not
applied to `programs/` by this PR.

| Original caller | Call ordinal (zero-based) | Caller byte offset | Main target | Experiment target |
| --- | ---: | ---: | --- | --- |
| Buy V2 `0x13b9b8` | 55 | 9024 | `0x442e0`, 512 B | `0x44140`, 416 B |
| ExactQuote V2 `0x13f630` | 95 | 13632 | `0x442e0`, 512 B | `0x44140`, 416 B |
| Sell V2 `0x144508` | 56 | 9168 | `0x442e0`, 512 B | `0x44140`, 416 B |

All three experimental rent callees match the **complete normalized** original
416-byte body, SHA-256
`72e7b88eae9ab86100cc80db413ee9d0ac1658d34635417f9d2f9a5b33100825`.
Every caller's normalized body remains unchanged from the control. All three
complete immediate-callee multisets now equal the original. ExactQuote V2's
130 and Sell V2's 80 ordered callees also equal the original. Regular Buy V2's
90 callees still differ in order; its equality is a multiset result only.
These are one-hop normalized body checks, not recursive or runtime equivalence.

## Fresh compiler results

| Source / local build | Normalized | Raw | Formatter span delta |
| --- | ---: | ---: | ---: |
| Historical main `1e04f5b34` | 1026 | 273 | +360 B |
| Historical main + #1384 rebase, exact repeat | 1026 | 273 | -152 B |
| Fresh main `fd8b94dfa` | 1027 | 273 | +392 B |
| Fresh main + #1384 rebase, exact repeat | 1027 | 273 | -120 B |

Each candidate preserves every normalized and raw membership across **1,035
windows** compared with its own fresh control: zero gains and zero losses.
The fresh pair is independently checked with a second ELF census. The current
unmodified scorer from `fd8b94dfa` reproduces both historical and fresh pairs.
The additional normalized membership between the two controls comes from
upstream source work, not this experiment.

Fresh unstripped compiler outputs:

- Main: 2,666,064 bytes,
  `09186a9021ba057d53d37b55e7d28c55415417995999c2d3e2006b943b09521a`.
- Candidate and independent repeat: 2,665,296 bytes each,
  `b500fc7f61fbd93258bb83cfa27c9105a7b05818c4c81fe08a21b2cb50a9a06f`.

The **entire candidate compiler output equals its repeat**. This is distinct
from the captured 10,485,715-byte original allocation image; no whole-original
equality is claimed. The local recipe uses Windows platform-tools v1.44 with
retained target dependencies. It is not the native Linux recipe and does not
establish native raw-membership preservation.

The complete physical normalized function-body multiset changes only by
deleting the extra 512-byte rent body. No other body class is added or removed.
The `.text` section shrinks by exactly 512 bytes; `.rodata` is byte-identical.
The whole file shrinks by 768 bytes, which includes symbol/string-table and
layout differences; that is not a 768-byte code-size change.

## The remaining formatter gap

The original formatter at `0xa868` calls `0x1a25b0`, a 1,670,472-byte span.
Seven normalized formatter candidates exist in each image. The verifier binds
the single one whose **complete 1,088-byte callee** matches the original before
measuring the span; it does not select a convenient unrelated 24-byte wrapper.
The fresh main span is 1,670,864 bytes; the experiment is 1,670,352 bytes.
Neither is raw-equal to the original formatter. **A 120-byte deficit remains.**

`RENT-CALLS.json` partitions each bound span into complete physical function
intervals with no gaps or overlaps and retains missing/extra normalized class
multiplicities. Removing the extra rent body accounts for the exact -512-byte
span change. No padding, emitted-byte edit, metadata search or toolchain change
was used. Historical measurements are separate in `HISTORICAL.json`.

## Verification and reproduction

`verify_rent_edges.py` uses explicit checks, including when run with `python -O`.
It pins the original allocation, inventory, local control and scorer modules;
the candidate is verified structurally rather than accepted by a fixed hash.
It freshly scores both images, checks all memberships, follows the actual
three call sites, checks caller/callee bodies and multiplicities, verifies the
physical-class deletion, binds the formatter span and requires whole-repeat
byte equality. It performs no compiler, VM, target or network operation.

With the retained compiler outputs and a copy of the **unmodified harness at
`fd8b94dfa`** (`score.py`, `score_admission.py`, `elf_symbols.py`, `llvm_tools.py`):

```sh
python3 -I -B verify_rent_edges.py \
  --control /path/to/03-main-fd8b94d/symbols.so \
  --candidate /path/to/04-zero-fd8b94d/symbols.so \
  --repeat /path/to/05-repeat-fd8b94d/symbols.so \
  --original /path/to/evidence/original/pump/deployed.so \
  --inventory /path/to/functions.tsv \
  --harness /path/to/fd8b94d-harness \
  --work /path/to/new-empty-report-directory
```

Use the selected Pump inventory formerly at
`repro/reconstruction-status-2026-10-26/functions.tsv` (available at Git commit
`aa8ffc2801b67c0be38506a678a09c571f24ee39`), SHA-256
`fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8`.
Do not substitute a current inventory without checking its identity.
Compiler outputs remain outside Git, following the lane rules. This packet
does not distribute the 207 cached dependency artifacts or claim a clean
dependency rebuild. Reproducing these exact local ELF hashes requires the
recorded local recipe and dependencies, not merely the program source patch.

`BUILD-INPUTS.json` records compiler argv/environment (with `${WORK}` replacing
the absolute work directory), tool/dependency hashes, all 100 fresh source
inputs, 95 base Git blobs, the exact patch, output hashes and compile receipts.
Five root compiler commands were run for this increment: two historical
candidate/repeat builds and three fresh-main control/candidate/repeat builds.
All returned success with no stack-offset/frame diagnostics. No dependencies
were rebuilt and no target program executed. Applying the exact retained
source patch to each base reproduces every candidate source-input hash.

Normal and optimized verifier reports are byte-identical. Two real negative
controls fail as required: (1) using unchanged main for both candidate and
repeat, despite equal aggregate scores, fails on the actual rent callee;
(2) using main as the candidate's repeat fails whole-image equality. The final
published verifier also replays both source revisions with the current scorer.
`VALIDATION.json` retains checks and exploratory failures. In particular, an
attempt to interpret every `.data.rel.ro` relocation qword as a direct virtual
address failed at offset zero; no data-referent or recursive closure claim is
made. All raw failure evidence remains local.

## Maintainer context and next step

The maintainer closed #1554 because its historical source composition had
already landed. That branch is preserved and is not reopened. The maintainer
[closed #1384 pending a fresh rebase and scoring run](https://github.com/lalalune/pumpfun-source/pull/1384#issuecomment-6514791592).
This packet supplies that new source-bound evidence and identifies a call-target
distinction hidden by equal window counts; it does not reopen or modify another
contributor's PR. No open zero-only/rent-helper source proposal was found in the
review before this contribution.

After these checks, main advanced to
`abfda9f14a99e03785e57afbb1e4018b1785219f`, including another `create_v2.rs`
change from #2154. The three rent-related source files and the four scorer
modules are unchanged, but that new main was **not rebuilt here**. All fresh
measurements in this packet remain bound to `fd8b94dfa`; they are not retargeted
to the later tree. This research-only branch contains no program-source diff.

Next work should account for the remaining -120-byte span under the qualified
fresh baseline, and obtain native compiler output before transferring local
no-loss conclusions. Program-source adoption of the credited #1384 hypothesis
is a separate maintainer decision. No completeness, historical-source
authentication, runtime equivalence or security claim is made here.
