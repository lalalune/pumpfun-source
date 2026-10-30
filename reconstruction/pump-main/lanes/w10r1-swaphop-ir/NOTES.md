# w10r1-swaphop-ir: 0x5b3b0 multi_hop_curve::swap_hop (IR oracle)

Base: origin/main 37f32a4f2 (fresh build 1032/347, swap_hop 18,584 B, ratio 0.85352), plus the
x1-p2 source (swarm/x1-p2-buy-fees-whole-netquote-completefill, TradeFees kept whole; 0.92654 at 18,584 B).

## Oracle
`tools/capir.py` (scratch `--emit=llvm-ir`), `tools/extract.py` + `tools/orc.py` (llc on the extracted
swap_hop; reproduces the fastbuild bytes exactly, `ref_equal`), `tools/dd.py` (diff vs the original with callee
names and masked jump/lddw immediates), `tools/trial.py` (scratch source variant build + metric + score).

## Results
| step | change | bytes | ratio | how |
|---|---|---:|---:|---|
| main 37f32a4 | | 18,584 | 0.85352 | build |
| x1-p2 | fees whole (x1 lane) | 18,584 | 0.92654 | build |
| oracle gepup | cap's `&BondingCurve` GEP above the fee_config clone (region1 lane) | 18,584 | 0.95103 | llc |
| oracle cfnone | + complete_fill tag test `icmp eq 0` | 18,584 | 0.95496 | llc |
| oracle glob | + `a.global` load hoisted from the memcmp block into the over-reserves block | 18,584 | 0.96327 | llc |
| **m8** | x1-p2 + `match complete_fill(..)? { Some(..) => .., None => .. }` | 18,584 | 0.93048 | build, 0 losses |
| **g1** | m8 + `let allowed = { let global = &*a.global; let user = a.user.key(); .. user != global.whitelist_pda }` | **18,584** | **0.93747** | build, 1032/347, 0 losses |

g1's IR plus the gepup edit reproduces the glob oracle byte for byte, so the source now carries every
oracle edit except the cap GEP placement (0.93747 -> 0.96327 once that spelling is found).
`let global=&*a.global` was rejected on the main base; it gains only on the fees-whole base.

## Remaining residual after glob (oracle, 18 hunks)
- fee_config AccountInfo drop: r3 vs r2 (follows the GEP; gone with gepup? no, still there)
- buy_fee_market_cap result: orig loads `[r10-0x6c8]` right after the call and spills to -0xac8 after the tag test
- post_fee_amount tag: orig `jeq r1,2,+1; ja` vs ours `jne r1,2`
- buy get_fees: `mov r9,r3; stxdw [fe8],r3` schedule; tag test `jne r1,0` vs `jeq +1; ja`
- net_quote_for_budget error tail: ours tail-duplicates the 5-insn sret store (orig keeps it once at 0x2718)
- buy apply/transfer block (0x2548 / 0x29f8): a.global reload and `add r2,8` placement
- adapter_difference / post_fill copy block (13 insns) placed after transfer_input's tag test instead of at 0x2d18
- 0x3e00: `jeq r1,0` vs `jne +1; ja`

Ledger: 8f7a8860 (m8), 5d99494c (oracle chain), 11cf2079 (g1), d550791e (g2 rejected).
