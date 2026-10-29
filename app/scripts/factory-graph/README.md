# Factory graph analyzer

This static analyzer ties recovered Turbopack factories back to authenticated capture objects, preserves factory variants, and builds deterministic route and API attribution reports. Captured JavaScript is parsed as inert text and is never evaluated.

## Commands

Run from `app/`:

```sh
pnpm graph:build
pnpm graph:verify
pnpm graph:summary
pnpm graph:route -- /go
pnpm graph:module -- 100281
pnpm graph:operations -- auth/admins
pnpm test:graph
```

`graph:build` transactionally replaces `research/turbopack-route-graph-20261028/`. `graph:verify` rejects missing, modified, extra, or symlinked generated records. Module lookup accepts an optional SHA-256 prefix and reports all matching identities so a colliding numeric ID cannot be presented as unique.

Report lookups authenticate the requested record against its unique manifest
entry, including compressed and decompressed pins where applicable. This checks
packet integrity; `graph:verify` also rebuilds from the current source inputs to
check freshness and the complete packet inventory.

## Source authentication

For every recovered variant, the analyzer:

1. Requires the origin to exist in `evidence/web/manifest.json`.
2. rejects absolute paths, traversal, NUL bytes, and symlinks;
3. verifies captured byte length and SHA-256;
4. decodes UTF-8 with fatal error handling;
5. slices the decoded source using the recorded UTF-16 half-open offsets; and
6. verifies the factory content hash; and
7. binds the recovered formatted file to that authenticated source before using it for graph extraction.

The formatted binding first compares a complete canonical Babel factory AST. It ignores source locations, comments, parser tokens, raw literal spelling metadata, and empty no-op statements, while preserving identifiers, values, properties, optional/computed access, operators, calls, arguments, expressions, and executable statements. A small number of pinned formatter outputs change Babel AST shape; those variants are accepted only when their complete formatted bytes equal a fresh derivation through the same pinned inventory formatter. Canonical digests are cached per authenticated factory hash and full ASTs are not retained.

The line census uses Babel token locations. It counts code lines once per unique factory content hash and excludes the recovery banner, blank lines, comment-only lines, and duplicate variants.

## Resolution model

Graph identity includes numeric module ID, factory hash, captured object, source range, and chunk URL. Calls whose receiver matches the top-level factory runtime parameter's spelling are recognized structurally:

- `runtime.i(literal)` is a direct import boundary.
- `runtime.A(literal)` is a dynamic import boundary.
- `runtime.s(...)` supplies observed export names.

The export array follows the captured runtime's mixed descriptor grammar, not a
fixed two-entry stride: `name, 0, value` is a constant, `name, getter` is an
accessor, and a following function is its optional setter. String-valued constants
are values, never additional names. Getter/setter/value expressions are parsed,
not called. Names are deduplicated and sorted as before.

This analyzer supports complete literal arrays with string names, literal zero
tags and inline function accessors. Non-array/dynamic calls, spreads and incomplete
or unsupported descriptors make no partial static export claim. This is a local
supported-format policy, not a statement that every omitted form is invalid at
runtime (for example, a truncated constant can evaluate to `undefined`). Receiver
recognition still matches the top-level runtime parameter's spelling; it is not
a lexical binding resolver and can misattribute a nested shadowed `.s` call.
This correction does not change import resolution or claim complete JavaScript
scope analysis.

The retained runtime `evidence/web/objects/f25d7686d048ae16.js` has SHA-256
`b5f9b5199b99ab6c141f4540f0b7d0fe803c4ecf6956849ecb6e59d3d439272e`.
Its `s` → `d` → `h` chain contains the descriptor decoder at UTF-16 `[720, 1077)`
(SHA-256 `371fda7a2b1b7b05805e4a8cfc97dcf18ea159eb41073ad2ea0f0aa09dfe986d`).
The runtime and all factory source remain inert and unchanged.

The source-bound regression also reads captured settings factories **358893**,
**956718/754219** and **272700** from `11cf0bf8a734ea43.js` (SHA-256
`a859077ba48e8afb625cd917a674ace225a0959ad40932f02331402dd5365f83`).
The old stride mislabeled the eight-bullet mask value as an export and lost
`C`, `M`, `s`, `u` and `W` in 358893; it also lost `d` in 956718 and `k` in 272700. Tests authenticate complete source and factory-range hashes before static
analysis. Synthetic cases cover mixed descriptors, setters, duplicate names,
function/string values, unknown shapes and non-array shadowed calls. No test
executes a captured getter or factory.

The export correction was qualified against all 5,947 authenticated factory
variants. Their 6,072 observed export calls contain 20,977 constant descriptors
and 1,298 getter descriptors; none requires the unsupported-format fallback.
Setter descriptors are covered by the captured runtime and synthetic tests,
not by a claimed observed setter occurrence. The selected graph changes only
the export lists of 657 of its 1,810 identities (387 unique factory hashes):
2,186 name occurrences are restored and 232 misread value occurrences removed.
Identity keys, factory IDs, source hashes/ranges, routes, imports, resolution
counts and every other report's content remain unchanged. The original
`IMPORT-EDGES.json.gz` bytes are preserved; only `MODULE-IDENTITIES.json.gz` and
its manifest entry are regenerated. All 17 graph tests and a separate full
source-rebuild verification pass. These are static analyzer checks, not an app
build, full workspace test run, browser test or native compatibility result.

An import is exact only when chunk context or the selected corpus leaves one identity. Multiple compatible identities remain `AMBIGUOUS`; missing selected targets remain `UNRESOLVED`; string runtime boundaries are `EXTERNAL`. The analyzer does not guess among collisions.

Route attribution requires an authenticated route HTML record to reference an authenticated captured JavaScript asset. A seed is keyed by module ID, factory hash, captured source object, and UTF-16 source range. Identical factory bytes in another captured object therefore do not inherit the route. Reachability then follows exact graph edges only, including legitimate exact cross-chunk imports. Static API attribution maps the repository's existing internal and developer ledgers into enclosing authenticated factory ranges. It does not claim endpoint reachability, authentication, or live compatibility.

## Reproducibility and limits

Outputs use stable ordering, deterministic JSON, deterministic gzip headers, and a content manifest. Publication happens in a temporary sibling directory and is renamed only after every output is written. Verification authenticates the current inputs, rebuilds every report, and compares the regenerated content with the packet manifest. Because gzip output can differ between zlib builds bundled with different Node releases, each `.json.gz` record is additionally pinned by the sha256 and length of its decompressed content, and rebuild comparison uses that content identity rather than compressed bytes. The checked-in packet records no timestamps or machine-specific measurements, so repeat builds are content-identical.

The selected corpus deliberately targets approximately 250,000 authenticated code lines rather than the entire recovered inventory. An unresolved edge may simply lead outside that selection. Exact route captures were not retained for `/profile/:id` or `/portfolio`; their reports fail closed with no attributed nodes. This is dependency evidence, not recovered original TypeScript and not proof of runtime behavior.
