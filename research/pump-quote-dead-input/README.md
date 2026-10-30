# Remove a discarded predecessor input from the current quote replay

The current USDC-quote replay still reads the removed historical arithmetic
report to build a SOL-case list. That list is never executed: a later `cases=[]`
replaces it before generating the actual 130 quote cases. The unnecessary file
read prevents the entire current CLI from starting on a clean checkout.

Remove only that read and the discarded case construction. Preserve reserve
values from the real fixture, the actual case generator, VM function, comparisons
and all 130 existing cases. This adds no new coverage and changes no maintained
Rust, oracle, signature handling or captured bytes.

`python -B research/pump-quote-dead-input/reproduce.py` compiles current Pump with
the authenticated official v1.44 SDK for its native host, then
executes the actual CLI with no historical report present. All 130 original and
candidate comparisons must agree. An unchanged captured different program is an
explicit diagnostic negative and must produce differences and a nonzero exit.
Static AST digests of the actual generator and VM function are retained before
and after as supplemental confirmation that these blocks are unchanged; the
primary proof uses real compilation and real VM execution, not AST simulation.

The complete actual compiler receipts, ELF outputs and VM results are retained
under `work/scoped-proof`. This proves the existing bounded quote workflow can
run without a discarded input. It does not establish other quote routes,
extensions, full corpus availability, whole-program equality or security status.

The Linux proof authenticates the unmodified official x86_64 v1.44 archive
(SHA256 `6719b889d60677a8a2fcf4c82f68441a1afe0ab093edd2efe9f84a67a808b3e9`)
and the exact pinned SBPF target-library hashes, then uses the verified builder's
existing native `--target sbpf-solana-solana` path. It does not impersonate the
macOS target-library profile or substitute tool bytes. Both red/green runs use
the same native Linux distribution; cross-host ELF identity is not claimed.

The Linux proof extracts into the fresh `work/quote-native-sdk` directory,
leaving an already installed SDK available for other builds. Use a clean work
directory for each proof. The reproduction command rejects `-O` and `-OO`,
since disabling assertions would disable its result checks.
