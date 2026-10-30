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

## Residual at 0.97158 (130 differing diff lines; first 761 instructions equal)
Two branch-polarity sites that cancel in size (-8 B / +8 B), plus offsets of jumps across them:
- after `post_fee_amount` (buy trade_amount): orig `jeq r1,2,+1; ja err`, ours `jne r1,2,err`;
- after buy `get_fees`: orig `jne r1,0,err`, ours `jeq r1,0,+1; ja err`.
Later: raw_output `checked_add` overflow-closure block and the transfer_input key load block are placed differently.

### llc oracle on this build's post-opt IR (irhc.py / bmove.py / od.py here; ~0.5 s per variant)
| IR block move (on top of the 0.97158 IR) | bytes | ratio | oracle slots |
|---|---:|---:|---:|
| none | 18,584 | 0.97158 | 908 |
| bb261 (get_fees Ok continuation) right after bb41 | 18,576 | 0.96960 | - |
| + bb258 (checked_sub overflow-closure block) right after bb37 (post_fee_amount call) | 18,584 | 0.97333 | 873 |
| + bb278 (native test) after bb75 | 18,584 | 0.97420 | 873 |
Greedy single-block-move search (1,710 moves per round, two regions) finds nothing further.
In our IR the sell-arm head (bb84 and its successors) sits between bb41 and bb261: LLVM threads the two
`buy` tests (trade_amount `if buy` and the arm `if buy`), and the threaded block order puts the sell
head ahead of the buy get_fees continuation.

### Source spellings measured on the 0.97158 base (all line-preserving)
Byte-identical (SAME): `?` -> Ok-first/Err-first match at post_fee_amount, checked_sub, get_fees,
net_quote_for_budget, sub3; trade_amount polarity (`if !buy`), `match buy` for trade_amount and for the
arm split, block-bound post_fee value, ok_or_else via match, require_ata key bindings.
Changed but worse: `.map_err(|e| e)` / `.map(|v| v)` (same swap_hop), Option match / let-else for the
checked_sub (+160 B, closure dropped), trade_amount via a nested helper (plain, #[inline], #[inline(always)]: 18,592 B),
checked_sub via a plain helper (18,696 B), mayhem `== false` (slots 1837), native default lhs (0.97027).
