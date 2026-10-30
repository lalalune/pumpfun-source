# Lane w7r1-v3buycosts-sibling: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Angle: take spellings from sibling code that already matches (v3_execute_buy, the callers, accrue_fees, buy_v2, the
`#[cold]` error helpers in set_reserved_fee_recipients / volume_accumulator) and use them in v3_buy_costs.

**Outcome: this angle found nothing. The target is matched by the concurrent lane w7r1-v3buycosts-blockorder
(PR #2272: both add3 errors leave through one labeled block and one `?`, 2,120 B, 1028/276, no losses).** This lane
stopped after hearing of that match. The source is unchanged; this PR adds notes only.

Base: origin/main 2162b3b00. Built here: 1027 normalized / 276 raw, unstripped fd54954f (the IR-capture build of the
same source is 33b242e6, and its stripped candidate.so is byte-identical). v3_buy_costs: 2,136 B, ratio 0.920,
19/21 differing slots, 17/17 calls.

## Source trials (ledger keys `0x80df8-main-2162b3b-sib-<trial>-v1`; every trial keeps 1027/276 with no gains and no
losses unless the table says otherwise)

| trial | sibling idiom | bytes | ratio | -/+ | result |
| --- | --- | ---: | ---: | ---: | --- |
| first-match | explicit `match add3(..){Ok(v)=>v,Err(e)=>return Err(e)}` | 2176 | 0.741 | 62/69 | worse |
| second-match | v3_execute_buy `match post{Some=>add3(..)?,None=>0}` | 2144 | 0.914 | 20/23 | worse (if-let saves a jump) |
| second-resmatch | `match post{Some=>add3(..),None=>Ok(0)}?` | 2136 | 0.920 | 19/21 | byte-identical |
| second-mapor / second-maporelse | `post.map_or(Ok(0),..)?` / `map_or_else` | 2136 | 0.920 | 19/21 | byte-identical |
| second-transpose | `post.map(..).transpose()?.unwrap_or(0)` | 2136 | 0.876 | 30/32 | worse |
| second-map-match | `match post.map(add3..){Some(r)=>r?,None=>0}` | 2176 | 0.895 | 23/30 | worse |
| second-fees-local / second-destructure | copied `fees` local / struct pattern | 2136 | 0.920 | 19/21 | byte-identical |
| mapid-first/-second/-375/-gross | caller idiom `.map_err(core::convert::identity)?` on each `?` | 2136 | 0.920 | 19/21 | byte-identical |
| front-destructure | accrue_fees `let (b,_)=protocol_fee_split(..)` | 2136 | 0.920 | 19/21 | byte-identical |
| front-block / front-unwrap-or / front-helper | block tuple / `map().unwrap_or(0)` / plain nested `buyback_of` fn | 2136 | 0.920 | 19/21 | byte-identical |
| mayhem-gt | `is_mayhem>0` | 2136 | 0.920 | 19/21 | byte-identical |
| postfee-local | `Option<u64>` post-fee local | 2256 | 0.579 | 100/117 | worse, 19 calls |
| total-match | 371 as `match ..{None=>return Err(error!(..))}` | 2136 | 0.920 | 19/21 | byte-identical |
| total-swap / sum-swap | swap the operands of the 371 / 375 checked_add | 2104 / 2136 | 0.835 / 0.892 | | worse |
| opt-local | 375 Option bound to a local | 2136 | 0.916 | 20/22 | gross-error loads swap |
| tuple-swap / ret-local / gross-closure | `(net,g)` order / `Ok(costs)` local / closure in place of fn item | 2136 | 0.920 | 19/21 | byte-identical |
| gross-closure-var | buy_v2 `gross_total`-style local closure passed to and_then | 2136 | 0.904 | 23/25 | worse |
| gross-cold | `#[cold]` gross_up_quote_error (rent_exempt_error idiom) | 2128 | 0.894 | 26/27 | error moved to the end of the function |
| costs-cold | `#[cold]` on v3_buy_costs | 2136 | 0.920 | 19/21 | callers 0x837a8 and 0x147ba0 lost (1025) |

Oracle recheck on the current main IR (one-function llc output reproduces 2,136 B at -9/+11 against the original):
dropping the front's LLVM-inliner ZST lifetime markers (the effect of a MIR-inlined protocol_fee_split), or emptying or
removing bb4 (mayhem && post Some), gives 2,120 B with the original's sret spill, but the front registers change
(-51/+51). Merging the 371/375 to_string panics gives 2,112 B with a layout change. These agree with the w6r2/w4 results.

## Takeaways

* Almost every sibling spelling folds to identical IR. Only the CFG shape of the error paths moves this function.
* The winning change (#2272) is of exactly that kind: one shared add3 Err arm in IR. It is not a sibling idiom.
  second-resmatch (a Result merged before `?`) was the closest thing tried here, and it folded to identical IR
  because only the second add3 was involved.
