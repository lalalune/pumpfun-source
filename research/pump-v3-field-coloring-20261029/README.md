# V3 costs: scheduler order and field register allocation

The two remaining normalized stack-load differences in the prior diagnostic
can be explained jointly by scheduling and register-allocation order. With
the previously retained **synthetic branch weights**, one private scheduler
decision reversal and two private field-priority replacements, the compiler
emits a **2,120-byte function equal to the original after relocation operand
normalization**. The emitted object was retained without binary patching.

A follow-up below replaces the private field-priority patch with LLVM's
existing `-greedy-reverse-local-assignment=true` option and reproduces the
**same complete object**. The private scheduler intervention and synthetic
profile are still required by this demonstrated diagnostic recipe.

**Raw equality is false.** This is a diagnostic experiment, not recovered Rust,
an original compiler recipe, a maintained-source window gain, or whole-ELF
identity. No production source, selected image, or census is changed. The next
source/provenance problem is how to obtain this order with a justified source
and compiler recipe, without the private interventions.

## Inputs and replay

This packet extends the merged [allocator/cost packet](../pump-v3-regalloc-20261029/README.md)
and [source/branch packet](../pump-v3-branch-layout-20261029/README.md).
It uses their pinned inputs rather than rebuilding current `main`.

- Rust revision: `08b7341888ab480dfaaa0698300cbbbbb2d75b53`.
- Anza LLVM revision: `08aedd64bf3abe4f163407b7bcf680403b84b32d`;
  LLVM 18.1.7, assertions enabled, SBF backend, Windows host.
- Function: `_ZN14pump_recovered5trade12v3_buy_costs17h280dba79c4dad174E`.
- Original extent: `0x80df8`, 2,120 bytes in `evidence/original/pump/deployed.so`;
  original SHA-256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`.
- Original source candidate remains 2,136 bytes / 23 differing aligned slots.
  The synthetic profile adds weights `1:16777215` to one panic branch in
  extracted IR. It is not evidence that the original build used PGO.

From the repository root, Python's standard library is sufficient:

```sh
python -I -B research/pump-v3-field-coloring-20261029/verify.py --repo-root .
python -I -B research/pump-v3-field-coloring-20261029/test_verify.py -v
python -I -B research/pump-v3-field-coloring-20261029/test_stock_priority.py -v
```

Replay reads the three packets, the original capture, and
`repro/reconstruction-status-2026-10-26/functions.tsv`. It checks both parent
packets recursively. It runs pure retained Python analysis/patch functions,
but no build controller, compiler, ELF, VM, or network command. It refuses
`-O`, because some inherited readers use assertions. Private Windows paths in
historical recipes need not exist. Host compiler binaries/libraries are not
distributed; their hashes and build receipts are retained, so this replay
does **not** attest a fresh compiler rebuild.

## Why load order alone regressed

The net-error block is tied to source line 375 and its full closure label,
not a guessed block position. `SelectionDAGBuilder` creates the hidden-sret
result loads in aggregate field order. The trace identifies two result stores
whose equal-priority tie uses queue IDs 4/5. Their bottom-up scheduled cycles
4/5 determine successor distances for load nodes 5/36 (frame 17, offsets 0/8).
The load comparison is `BURRSort:LDist < RDist`, with distances 4/5; it is not
a queue-ID tie between the loads.

The opt-in `-v3-diagnostic-reverse-loads` intervention changes exactly that
actual queue comparison. The remaining 38 scheduled positions in the
40-node block stay unchanged. Default-off objects and complete traces equal
their stock controls after removing only the added logging and printed
BasicBlock addresses; branch probabilities and instructions remain literal.

Reversing the load pair alone makes the first virtual register `%100` carry
field 8 and the second `%101` carry field 0. Greedy still assigns the first to
`r1` and the second to `r2`. This reverses the semantic field-to-register map,
so the branch folder cannot share the existing result-store tail. Saved
pass dumps show the separate stores and return-pointer reload. With synthetic
weights this grows the function to 2,144 bytes / 9 differing slots.

## Local priority, independent of spill weight

These intervals are local, unhinted, in `RS_Assign`, and use forward local
assignment. The pinned `DefaultPriorityAdvisor` chooses priority by distance
from interval start to the last SlotIndex. The enum in `SlotIndexes.h` has
four slots; the high assignment bit is `1 << 31`.

| Register | Start | Last | Priority calculation | Priority |
| --- | ---: | ---: | --- | ---: |
| `%100` | 6352 | 7040 | `2^31 + (7040 - 6352) / 4` | 2147483820 |
| `%101` | 6368 | 7040 | `2^31 + (7040 - 6368) / 4` | 2147483816 |

The baseline second interval has infinite spill weight, but is still queued
second. In this path spill weight does not decide this local priority. The
first interval obtains `r1` without interference; the second finds `r1`
occupied and takes `r2`. There is no equal-priority register-number tie here.

The opt-in `-v3-diagnostic-field-priority` control applies only to this exact
function and the reversed frame-17 field pair. It substitutes the other
interval's local distance while preserving the high priority bits. `%101`
(field 0) then receives `r1`, and `%100` (field 8) receives `r2`. The emitted
load order is field 8 into `r2`, then field 0 into `r1`, preserving the shared
tail. The two replacement events and three interference observations are
checked against the complete retained Greedy trace and rewritten instructions.

These private switches are exact-input diagnostic devices, not general
compiler optimizations or proposed upstream LLVM changes.

## Measurements and failed controls

Distances compare complete instruction sequences in aligned eight-byte slots
using the inherited metric; normalization masks only the 17 relocated direct
call immediates and 16 relocated data-address operands.

| Retained control | Target bytes | Differing normalized slots |
| --- | ---: | ---: |
| Qualified source / stock baseline | 2136 | 23 |
| Synthetic profile / stock | 2120 | 2 |
| Scheduler reversal, baseline | 2152 | 26 |
| Scheduler reversal, synthetic profile | 2144 | 9 |
| Field switch on with scheduler off (guard inactive) | 2120 | 2 |
| Both switches on, synthetic profile | **2120** | **0** |
| Stock `-post-RA-scheduler=true`, baseline | 2136 | 71 |
| Stock `-post-RA-scheduler=true`, synthetic profile | 2120 | 52 |

The final **whole emitted object** SHA-256 is
`2dc620ca0dae357214ce7af9c3b7af8fade5a622fd3716357625aba40821b527`.
This is not a linked program or allocation image. The final private compiler
SHA-256 is `d405c5a1e36b29b9579c63bb3ba754585eae2643e2c5235a9c019ae7e94efc75`.
Complete per-run compiler, input, controller, command, environment, log and
object bindings are verified, including all default-off controls.

The first field-priority implementation queried the other register's full
priority advisor before that register had been enqueued. The private build
asserted `index out of bounds!` in `IndexedMap.h`, exited with 2147483651, and
emitted no object or intervention marker. Its source, controller, logs,
stack trace and result remain in `fields/scheduler1-priority1` and
`fields/derivative01`. This is a diagnostic implementation failure, not a
claimed stock LLVM defect. The repaired derivative computes the already
qualified local distance without reading or changing the other register's
uninitialized allocation stage. Its default-off and inactive-guard controls
still reproduce the complete parent objects and traces.

The initial experiment retains 22 `llc` attempts (one failure), 12 host
compile/archive/link commands, and 21 emitted objects. It adds no root Rust
compilation and executes no target program. The older scheduler analysis
receipt predates the successful combined control; its negative conclusion
describes the scheduler-only experiment and is intentionally preserved.

## Replacing the private field-priority patch

The pinned `GreedyReverseLocalAssignment` option is a stock override of
`TargetRegisterInfo::reverseLocalAssignment()`; SBF inherits the default
`false`. With the option enabled, the local priority uses the interval's
**end** distance from zero instead of its **begin** distance from the last
index. This is not simply an inversion of the previous priority number.

For the scheduler-reversed pair, `%101` ends at 6400 and `%100` at 6384.
Their derived priorities are `2^31 + 6400/4 = 2147485248` and
`2^31 + 6384/4 = 2147485244`. Saved Greedy records select `%101` first into
`r1`, then `%100` into `r2`. There is no private field instrumentation or
field-priority switch in this run. Its compiler is the earlier scheduler-only
derivative (`89fcc76c5c3c94613ff93984a0afee87628a64fad499d0c54ece3dc88547032f`).
The complete emitted object equals `2dc620ca...b527` from the repaired
two-intervention experiment, including its relocation and constant data.

Nine further `llc` controls bind this result:

| Input and scheduler | Reverse-local false | Reverse-local true |
| --- | --- | --- |
| Baseline IR / stock compiler | 2136 bytes / 23 slots | identical complete object |
| Synthetic profile / stock compiler | 2120 bytes / 2 slots | identical complete object |
| Synthetic profile / private reversed scheduler | prior 2144 bytes / 9 slots | 2120 bytes / 0 slots |
| Reversed IR stores / stock compiler, baseline | 2152 bytes / 26 slots | identical complete object |
| Reversed IR stores / stock compiler, synthetic profile | 2144 bytes / 9 slots | identical complete object |

The last two rows revisit the previously rejected store-order alternative.
Only two disjoint eight-byte result stores at offsets 8/16 change order;
their pure address definitions retain valid numeric SSA order. That change
also reverses the uses, leaving the first field's interval ending at 6400 and
the second at 6384. The reverse-local option therefore still assigns the
first to `r1` and fails to rescue this alternative. These are manually edited
IR controls, not generated Rust candidates. Both failed alternatives remain
in the packet alongside the positive control.

`verify_stock_priority.py` checks all nine complete object receipts, exact
input changes and supported options, observed allocation order, derived
priorities, and 33 ordered references/13 constants per object. Nine additional
mutation tests reject forged endpoints, colors, hidden private instrumentation,
extra input changes/flags and mismatched compiler/input hashes. The combined
packet has 31 `llc` attempts, 30 emitted objects, the same 12 historical host
build commands, and zero root Rust compilations or target executions. A
compiler option reproducing one effect does not establish original build flags.

## Evidence boundary

`EVIDENCE.json` binds 252 gzip members by uncompressed length/hash;
`MANIFEST.json` seals the packet. `verify.py` recomputes the measurements,
formula, trace controls and exact field/source patch applications. It binds
all 33 ordered function relocation targets and 13 complete recursively
referenced constant objects back to the qualified extracted object. The
post-RA controls are measured separately because scheduling may reorder sites.
External function references remain symbolic at the object stage. The parent
packet supplies the bounded original/candidate reference audit; this does not
prove arbitrary callee behavior or whole-program identity.

The initial 16 mutation tests exercise actual saved traces and recipes: forged local
priorities/endpoints/hints/colors/interference, duplicate or missing events,
unparsed interventions, extra compiler flags, changed environment and hashes,
and overly broad log/address filtering. A fresh minimal-directory replay also
passes with the nine follow-up tests and the two parent packets' 38 tests
(63 tests total).

No behavior test, raw-byte match, original compiler provenance, allocation
image identity, completeness, or security conclusion follows from this
normalized diagnostic match. Recovering a justified source/compiler recipe
and then qualifying a normal linked build remain open.
