# Pump multi-hop sell fee subtraction recovery

This is the follow-up to the token-quote recovery in PR1164. It replaces the sell branch's two local `sub` calls with the existing recovered `trade::sub3(gross_sell, pf, cf)` call. `sub3` becomes `pub(crate)` so the sibling module can call it; its body and physical Source294 line remain unchanged. Only multi_hop_curve_swap.rs line679 and trade_v3.rs line294 change in this packet. The earlier three token-quote source lines and its frozen evidence remain in the preceding packet.

The original sell path calls sub3 at +0x1c08 with the gross sell quote and the independently gated protocol/creator fees, then checks SellZeroAmount. The current parent calls local sub twice. This recovers an actual callee and error-payload boundary, not an expression-order experiment. Both implementations sequentially subtract protocol then creator fees with checked u64 arithmetic. Underflow changes the reported source from the local helper's Source65 to recovered trade Source294, as in the original helper; these fixtures do not exercise that underflow.

This remains a partial machine-code fidelity improvement. No complete function window or whole ELF becomes equal, and the candidate becomes farther from the original size.

| Measurement | Initial selected control | Published1164 parent | Sell-helper candidate |
|---|---:|---:|---:|
| Target bytes (original18,584) |18,056|17,704|17,608|
| Absolute size difference |528|880|976|
| Aligned differing8-byte slots |3,423|3,372|3,336|
| Normalized windows |1,019/1,035|1,019/1,035|1,019/1,035|
| Raw windows |183|183|183|
| Lost/gained memberships |0/0|0/0|0/0|

The follow-up reduces the retained alignment diagnostic by36slots; cumulative reduction is87slots. SequenceMatcher can count moved blocks as deleted and inserted slots, so this is not a semantic-distance metric. The complete matched membership sets are unchanged, including after the helper visibility change.

## Parent lineage and actual build

`provenance/parent-lineage.json` pins the immutable preceding packet, research/pump-multihop-token-quote-20261029, at MANIFEST SHA25654639f0c28720c6231e70dd330998f5c001caafa8e65dfcc559b5fba3b38e603 and PR1164 head9d7b5652ce8b20692bea817a9f0660b6a126cf36. All68 prior members remain unchanged. The new parent source archive/map and six build files are byte-identical to that packet's candidate. Verification checks the historical packet and source lineage without applying its old maintained-source equality check to the new source.

The66-input compiler workspace is the same selected D037 Cargo recipe plus four maintained Rust changes from merged1110 and the earlier token-quote change. This is not a checkout-wide main build. Native macOS188raw and this Linux183raw are different cohorts. Preprobe main d2cb88d3aad7b4a324dd6abe09426f9a7eefcf3c and all then-open source patch scopes were checked; the only overlapping Pump patch was our own open1164.

One new normal compile used the unchanged v1.44 offline/locked recipe and physical-source wrapper. Its source inputs remained unchanged during compilation. The parent compile is reused from1164, not rerun. There is no repeat-build claim, IR edit, assembly edit or ELF patch.

| Image | Parent SHA256 | Candidate SHA256 |
|---|---|---|
|Symbols|99ee3d669ef817c7e66e42453f12e3706fbbbfa965173cd2c533db42a036d837|b79428215bac7c4cb487681ea3a5cdad84197fcaa04142a0e68f4a4706008898|
|Stripped|47cb3e2aac8bd8b444a820d3ed4a11f37d58cd7da1ad571692f9b7d22a39887d|a1a9223a33274b687d263a7ed263dbbd29429abe9532a61c3959b4d5b6e6bd2e|

## Bounded reference audit

The complete576-byte sub3 and its four immediate callee bodies have the same narrow normalized bytes across original, parent and candidate. The original target has two sub3 sites; the parent has none and this candidate restores the sell site only. The buy subtraction remains unchanged. The50 common direct callees and all715 references inside those bodies remain mapped identically. Across1069 named functions, only swap_hop changes its narrow normalized body. Raw CALL opcodes decrease91 to90, including one imported syscall in each; internal direct calls decrease90 to89. The earlier tokens_for_quote call remains present once. The21 target LDDW references resolve to the same section-offset multiset.

Parent/candidate .rodata is byte-identical. All590 .data.rel.ro relocation words resolve consistently;553 change only for relocated addresses,37 remain unchanged, and non-relocation bytes agree. No original whole-data identity, raw callee identity or recursive transitive closure is claimed. The portable audit recomputes from actual compressed images.

## Retained runtime evidence

Exactly the previous16 cases were rerun against original, published1164 parent and new candidate:48 signed transaction records, seven successful and nine rejected cases on every image. The13-case admission/Token22 corpus includes successful sells, and the three previously declared fee-cap/upstream-gate cases remain unchanged. No fixture variant was added. Source-owned definitions, signed wires, prestates and actual loader image hashes bind the reports to these inputs.

All structured results and ordered logs agree with original, excluding only complete runtime compute-meter lines. No runtime behavior improvement or sell-underflow coverage is claimed. The prior zero-quote-named case still rejects at the earlier6041 Source317 guard; it does not exercise the tokens helper's error path.

Executed producer and fixture bytes are unchanged from1164. The two new controllers select new images and output directories. The two execution receipts declare six plus three output files, all retained.73 input records comprise69 byte joins and four pinned host-file fingerprints. These are finite consistency checks, not independent execution attestation; post-state snapshots are not independently observed.

## Verification

With Python3.12 and solders0.27.1, from the repository root:

```sh
python -B research/pump-multihop-sell-fees-20261029/verify.py --repo-root .
python -B research/pump-multihop-sell-fees-20261029/test_verify.py --repo-root .
python -B research/pump-multihop-sell-fees-20261029/audit_refs.py --repo-root .
```

Verification recomputes source/build/runtime correspondence, exact historical lineage, both changed maintained source files, whole-window census and bounded references. Finite resealed mutation controls check the declared evidence joins. Optimized Python is rejected. None of these commands compiles source or replays the VM.
