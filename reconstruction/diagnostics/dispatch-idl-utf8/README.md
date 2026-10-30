# Dispatch IDLs use their recorded UTF-8 encoding

The actual UTF-8 Pump IDL cannot decode under a CP936 host default.
`deep_disassembly.py` catches the resulting ValueError and silently recovers
zero selectors; `recover_dispatch.py` exits with UnicodeDecodeError.
Specify UTF-8 on those two existing IDL reads. No loader algorithm, selector
heuristic, no-IDL fallback, captured bytes, scorer or program source changes.

From the repository root:

```
python -B -X utf8 tests/test_dispatch_idl_encoding.py -v
```

The same tests run the actual maintained CLIs with real retained ELF/IDL inputs
in isolated filesystem trees. Base950c94c7 gives2 failures/2 passing controls;
the two-line fix gives4 passes. Pump recovers56 selectors and produces the same
complete12-file packet as the UTF-8 control; its generated verifier passes.
The complete four-program map equals its UTF-8 control; actual no-IDL Mayhem
behavior is unchanged. A test-only adapter changes only omitted text encodings
to CP936; no product loader, decoder, ELF or subprocess result is mocked.

The scripts README permits reviewed asset transitions for unpinned existing
helpers. At950c94c7 all1578 tracked text blobs were inspected with no missing
objects: the8 filename references in policy-review.json are code, docs and
current-CLI tests, not an immutable checkpoint/global asset-hash guard.
transition.json records complete before/after source hashes and complete loader
ASTs, whose sole change is the existing IDL read's encoding argument. The set
of275 root Python scripts remains unchanged. These hashes are review metadata,
not a runtime whole-module gate. Prior packets and existing guards are untouched;
the focused regression is added to the existing evidence CI suite.

This is finite encoding-independence evidence, not a new program build, byte
match, VM execution or security qualification. Windows CPython3.11.7 is tested.
The coordinator's pinned solders0.27.1 Windows wheel lacks FeatureSet/LiteSVM,
so the required aggregate root suite cannot import and is not claimed passing.
POSIX fastbuild tests also require unavailable fcntl on this host.
