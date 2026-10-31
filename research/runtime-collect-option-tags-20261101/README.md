# Collect-fee base-account option tags

At base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, the native `collect_coin_creator_fee` model accepts an invalid COption tag in a base mint/token account that the retained program rejects with `InvalidAccountData`. The model now checks the two mint tags and three token-account tags before initialization, preserving owner and length error precedence. A `None` payload may contain nonzero bytes.

The same 72-case local probe uses the actual captured Pump AMM, SPL Token, and Token-2022 programs and freshly compiled native hosts. It has 22 mismatches before the fix and zero after. All amounts are zero, so the cases isolate decoding in the existing 82/165-byte model. The controls cover tags 0/1, inactive nonzero payloads, and competing initialization/owner errors. Both JSON receipts retain all outcomes and capture/host hashes.

The affected test file passes all six test methods (including 72 new subcases); `results.json` distinguishes these from the existing fixed/random cases. Mandatory checks pass: nine captured images and 250 tooling tests. The affected captured test is added to the existing host-fragments CI job.

From the repository root, with its requirements and `rustc` installed:

```sh
proof_dir=$(mktemp -d)
base=9120883a957d7d9b2cab6140f66fb5bc9e6774d5
git show "$base:programs/pump-amm/recovered/collect_coin_creator_fee.rs" > "$proof_dir/collect_coin_creator_fee.rs"
git show "$base:programs/pump-amm/recovered/collect_coin_creator_fee_host.rs" > "$proof_dir/collect_coin_creator_fee_host.rs"
rustc --edition=2021 -O -D warnings "$proof_dir/collect_coin_creator_fee_host.rs" -o "$proof_dir/base-host"
rustc --edition=2021 -O -D warnings programs/pump-amm/recovered/collect_coin_creator_fee_host.rs -o "$proof_dir/fixed-host"
python -B research/runtime-collect-option-tags-20261101/reproduce.py --repo . --host "$proof_dir/base-host" --output "$proof_dir/before.json"
python -B research/runtime-collect-option-tags-20261101/reproduce.py --repo . --host "$proof_dir/fixed-host" --output "$proof_dir/after.json"
python -B tests/test_pump_amm_collect_coin_creator_fee_captured.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

These are synthetic account fixtures and offline reconstruction parity results. They establish neither on-chain reachability of malformed token accounts nor a production SBF rebuild, full handler equivalence, or byte identity. Token-2022 extensions and native transfers remain outside this patch.
