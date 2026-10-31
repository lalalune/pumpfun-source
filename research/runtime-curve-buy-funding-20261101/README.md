# Curve walk: insufficient buy funds

At base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, the native `curve_walk` model subtracts a successful buy's payments from the user balance without checking funding. With 1,000,000 initial lamports and a 10^12-token buy, the captured Pump program returns System error 1 and retains only the 5,000 transaction fee. The host instead returns success, wraps the user balance to 18,446,744,073,681,320,846 and changes the curve and token balances.

The shared Buy/ExactSolIn settlement now checks the quote, protocol payment and creator-vault credit before storing the fill. This preserves the previously charged transaction fee and the existing pricing/option error precedence. Checked subtraction also avoids overflowing an intermediate total.

The same real API comparison covers 69 cases / 72 steps: creator present/absent, empty/rent-funded vaults, insufficient/exact/one-above funding, funded success, zero amount, slippage and malformed options. A four-step walk checks the state handed onward after a failed payment. Base: 17 mismatched cases / 20 mismatched steps. Fixed: zero. Every probe transaction goes through LiteSVM with signature verification enabled, using the retained Pump, Fees, Token and ATA images. No RPC is used.

Run from the checkout with the pinned Python requirements and `rustc` on PATH; use new output filenames because the probe refuses replacement:

```sh
python -B research/runtime-curve-buy-funding-20261101/reproduce.py --revision 9120883a957d7d9b2cab6140f66fb5bc9e6774d5 --output /tmp/curve-funding-before.json
python -B research/runtime-curve-buy-funding-20261101/reproduce.py --output /tmp/curve-funding-after.json
python -B tests/test_curve_walk_funding_captured.py
python -B tests/test_curve_walk_captured.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

`--revision` reads the six host sources from Git into an isolated temporary directory. The same new test driver and retained captures exercise both versions. `before.json`, `after.json` and `results.json` retain the actual host/model hashes and results. Host hashes can vary with Rust toolchains or embedded temporary source paths; no host byte equality is claimed.

Validation: one new test method (69 cases / 72 steps), all three existing curve-walk methods, 250 tooling tests, and nine capture seals pass. The CI host-fragments group runs the new test.

This is a host-only recovered model; it is not linked into the production SBF crate. The proof uses admitted accounts, valid fee configurations and payers able to cover the transaction fee. It does not establish all account-admission or balance-error behavior, exact byte identity, or an on-chain issue. Original captures and earlier packets are unchanged.
