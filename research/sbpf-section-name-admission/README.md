# Unambiguous disassembly section lookup

The archived scripts/sbpf_disassembly_inventory.py indexes ELF section rows
by decoded name. Repeated names overwrite earlier rows. With two distinct
.text sections, the first body's bytes disappear from the inventory while
the selected body's coverage can still look complete. Repeated section names
are not universally invalid ELF; this particular name-keyed tool cannot
represent them, so it must reject the ambiguity rather than choose one.

inventory.py is an opt-in successor for the same disassembly CLI. It checks
the archived source SHA-256 before loading it and adds one admission rule:
the section map must retain as many entries as the ELF section table. The
check runs before the external disassembler is invoked. Unique-name rows and
all other inventory behavior are unchanged. Generated manifests hash this
successor as their generator; its bytes include the required archived hash.
The frozen root script and all historical packets remain unchanged.

Reviewed base: 8da57e405.
Archived script SHA-256:
08070b3ea6c8e5627a85c8d53bd63fc6fc25b2534f1da9fd82e0adce6a59013f.
This binding includes #1277 (captured-program enumeration when
`repro/programs.json` is absent) and #2303 (staged publication of the
inventory directory). Neither changes `sections()`, which still keys rows by
name, so the admission rule is unchanged. Because #1277 makes the archived
script import its `scripts/` sibling `analyze` by plain name, the successor
puts that directory on `sys.path` after the hash check and before execution.
The binding also includes the captured-input dedupe (a program routed to
`evidence/dependencies` by `capture_directory` was offered a second time by
the dependency sweep). That change touches only input enumeration, not
`sections()`, so the admission rule is unchanged.

Run from the repository root:

    python3 -B research/sbpf-section-name-admission/test_inventory.py
    python3 research/sbpf-section-name-admission/inventory.py --help
    python3 research/sbpf-section-name-admission/inventory.py \
      --tool-source /path/to/pinned/sbpf --output /fresh/output

The six tests exercise duplicate text/data names, exact unique-name payloads,
rejection before tool execution with unchanged input, archived-source drift,
and all nine retained ELF capture tables. The original parser fails the two
duplicate-name parser regressions; the guarded parser passes them. The real
inventory admission path is also exercised without launching any tool.

Limits: no external SBPF tool was built or run for this change, and no full
disassembly packet was regenerated. The archived roundtrip entrypoint remains
unchanged. This is an admission guard, not complete ELF semantic validation,
new reconstruction coverage, runtime equivalence or security clearance.
The source binding intentionally requires the exact reviewed LF bytes.

The inherited all-program CLI now falls back to the captured programs under
evidence/original when repro/programs.json is absent (#1277). The guard also applies to the
explicit-input inventory() function returned by load_inventory(); the tests
exercise that actual path. CLI --help succeeds, but a complete multi-program
CLI run is not claimed.

The current adapter also admits the reviewed UTF-8/LF-only writer update.
Its source binding is `5d00aedbccf78c2a00780ada287d4ae2c2cb649d88da7dfc796c843803c9d3b2`;
RPC, parsing and admission behavior are unchanged. The earlier binding above
identifies the historical baseline.

The current binding retains the UTF-8/LF manifest writer from #3104 and the
selected-contract-preserving dependency dedupe from #3126. Different-file
name collisions remain errors; explicitly selected aliases are not dropped.

## Current inventory publication binding (2026-11-01)

The maintained adapter now explicitly admits generator SHA-256
`0d3714567123a34fd504b97609d00bd1a61eb223213d8b2dc39af68a61081bcf`.
The prior `08070b3...` binding correctly identified the merged #3126 source.
The later #3622 bounded-staging-prefix change moved the current generator to
`81c0f7...` without updating this adapter, so the documented CLI began refusing
the maintained source before any disassembly. The reviewed current binding
also includes #3912's lexical-leaf admission and no-replace publication fix.

This is one explicit reviewed source identity, not automatic hash discovery or
an expanded allowlist. The section-map admission behavior remains unchanged.
An unreviewed source and the previous generator are rejected by the current
adapter. A separately reconstructed historical adapter/source control still
produces its original payloads; no historical stored packet is rewritten.

The [follow-up proof](../sbpf-inventory-publication-20261101/README.md#section-name-adapter-follow-up)
uses the pinned real disassembler and all nine retained captures. Its complete
current packet matches the historical control and direct current generator in
all 27 payload files and semantic manifest fields. The generator digest names
the actual adapter source as before. The six existing section-name admission
tests now run in the ordinary tooling CI lane as well.
