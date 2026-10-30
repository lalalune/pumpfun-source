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

Reviewed base: 665499915f9caedcd38921d415a90f0606686398.
Archived script SHA-256:
831cee56ca07bba6be4b057dcf33873319e63cc27aa3d7b45a7f2ab66adaee6c.

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

The inherited all-program CLI still requires repro/programs.json, which is
absent on the reviewed main branch. The enumeration fallback proposed in
PR #1277 is separate and is not copied here. The guard also applies to the
explicit-input inventory() function returned by load_inventory(); the tests
exercise that actual path. CLI --help succeeds, but a complete multi-program
CLI run is not claimed.
