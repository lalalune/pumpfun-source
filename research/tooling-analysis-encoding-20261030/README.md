# UTF-8 analysis packets

The documented `analyze_program.py` and `deep_section_analysis.py` CLIs write
Unicode README text using an unspecified text encoding. With a CP949 default,
both fail on the em dash before writing the verifier and manifest. Their final
line-count reads also need the packet encoding specified.

At baseline `094a06f18df738d41e77070c1a009e135671ac1a`, actual CLI runs against
`evidence/original/mayhem/deployed.so` under a controlled CP949 text default
exited 1 with `UnicodeEncodeError` at the README write. Program analysis left
6 files; section analysis left 7. UTF-8 controls completed 8 and 9 files,
respectively, and both generated verifiers passed.

The test adapter changes only omitted or `locale` encoding arguments to
`builtins.open` and `io.open`. It preserves explicit encodings and binary I/O;
the analysis and retained ELF are real. This is a controlled encoding test,
not a native CP949 Windows run: the investigation host reports CP65001 with
UTF-8 mode disabled. No operating-system locale settings are changed.

The fix specifies UTF-8 for packet text writes, generated verifier JSON reads,
and the generators' final line counts. It does not change newline policy or
analysis semantics. Archived roadmap and bytecode-signature sources and all
existing evidence packets remain untouched.

Run:

```sh
python -B research/tooling-analysis-encoding-20261030/test_verify.py
```

For each generator the tests run CP949-default, UTF-8-default, and unadapted
native CLI executions. They verify complete file counts, UTF-8 README content,
all JSON (including manifests) equality, and each generated verifier under the
same encoding control. Python 3.12 on Windows passed both tests.

Python documents that [open's default encoding is platform-dependent](https://docs.python.org/3.12/library/functions.html#open)
and [Path.write_text uses the same encoding arguments as open](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.write_text).

Input SHA-256:

- Mayhem deployed ELF: `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`
- Baseline `scripts/analyze_program.py`: `b6e945c08aac13ebd5c4411b9f7ce21fecd8daf6753eb432769189b96a820e5a`
- Baseline `scripts/deep_section_analysis.py`: `e074929f474a6b98153bb6fd12f7943fa45d80ba10750c9967e334feee0e59e1`
