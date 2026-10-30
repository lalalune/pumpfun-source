# Fresh-main provenance through Borsh and Metaplex

This extends the [Borsh producer result](../borsh-producer/NOTES.md) and
addresses the older-baseline limitation raised in PR #2208's automated review.
Main `a7135a6a64c446166895f7e3ea4ca84ac1a9b848` was fetched and freshly compiled
before testing the same producer change and its propagation through Metaplex.
The recorded control contains **112 source files / 107 Git blobs**, four tool
files and 207 cached dependency inputs. No program source is edited.

| Fresh source, changed producer inputs | Whole-output changed bytes | Original `.rodata` differences | Normalized / raw |
| --- | ---: | ---: | ---: |
| Main control | 0 | 104 | 1027 / 273 |
| Corrected Borsh rlib | 2 | 102 | 1027 / 273 |
| Also recompile Metaplex using that Borsh input | 4 | 100 | 1027 / 273 |
| Also remap Metaplex's observed source filename | 7 | 97 | 1027 / 273 |

Every candidate preserves all 1,035 normalized/raw memberships. Every output
has 2,666,344 bytes. Across the complete compiler output, only the listed path
separators change (`0x5c` to `0x2f`); all other bytes, including the complete
`.text`, `.data.rel.ro`, relocation tables and ELF metadata, are identical to
the fresh control. The seven corresponding original section bytes are `/`.
This is section-relative raw data improvement, not full-original file-position
identity. The formatter gap and function-window raw count do not improve.

Fresh control SHA-256:
`15c29a714f16bbe749766f795d6c933d4905d4dfc9b5491942ad6b35b2d528ff`.
Final output and independent repeat:
`532aa580aa308ec42d1436306041a03fa96e67acb7265fd19e02a66acd0e5acd`.
The intermediate hashes and all changed offsets are in `SUMMARY.json` and
`VERIFICATION.json`, which can be reviewed without decompressing a receipt.

## Why rebuilding Borsh alone left another copy

The original two-byte correction changed Borsh's imported metadata. Another
copy of `src\de\mod.rs` remained at `.rodata+17796`. Its diagnostic records
have line/column pairs 161/54 and 169/21, matching Borsh 0.10.4's checked vector
deserialization source. That path/line observation suggested a producer;
the controlled compilation below establishes which retained object carried it.

The logged `mpl-token-metadata-5.1.1` command is replayed with the same source,
tools, dependencies, metadata argument and working-directory-remap behavior.
It reproduces both the entire retained rlib and cdylib byte-for-byte:

- rlib: `c5f27ffec7ad6e5fe2009149d60bd0408b73341c626dd80bd8dbc7c065838a68`
- cdylib: `1609de75b758872f2a864f7db52c8a5dc27d94cbe61c0e7dc7560678e35a7b51`

Changing **only the Borsh extern input** to the previously reproduced corrected
library produces a Metaplex rlib differing at exactly two bytes. Both are in
its 3,182,048-byte object; the entire 7,120,248-byte metadata member and archive
tables remain equal. Rebuilding Pump with that object-bearing rlib changes
the second Borsh path copy as well. This is an observed metadata-to-dependent-
object-to-root propagation boundary, not an inference from aggregate scores.

The final variant additionally remaps the checked source filename
`src/generated/instructions/create_metadata_account_v3.rs`. Its source records
are 44/47 and 76/42, matching the checked vendor source. This follows the
previous packet's successful recipe: retain `-Zremap-cwd-prefix=`, compile
outside the vendor tree, explicitly map the vendor root to the empty prefix,
then map the full source filename to its forward-slash spelling. No metadata
identifier is searched or changed. No binary is patched.

Compared with the original Metaplex rlib, the final archive changes exactly
**eight bytes**: three in its metadata and five in its object. All are path
separators; all other archive bytes remain equal. The additional three root
output changes bring the total from four to seven. Corrected Metaplex rlib
and independently compiled repeat have SHA-256
`88d2859a9b6d0d01abfcfab62b1d26dd8a5247d850090f39b19519be7a18ef97`.
The generated cdylib remains identical but is not substituted into the root
cache: only the two actual Borsh/Metaplex rlib inputs change.

## Validation, replay and remaining work

Five root and four dependency compiler commands succeeded. Each retained
source/tool/dependency input is checked before and after its invocation; no
stack diagnostics or target/VM execution occurred. The final dependency and
root repeats are independently compiled and whole-file identical.

The current unmodified scorer from the same a713 source and an independent
all-window census agree on every control/final membership. The portable
verifier passes normally and under `-O` with identical reports. Real negative
inputs are rejected: Borsh-only root as the final candidate, import-only root
as the final candidate, and unchanged Metaplex as the dependency repeat.

```text
python -I -B verify_mpl.py --control CONTROL.so --borsh-only BORSH.so --import-only IMPORT.so --candidate FINAL.so --repeat REPEAT.so --original ORIGINAL.so --mpl-control CONTROL.rlib --mpl-import IMPORT.rlib --mpl-candidate FINAL.rlib --mpl-repeat REPEAT.rlib --report verification.json
```

Keep the sibling `borsh-producer/verify_producer.py`: its explicit checks and
bounded ELF reader are reused. No other repository imports or network tools
are needed by the verifier. `PRODUCTION.json.gz` retains exact argv, cwd,
allowlisted environment, complete source/checksum/tool/dependency hashes,
current scorer pins, archive-member comparisons and the path-record census.
`${WORK}` substitutes the local work root. `COMPILER-LOGS.json.gz` retains the
compiler streams with that substitution. `MEMBERSHIPS.json.gz` includes all
memberships and remaining byte locations. Actual ELF/rlib inputs are retained
locally outside Git and must be supplied to replay the verifier; repository
contents alone do not provide those compiler outputs.

The remaining **97** `.rodata` differences comprise **16 path separators** and
**81 bytes from two adjacent strings appearing in the opposite order**:
the `admin_cto.rs` filename and the canonical-pool diagnostic. This bounded
classification is supported by complete byte locations, not a claim that
either cause is already fixed. The path-record census covers all 21 separators
left after the first Borsh correction; several short filenames have multiple
source candidates, so filename search alone is not producer authentication.

These are fresh, pinned local Windows measurements, not native Linux
qualification or a source change proposed for adoption. Later main revisions
are not covered. No completeness, historical-source authentication, recursive
runtime equivalence or security claim follows.
