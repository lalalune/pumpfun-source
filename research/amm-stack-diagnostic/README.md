# Reject definite compiler frame diagnostics before AMM publication

The native AMM builder publishes whenever Cargo exits zero. The pinned SBF LLVM
backend can print `exceeded max offset` and still return success; a source
iteration can therefore replace valid prior outputs with a diagnosed attempt.
The main Pump fastbuilder already refuses this exact diagnostic. Apply the same
admission rule to this independent AMM publisher, before copy, strip or publish.

Retain the actual Cargo status as `compiler_returncode`, the exact diagnostic lines
as `stack_warnings`, and use a nonzero overall `returncode` for a diagnosed attempt.
The existing failed-attempt path keeps its new source/log/record separately and
preserves a prior complete output. `try_sell.py` already gates scoring on that
overall return code. Other warnings, including the qualified baseline's separate
`overwrites values in the frame` diagnostic, do not match this gate.

The fixed upstream LLVM source distinguishes the two branches:
[SBFRegisterInfo.cpp at 08aedd64](https://github.com/anza-xyz/llvm-project/blob/08aedd64bf3abe4f163407b7bcf680403b84b32d/llvm/lib/Target/SBF/SBFRegisterInfo.cpp#L45).
Its size warning only writes to the diagnostic stream; it does not make Cargo
fail. No new interpretation of every line labelled Error or every stack-related
message is introduced.

The real proof provisions the authenticated native v1.44 SDK with pinned Linux
SBPF libraries and actually compiles the maintained AMM baseline. It scores all
785 raw windows and verifies the captured allocation image. A private Sell-source
copy then exports a dynamic volatile 8192-byte stack-buffer function and is
compiled with the same recipe/output ID. Require the actual diagnostic to name
that function and require its nonempty symbol to remain in the genuine compiler
ELF, rather than diagnosing code subsequently discarded from the output. Verify
rejection and byte-preservation of every prior published file. Finally restore
the ordinary baseline and actually rebuild it, checking the same candidate hash
and acceptance of its existing other warning class.

```sh
python -B research/amm-stack-diagnostic/reproduce.py
```

Real baseline/diagnosed compiler logs, actual ELF gzip files and the result are
retained in `work/scoped-proof`. The existing three publication unit tests are
additional compatibility checks; their synthetic compiler fixtures are not the
primary evidence. SDK, Cargo registry and targets stay outside the upload.
Maintained Rust and captured bytes are unchanged. This proves diagnostic admission
and publication protection, not VM execution, exploitability or whole-program
security. There is no binary patch or manufactured equality.
