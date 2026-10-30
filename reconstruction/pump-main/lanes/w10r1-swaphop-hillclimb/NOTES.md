# w10r1-swaphop-hillclimb: 0x5b3b0 multi_hop_curve::swap_hop

Angle: automated equal-size mutation hill-climb on programs/pump/src/multi_hop_curve_swap.rs.
Tools here: `hc.py` (driver: fastbuild + target_metric + score.py, ledger record per trial,
sha-keyed cache), `mutations*.py` (line-preserving respellings; sets 1-3 from
w7r1-swaphop-hillclimb, set 4 new for this wave), `apply.py <module> <m1,m2>`.

Base: origin/main 37f32a4f2 + swarm/x1-p2-buy-fees-whole-netquote-completefill (581362582).

## Metrics (score.py vs fresh main build: 1032 normalized / 347 raw)
| build | bytes | ratio | slots_diff | official | losses |
|---|---:|---:|---:|---|---|
| main 37f32a4f2 | 18,584 | 0.85352 | 1023 | 1032/347 | - |
| + x1-p2 fees-whole | 18,584 | 0.92654 | 1047 | 1032/347 | none |
| + res-le-first + d1 (= stitch x1-le-d1) | 18,584 | 0.93441 | 930 | 1032/347 | none |
| **+ cap-fee-inputs-always-q** | **18,584** | **0.97158** | **925** | **1032/347** | **none** |

unstripped sha256 (best): 305b7f78abd109f5e2fb5681a117c781aa4dbefb3ad0e957dd15733b42623320

## Mechanism of the new step (cap-fee-inputs-always-q)
`fee_config_len` and `cap` come from a same-line `#[inline(always)]` nested
`fn fee_inputs(curve: &BondingCurve, fee_config, mint) -> Result<(usize,u128)>`, called with `?`.
The `&BondingCurve` deref coercion is a call argument, so it is computed before the fee_config
AccountInfo clone and stays live through EarlyCSE (y1-hop-llvm's IR trace). This removes the
-0xaa8/-0xab0 spill-slot swap (StackSlotColoring weight order, region-1 lane #2526).
y1-hop-llvm's spelling (`match fee_inputs(..) { Ok(v)=>v, Err(e)=>return Err(e) }` outside,
`?` inside) was 16 B short on the old base; with `?` outside and the explicit match inside,
on the x1+le+d1 base, the function keeps the original 18,584 B.

Ledger: ac2d5a42 (composite), hc10-* rows (each hill-climb trial).
