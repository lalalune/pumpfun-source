# pumpfun-source

This repository has one goal: exact bytecode reconstruction of pump.fun's
on-chain Solana programs — Pump Main, PumpSwap/AMM, Fees, Mayhem and the
Donation Relay. Each program is rebuilt from source with a pinned toolchain
and scored instruction-by-instruction against the captured deployed binary.

**Scope.** Only the program bytecode publicly deployed on-chain is
reconstructed. This project does not reconstruct, capture or reproduce
pump.fun's website, apps, backend services, APIs, SDKs, branding or any other
off-chain material. Pull requests for frontend, backend, SDK or off-chain
capture work are closed without review. See [CONTRIBUTING.md](CONTRIBUTING.md).

Everything here serves building, scoring, verifying or differential-testing
those programs. There is no frontend, backend, SDK or off-chain service code.

- `programs/` — reconstructed program sources and per-program status
- `reconstruction/` — toolchain recipes, build harness and scoring
- `evidence/` — captured original binaries and analysis inputs
- `scripts/` — build, scoring, verification and differential-test tooling
- `crates/`, `binaries/` — supporting crates and experimental build outputs
- `research/` — retained investigation packets with their own verifiers
- `tests/` — unit tests for the tooling

**Verified checkpoint progress — 2026-11-01**

**Code-byte completion: 99.47% — 5,185,728 of 5,213,128 bytes matched.**
**27,400 bytes remain** in unmatched raw windows. Matched-window completion is
**99.97% (3,337/3,338)**.

| Program | Matched / total code bytes | Code bytes matched | Matched windows | Windows matched | Whole meaningful ELF equal |
| --- | ---: | ---: | ---: | ---: | --- |
| Pump Main |1,764,808/1,792,208|98.47%|1,034/1,035|99.90%|No|
| PumpSwap / AMM |1,162,040/1,162,040|100.00%|785/785|100.00%|**Yes**|
| Fees |799,648/799,648|100.00%|585/585|100.00%|**Yes**|
| Mayhem |706,744/706,744|100.00%|441/441|100.00%|**Yes**|
| Donation Relay |752,488/752,488|100.00%|492/492|100.00%|**Yes**|
| **Total** |**5,185,728/5,213,128**|**99.47%**|**3,337/3,338**|**99.97%**|**4/5**|

All **3,337 matched windows are raw-equal**; normalized-only Pump windows: **0**.
The latest fresh Pump Main identity build preserves all matched windows with
no raw or normalized losses. The targeted `admin_cto::execute` window is 27,400 bytes;
its instruction-token similarity is **71.548%**, adding **51 matched tokens**
since CP113 (70.021%,2,338 tokens). Positional byte differences change from
3,189 to **3,289**. Partial token similarity is excluded from completed-byte totals.
All **388 targeted signed synthetic admin-CTO pairs** pass for this exact new
image, with **776 canonical signed vectors** verified and seven rejection controls.
A separate 22-transaction cross-program lifecycle, four controls and independent
replay also pass. Finite runtime and compiler/layout/valid-context limits remain.
The new unlinked reference models add captured-program test coverage without
increasing compiled completion. Pump Main's meaningful ELF is not yet equal.

AMM, Fees, Mayhem and Donation Relay retain their exact meaningful-ELF
checkpoints. Separate bounded tests do not replace those identity receipts. See the
[latest scores, runtime coverage and limits](reconstruction/pump-main/checkpoints/completion-pass114-20261101/README.md),
[other-program checkpoint provenance](reconstruction/pump-main/checkpoints/completion-20261030/other-programs.json)
and [Fees Linux rebuild packet](research/fees-linux-fresh-rebuild-20261030/README.md).

Raw equality compares complete instruction bytes. Normalized windows mask
specified call/address operands and do not prove whole-program identity.
Whole meaningful ELF equality excludes documented zero loader-allocation padding.
These counts describe the selected maintained recipes; they are not a
percentage of engineering work completed.

The [reconstruction toolchain](reconstruction/README.md) rebuilds `programs/pump` and
scores it against the captured original in `evidence/original/`.

## License

Repository code and documentation are [MIT licensed](LICENSE). Third-party
sources and artifacts retain their original licenses and ownership.
