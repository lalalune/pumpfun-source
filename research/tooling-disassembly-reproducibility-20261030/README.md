# Repeatable deep-disassembly packets

Two runs of `scripts/deep_disassembly.py` on the same captured Mayhem binary
produce different packet hashes: the window report serializes unordered sets,
and the gzip header records the current time. On Windows, implicit text I/O
also makes packet encoding and line endings depend on the local configuration.

The reviewed helper transition sorts the unique syscall/external-call lists,
sets gzip time to zero and omits its original filename, and writes packet text
as UTF-8 with LF newlines. It changes serialization, not instruction decoding,
window selection, capture bytes or analysis semantics. New regression tooling
lives in this research package; no new root `scripts/*.py` entry is added.
No historical packet or its input hashes are rewritten.

## Source and input identities

All source digests below refer to Git's exact blob bytes for
`scripts/deep_disassembly.py`, without checkout newline conversion.

| Role | Source commit | SHA-256 |
| --- | --- | --- |
| Original helper | `094a06f18df738d41e77070c1a009e135671ac1a` | `e0241c00f43218f15a127ded6c6e5398811faa38d7b6fcd8f875029135db0ceb` |
| Corrected helper | `1fa05fb74d1ea006e57f1c1f3cbdd270aafddd84` | `0bf017a8bb351e260685c124a9974a9e2c16ef97a250b16536b3907502dd82e9` |

The test uses `evidence/original/mayhem/deployed.so`, SHA-256
`a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`.
The required evidence verifier checks that capture before accepting the corpus.

## Reproduction and validation

Run from the repository root:

```sh
python -B research/tooling-disassembly-reproducibility-20261030/test_verify.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
git diff --check
```

The regression runs the real Mayhem CLI twice, in fresh distinct output
directories, with `PYTHONHASHSEED=1` and `2`, UTF-8 mode disabled and enabled,
and a 1.1-second delay to expose gzip's timestamp. Both generated packet
verifiers must pass. The test requires all 12 expected output files to be
byte-identical, including the compressed disassembly and manifest, and checks
the absent gzip filename, zero timestamp and UTF-8/LF text representation.
Temporary output packets are removed after the test.

Before the correction, repeated runs with UTF-8 mode enabled produced
different `windows-deep.json`, `disassembly.json.gz` and `manifest.json` bytes;
the gzip filename check also failed. The decompressed instruction records were
identical. After the correction, the full 12-file comparison passes even when
the two processes use different UTF-8 modes. Validation used Python 3.11.9 and
zlib 1.3.1 on Windows; the 10 existing tooling tests and all nine capture checks
also pass. The regression is included in the workflow's evidence suite.

## Limits

Byte reproducibility is tested with the same Python and zlib versions. It is
not a promise of identical compression across different runtime/library
versions. This is an offline tooling repair, not a fresh contract build,
runtime replay, source-equivalence result or security acceptance. It does not
change the archived helper's policy for existing output directories; use fresh
destinations as the test does.
