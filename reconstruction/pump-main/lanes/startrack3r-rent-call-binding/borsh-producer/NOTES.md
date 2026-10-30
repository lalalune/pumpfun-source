# Two diagnostic-path bytes corrected by the dependency producer

The Borsh path mismatch from [#2198](https://github.com/lalalune/pumpfun-source/pull/2198)
is now reproduced and corrected through compiler inputs. On the same pinned
`fd8b94dfa3a0ec671e018a5418c4b5009e26da6a` source, the entire 2,666,064-byte
compiler output changes at exactly two bytes: file offsets 1794237 and 1794240
replace `0x5c` with `0x2f`. Both lie in `.rodata`, at offsets 1421 and 1424.
The diagnostic string becomes `src/de/mod.rs`, matching the corresponding
original section bytes. Every other output byte is unchanged, including the
complete `.text`, relocation tables and `.data.rel.ro`.

Original-to-local `.rodata` differences fall from **104 to 102**. This is a
section-relative data improvement, not whole-original file-position identity.
All 1,035 function-window memberships remain identical: **1027 normalized,
273 raw, zero gains or losses** under the pinned, unmodified scorer. The
formatter gap is unchanged. This experiment uses the earlier main control,
not the separate rent-helper source experiment.

Control SHA-256: `09186a9021ba057d53d37b55e7d28c55415417995999c2d3e2006b943b09521a`.
Corrected output and independent repeat:
`cd8bc6ca92d66cd9808dd8f3a3a3b27bd204f916a4b2487d8989e4b5db99bc09`.

## Producer boundary

The logged Borsh 0.10.4 compiler invocation reproduces the retained rlib
**byte-for-byte**, SHA-256
`93996b291f8d421c6bf9f028f984452dadfadb28570456ea4a0876e23a339b71`.
All checksum-listed vendor files are checked, and the four pinned tools and
207 cached dependency inputs remain unchanged. The library contains a
1,141,352-byte `lib.rmeta` and a 111,000-byte object. The target path occurs
in metadata; it does not occur in that object.

The first dependency-level absolute-file remap also has no effect. The
SDK-associated pinned Rust source explains why: `parse_remap_path_prefix`
appends the current-directory mapping after all explicit mappings
([config.rs](https://github.com/anza-xyz/rust/blob/08b7341888ab480dfaaa0698300cbbbbb2d75b53/compiler/rustc_session/src/config.rs#L2262)),
and mapping searches from last to first
([source_map.rs](https://github.com/anza-xyz/rust/blob/08b7341888ab480dfaaa0698300cbbbbb2d75b53/compiler/rustc_span/src/source_map.rs#L1099)).
This is a bounded source/observation association; the Windows compiler's
`-vV` reports its commit as unknown. Exact retrieved Git blobs and hashes
are retained in `PRODUCTION.json.gz`.

Removing `-Zremap-cwd-prefix=` and replacing it with an explicit equivalent
mapping changes metadata and fails the retained-library identity control.
That attempt is retained; its object remains identical.

The successful control keeps the original unstable flag and compiles from
an output directory outside the vendor tree, adding an explicit mapping
from the absolute vendor directory to the empty prefix. It again produces
the **entire original rlib byte-for-byte**. With that control established,
adding a later explicit mapping from the full `src/de/mod.rs` source filename
to the literal forward-slash path changes exactly two bytes in `lib.rmeta`
(offsets 1138117 and 1138120), and no other byte in the entire archive.
No metadata identifier was searched or changed, and no binary was patched.

Corrected rlib and independent repeat:
`415cf04df1426d7f149f6f02f75ea593f093f36681f5dcc52077296fef6ace2d`.
The rebuilt library is the **only changed dependency** for two isolated root
compilations. All 100 root source files, four tools and 207 recorded dependency
inputs remain unchanged during each root invocation. Both compiler outputs
are byte-identical. The source records still contain length 13, line 637,
column 21; their pointers and placement are unchanged. No target/VM executes.

## Attempts and verification

| Attempt | Result |
| --- | --- |
| 01 logged dependency replay | Whole retained rlib reproduced |
| 02 explicit file remap with original cwd | Byte-identical; override hypothesis rejected |
| 03 remove cwd flag, use equivalent explicit mapping | Object identical, metadata differs; control rejected |
| 05 outside-cwd explicit mapping control | Whole retained rlib reproduced |
| 06 outside-cwd specific file mapping | Exactly two metadata bytes change |
| 07 root preparation | Controller expected absent cached rmeta; no compiler started |
| 08 root with rebuilt rlib | Exactly two `.rodata` bytes change |
| 09 independent dependency repeat | Whole corrected rlib reproduced |
| 10 independent root repeat | Whole corrected compiler output reproduced |

Six dependency and two root compiler commands succeeded, with no stack
diagnostics. Failed hypotheses and the pre-compiler preparation failure are
retained. `PRODUCTION.json.gz` records each exact argv, cwd, allowlisted
environment, source/tool/dependency hashes, results and source pins;
`${WORK}` substitutes the local work directory. `COMPILER-LOGS.json.gz`
retains the diagnostic streams with the same path substitution. Dependency
commands use checked Borsh vendor source and the retained cache. Root commands
reuse the prior packet's exact source/control recipe with only the recorded
rlib replaced by its new compiler output. The commands can be reconstructed
from the receipts once those pinned inputs are supplied; they are not a
fresh-machine dependency installer. Actual ELFs and archives stay outside Git.

The standalone verifier requires no scorer or repository imports:

```text
python -I -B verify_producer.py --control CONTROL.so --candidate CORRECTED.so --repeat REPEAT.so --original ORIGINAL.so --control-library ORIGINAL.rlib --candidate-library CORRECTED.rlib --repeat-library REPEAT.rlib --report verification.json
```

It checks whole-input hashes, complete raw differences, independent repeats,
metadata-only changes, exact diagnostic records and original section-relative
data differences. Normal and optimized Python produce identical reports.
Three actual negative inputs are rejected: unchanged root as repeat, the
ignored remap library, and the changed-option control library. The unmodified
scorer separately confirms all memberships in `MEMBERSHIPS.json`.

The publication base is `6edd839eacedb837b281ebbd344f204bea4779f5` and has later
program changes, including `create_v2`; it was not built here. Measurements
remain pinned to fd8. This packet proposes no program change and establishes
neither native Linux preservation, runtime equivalence, complete data identity,
historical source authentication nor security. The next provenance work should
attribute the remaining 102 section differences before changing more inputs.
