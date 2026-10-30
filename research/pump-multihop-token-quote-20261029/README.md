# Pump multi-hop constant-product helper recovery

Restore the original `constant_product::tokens_for_quote` call in `swap_hop` (original address `0x5b3b0`). The maintained source manually checked/subtracted one quote unit and divided the product. This three-line change uses the existing recovered helper and preserves every physical source line, including the Truncation closure on 589 and BuyZeroAmount check on 590. No arithmetic fee calculation, event, payment or other helper boundary is bundled.

This is a partial machine-code fidelity improvement. No complete function window or whole ELF becomes equal. The new function is smaller and **farther from the original size**, even though its aligned normalized instruction difference decreases.

| Measurement | Current source control | Candidate |
|---|---:|---:|
| Target bytes (original 18,584) | 18,056 | 17,704 |
| Absolute size difference | 528 | 880 |
| Aligned differing 8-byte slots | 3,423 | 3,372 |
| Normalized original windows | 1,019/1,035 | 1,019/1,035 |
| Raw original windows | 183 | 183 |
| Lost/gained normalized memberships | 0 / 0 | 0 / 0 |
| Lost/gained raw memberships | 0 / 0 | 0 / 0 |

The slot metric uses the unchanged normalizer and SequenceMatcher alignment. Block movement can count deleted and inserted slots separately; the metric is diagnostic, not a count of semantic differences. The 51-slot reduction accompanies an actual missing original call being restored.

## Current source and compiler inputs

The selected D037 public recipe contains 66 compiler-workspace inputs. Current main 040c2822643b4f41f3bc62f5a61f637b41efcf56 differs in four Rust files plus three workspace Cargo files. Merged[#1110](https://github.com/lalalune/pumpfun-source/pull/1110) already supplied those four Rust changes, including the single multi-hop Clock snapshot. That timestamp change was detected before a duplicate probe was built.

The parent here applies only those four maintained Rust changes to the authenticated D037 66-input workspace. The three Cargo inputs remain the retained recipe. Thus this is a specifically mapped Linux source control, not a checkout-wide main build or a claim to reproduce #1110's native macOS outputs. Its 183 raw windows must not be conflated with the native 188 count. The complete mapping, original D037 archive and current-parent patch are in `provenance/` and `control-source.patch`. The candidate changes only `multi_hop_curve_swap.rs` lines 581, 582, 589; its patch is `source.patch`.

Each ELF was produced by one actual normal root compilation with unchanged inputs, v1.44 tools, offline/locked Cargo, pinned container, and the existing physical-source wrapper. The existing normal recipe is retained in `controllers/local_build.py`; compiler commands, input inventories, tool hashes and full logs are in `build/`. There is no IR, assembly or ELF patch. No repeat-build claim is made.

| Output | Parent SHA256 | Candidate SHA256 |
|---|---|---|
| Symbols |`e1c9bdc3b248d41ebd73c1f8d0d2756edf95eafa178b8aed4a8ae0715649705a`|`99ee3d669ef817c7e66e42453f12e3706fbbbfa965173cd2c533db42a036d837`|
| Stripped |`21793a427cbb361de503fa01e98623e90c1d8abbecf178b9e75ebd57393f8b69`|`47cb3e2aac8bd8b444a820d3ed4a11f37d58cd7da1ad571692f9b7d22a39887d`|

The actual source PR is based on 4c929ce06ae0630d1f08cae832f1e0283a166264; its multi-hop file remained byte-identical to the qualified current-parent file. The final scope gate inspected all 14 then-open PRs and found no overlapping source patch.

## Call and data evidence

Original swap_hop calls `tokens_for_quote` at +0x1db0. The control has no such call; the candidate has exactly one at +0x1f08. Across all three images the complete 192-byte helper and its two immediate callees (504-byte PumpError conversion and 2,136-byte constant-product output) have identical narrow normalized bodies. This verifies the restored boundary; it is not raw identity or a recursive transitive closure proof.

Control and candidate `.rodata` are byte-identical. All 590 `.data.rel.ro` relocation words, including 553 changed and 37 unchanged words, resolve to the same function symbol/normalized body or the same section offset. Non-relocation bytes agree and no reference remains unresolved. Original whole-data identity is not claimed. `audit_refs.py` recomputes these checks from the actual compressed ELFs.

## Finite signed runtime evidence

The captured AMM calls Pump through its captured upgradeable loader. Sixteen local synthetic cases yield 48 original/parent/candidate executions and signed transaction records. Seven cases succeed on all three images; nine reject on all three. Original and candidate agree on state, error, return data, CPI/event bytes, transaction wire and ordered logs, excluding only complete runtime compute-meter lines. Parent also agrees in this finite set. **No runtime behavior improvement is claimed.**

- The existing 13-case multi-hop admission/Token22 corpus is reused with only a local path adapter.
- Two additional 100% Token22-fee buy cases retain the existing 100-unit cap (amounts 3 and 1,000). Both succeed and cover ordinary arithmetic.
- One separately preserved variant changes the two transfer-fee maximum fields to u64::MAX. It rejects earlier with 6041 at `trade_v3.rs:317`; it does not exercise the zero-quote helper error. Its historical filename contains `zeroquote`, but its verified classification is an upstream gate.

The helper would use the original bare PumpError conversion for quote zero and the recovered output helper for a zero denominator, unlike the removed local Source 581/manual-div path. Neither boundary was reached in these fixtures; no runtime error-origin recovery is claimed. The net-quote guards stop the attempted zero-net path first. Mainnet reachability is not established.

Original producer/fixture bytes are retained under `runtime/inputs/upstream`. Executed local copies retain the same JSON values; the fixture's only text serialization change is newline conversion, checked against the exact upstream bytes. The source-derived path adapter is preserved. Input hashes, actual loaded ELF prefixes, captured ProgramData headers/allocation tails, signatures, prestates and all declared output hashes are joined by the finite verifier. The two execution receipts declare 6 and 3 outputs respectively; all 9 outputs and both receipts are retained.

## Verification

From the repository root, with its pinned Python requirements:

```sh
python -B research/pump-multihop-token-quote-20261029/verify.py --repo-root .
python -B research/pump-multihop-token-quote-20261029/test_verify.py --repo-root .
python -B research/pump-multihop-token-quote-20261029/audit_refs.py --repo-root .
```

The first command recomputes source/build/runtime correspondence and the complete census; the second runs finite resealed mutation controls. The audit independently resolves the helper and data references. Optimized Python is rejected. No compiler or VM is launched by verification. The finite controls passed: 16 resealed mutations, output-receipt and repository source/fixture substitutions, and four optimized-Python guards. Runtime consistency checks are not independent execution attestation; post-state snapshots come from the retained producer, not a separate post-state observer.
