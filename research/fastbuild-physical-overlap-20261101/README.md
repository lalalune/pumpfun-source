# Fastbuild source/output case aliases

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

`fastbuild.build` rejects an output directory inside its source before taking
locks or staging. On a case-insensitive filesystem, `Path.resolve()` can retain
an alternate case spelling, so string ancestry alone misses the same directory.
The real SBF build succeeds and writes output files into the original source.

The fix compares existing physical ancestors as well as lexical ancestry for
the source/work/output admission check. It runs before locks and directory
creation. No compiler recipe, captured program, program source or historical
packet changes.

## Repeat

Use Python 3.11+ and the macOS arm64 platform-tools v1.44 SDK, with `rsync`
available and no unreviewed Cargo configuration in the temporary ancestry.
The probe explicitly requires a case-insensitive filesystem; it does not
download or install tools.

```sh
python3 research/fastbuild-physical-overlap-20261101/probe.py /path/to/checkout /path/to/platform-tools
PUMP_BUILD_TEST_SDK=/path/to/platform-tools python3 reconstruction/harness/test_fastbuild_source_preflight.py
```

Run the identical probe against the base and fixed checkout. The probe uses
production fastbuild with actual SDK Cargo/rustc/linker/objcopy and a tiny
no-std crate. It does not replace compiler results or run live transactions.

Recorded environment: macOS arm64, Python 3.12.13, platform-tools v1.44
rustc 1.79.0-dev. Official SDK archive SHA-256:
`66e20d135fddd70ff519baf7ff320d762957f9aedf93a50e23756db23ad79351`.

| Layout | Before | After |
| --- | --- | --- |
| Separate output | Builds; source unchanged | Builds; source unchanged |
| Canonical output below source | Rejected before writes | Rejected before writes |
| Alternate-case output below source | Builds; source modified by lock and 4 outputs | Rejected before writes |

The valid control emits the same candidate SHA-256 before and after:
`dcbf63f7b5b5ae4a4c6efde978fd4ac803105e31527776ef94d89815e8a68087`.
Raw observations are in `before.json` and `after.json`. The output-parent alias
is already present while the nested output is not, so this also exercises
admission of a destination that has not been created.

This proves a local build-path admission defect on the tested filesystem;
it is not a whole-program equivalence or security claim. Concurrent replacement
of filesystem paths after admission is outside this test. The existing separate
staged-output ancestry rule is unchanged.
