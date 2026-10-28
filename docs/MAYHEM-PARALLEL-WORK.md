# Parallel Mayhem reconstruction work

The objective remains byte-identical Rust reproduction, including calls, data,
relocations and ELF layout. The [current Buy/Sell quote composition](../research/mayhem-quotes-current-recovery-20261027/README.md)
has **432/441 normalized windows: 100 raw-local, 332 normalized-only and 9
unmatched**. The unmatched windows total **107,952 original text bytes**.
Normalized body matches do not establish recursive semantic or whole-ELF equality.

## Independent lanes

These are independent work assignments, not a claim that workers are currently
running. Each lane needs a separate source directory and build cache. The main
agent integrates, verifies, documents and reviews incoming PRs while independent
source and compiler investigations proceed.

| Lane | Next scope |
| --- | --- |
| AMM trade and quote bodies | O0077 and O0079; cap/min selection, retained-reserve arithmetic, ownership and error flow |
| Legacy and V2 trade bodies | O0081–O0084; source ownership, fallible arithmetic and CPI error lifetime |
| Runtime and layout | O0210 → O0209 allocator-provider mismatch and seven transitive callers; remaining data/indirect-call closure, section layout and ELF equality |
| Integration | Preserve the 432-window parent, qualify combinations with fresh builds and signed local replays, synchronize documentation and PRs |

Sweep/burn work is outside the active scope. O0073 and O0076 are connected to the
sweep path and are not dispatched. [O0075 is statically attributed to SweepFeesAdmin](../research/mayhem-sweep-admin-attribution-20261027/README.md);
it receives no execution assignment here. Historical sweep evidence remains
available under its original artifact bindings.

## All remaining windows

The table is derived from the current packet's [441-row inventory](../research/mayhem-quotes-current-recovery-20261027/inventory.json).
Each unmatched original window occurs once. Body names are reconstruction
attributions, not authenticated original symbols.

| Window | Original start | Bytes | Remaining body | Lane |
| --- | ---: | ---: | --- | --- |
| O0073 | 65472 | 912 | Sweep fee-recipient helper / block placement | Paused scope |
| O0075 | 69192 | 8008 | SweepFeesAdmin; static wrapper attribution, body unmatched | Paused scope |
| O0076 | 77200 | 8400 | Sweep business body | Paused scope |
| O0077 | 85600 | 9736 | AMM Buy | AMM trade and quote |
| O0079 | 95848 | 17312 | AMM Sell | AMM trade and quote |
| O0081 | 113672 | 13848 | Legacy Buy | Legacy and V2 trade |
| O0082 | 127520 | 12992 | Legacy Sell | Legacy and V2 trade |
| O0083 | 140512 | 18648 | BuyV2 | Legacy and V2 trade |
| O0084 | 159160 | 18096 | SellV2 | Legacy and V2 trade |

## Closed windows and partial controls

The [quote-aware validator](../research/mayhem-trade-origins-validator/README.md)
closes O0095's complete 1,296-byte normalized body, with eight immediate callee
shapes and fourteen typed data references checked. The [staged initializer](../research/mayhem-initializer-current-recovery-20261027/README.md)
closes O0193's complete 960-byte normalized body through a real AccountInfo/key
snapshot. Its five immediate callee shapes and four typed data references agree.
These two windows are no longer pending lane assignments.

The [current Legacy Buy ownership composition](../research/mayhem-current-ownership-composition-20261027/README.md)
preserves the frontier. Its 13,784-byte body remains different from the original
13,848 bytes despite equal immediate-callee and Source profiles. Its 486 signed
pairs are bound to that exact artifact, not to every private source variant.

The [qualified Sell quote composition](../research/mayhem-sell-current-recovery-20261027/README.md)
closes O0093 with all 140 instruction slots, ten ordered immediate callee shapes
and ten ordered typed references checked. Two builds repeat and fresh trade and
initializer matrices pass. The earlier 124/140-slot controls and backend replay
remain negative evidence; they do not add another match. The [qualified Buy/Sell composition](../research/mayhem-quotes-current-recovery-20261027/README.md) also closes O0092 with all 157 slots, ten ordered immediate callees and ten typed references, without losing any earlier match. Its own repeat builds and fresh runtime matrices pass.

The [account-data cohort](../research/mayhem-account-cohort-complete/README.md)
checks 156 typed references. The [historical parser composition](../research/mayhem-historical-macro-current-20261027/README.md)
reproduces the allocation context with historical macro/event sources, but does
not authenticate the original framework. The later historical initializer
composition reaches 430 normalized / 141 raw windows separately; its raw gains
are not added to the current 430/100 row.

The [AMM handler controls](../research/mayhem-amm-handler-shape-controls-20261027/README.md)
retain nine source/compiler comparisons. Explicit AccountInfo copies and enum-valued
arithmetic recover the Sell immediate-callee multiset; evaluation-order changes
improve partial instruction alignment. The full body and ordered callees still
differ. These controls add no accepted match or runtime qualification.

The [native historical-macro quote composition](../research/mayhem-native-current432-composition/README.md)
repeats 432 normalized / 85 native raw-local windows with its own 2,496 signed
trade pairs and 69 initializer pairs. It retains the earlier 13,680-byte Legacy
Buy body; it is not promoted over the qualified 432/100 source.

The [fresh Linux closure follow-up](../research/mayhem-direct-call-closure-20261027/README.md#fresh-linux-follow-up)
repeats the same 414-window relation and the same 18 unclosed windows on two
fresh-dependency artifacts. The allocator task remains an actual call-target
problem; merely rebuilding the previous source with a fresh cache did not fix it.

The [independent allocator composition reproduction](../research/mayhem-allocator-call-closure/README.md)
repeats PR295/296's complete native artifacts from two empty dependency target
directories. It provides an executed portable build recipe, current curve/root
optimized IR comparison and fresh initializer qualification. Its 432 normalized,
85 native raw and 422 direct-closed counts are inherited source results, not
additional recovery. The separate qualified 432/100 layout and ten unmatched
handler-dependent call relationships remain unresolved.

## Integration requirements

Preserve every prior normalized/raw match, immediate call shape and Source
profile, then verify referenced data and transitive/indirect callees separately.
Search builds use content-based local-package invalidation and isolated caches;
they reuse pinned dependencies and are not fresh full-dependency builds.
Acceptance requires ordinary Rust compilation, repeatable artifacts and signed
local execution evidence bound to the composed source. No assembly substitution,
dummy operations, invented padding or executable patching is an identity result.

Finite local replay does not establish exhaustive behavior or current-chain
acceptance. Source-coordinate and compute-log normalizations must remain
explicit for each packet. Whole-ELF identity remains false.

## Ordered direct-call audit

The [qualified-parent direct-call relation](../research/mayhem-direct-call-closure-20261027/README.md)
retains 594 of 722 normalized pairs, covering 414 of the 432 body-matched
windows. Eighteen windows have no direct-closed counterpart: ten depend on
unmatched handlers, and eight on an allocator-provider mismatch rooted at
O0210. O0209 has a matching body elsewhere, but O0210 calls a different
`finish_grow` specialization. This adds a target-by-target recovery obligation,
not a new body match or semantic-equivalence claim. Indirect/data closure and
whole-ELF identity remain open.

The [Legacy Sell signer-seed controls](../research/mayhem-signer-seed-order/README.md)
trace a current-source evaluation-order difference: moving the signer-bump read
after CPI account construction moves its instruction offset from 1,968 to
6,144, versus 6,296 in the original. The repeated inline control remains an
unmatched 12,952-byte body versus 12,992 original bytes. All 432/77 native
matches and 4,314 positive immediate-call observations remain; the qualified
432/100 artifact is separate. This is source-order research with no new complete
match, runtime qualification or checkpoint promotion.

The subsequent [arithmetic-lowering controls](../research/mayhem-signer-seed-order/composition/arithmetic/README.md)
bind the early multiply/divide difference to actual compiler stages. Reusing
the existing overflow-tuple price form restores price-before-guard ordering,
including with late inline seeds, but leaves the original branch layout and
complete handler unmatched. Six root builds and one fresh dependency rebuild
preserve 432/77 native matches and reproduce both complete control outputs.
This is bounded source/compiler evidence, not a selected-source promotion.

The [ordinary price-first control](../research/mayhem-signer-seed-order/composition/arithmetic/guard/README.md)
then restores the original first seven callee identities and nonzero overflow
branch direction by placing price before `checked_mul`. Three source-control
compilations and a fresh 163-command rebuild repeat both complete checked
outputs, but the shared error-block layout and full handler remain unmatched.
The alternative Option conversion is retained as a negative control.

## Current-source allocator-provider composition

The [current 432-window provider composition](../research/mayhem-current-provider-closure-20261027/README.md)
combines the qualified quote/initializer program source with the complete historical
macro/IDL context. In the fresh Linux cohort, the curve reserve now calls the
matching 328-byte allocator at relative offset 528. Eight windows regain ordered
direct-call closure (414 to 422), and O0207 becomes raw-equal (84 to 85), with
all prior normalized and raw matches preserved. Three enabled builds agree;
6,636 fresh trade pairs pass independent signature/state/non-compute-log checks.

This remains a mixed-framework source-context diagnostic, separate from the
selected 100-raw checkpoint. No new normalized body is recovered. The upstream
gate returns the direct-closed set to 414, but its complete ELF differs from the
baseline. Indirect/data closure, initializer qualification on this artifact,
historical source attribution and whole-original identity remain open.
