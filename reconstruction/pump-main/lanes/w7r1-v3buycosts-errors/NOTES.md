# Lane w7r1-v3buycosts-errors: `trade::v3_buy_costs` (0x80df8), error-path angle

Base: origin/main 2162b3b00 (rebuilt: 1027 normalized / 276 raw, v3_buy_costs 2,136 B, ratio 0.920, 19/21 slots).
**No source change is proposed here.** The target was matched during this round by the sibling lane
w7r1-v3buycosts-blockorder (PR #2272), with an error-path mechanism: both `add3` errors leave through one
labeled block (`'s: { .. Err(e) => break 's Err(e) .. }`) and a single `?`, so their Err arm (the sret
stores) is shared in IR. This lane verified that result and tested the nearest alternative error forms.

| Trial | Bytes | ratio | -/+ slots | normalized / raw | gains / losses |
| --- | ---: | ---: | ---: | --- | --- |
| base 2162b3b00 | 2,136 | 0.920 | 19 / 21 | 1027 / 276 | - |
| PR #2272 head, independent rebuild | **2,120** | **1.000** | 0 / 0 | **1028** / 276 | +0x80df8 / none |
| `#[inline(always)] fn add3_pair(..)->Result<(u64,u64)>` with `?` inside, one `?` outside | 2,112 | 0.982 | 5 / 4 | 1027 / 276 | none |
| same helper, no inline attribute | 2,112 | 0.982 | 5 / 4 | 1027 / 276 | none |

Both helper variants are byte-identical to each other and to the immediately-invoked closure variant
(blockorder g04, sha ac8b0f86): the sret allocation is already the original's, and the only residual is the
add3#1 Ok-check polarity (`jne` vs the original `jeq` + `ja`). A function or closure boundary is LLVM-inlined
and loses the MIR block order that the labeled block keeps, so among the shared-Err-arm spellings only the
labeled block reproduces the original.

## IR-oracle results (one-function llc module, diagnostic only)

* Splitting every CFG edge with an empty block or a lifetime.start-only block (43 edges, on the base IR and on
  the bb4-lifetime-moved IR): no 0-diff result; the best stays the base (9/11 lines) or the -51/+51 front state.
* Merging the 371 and 375 `to_string` `unwrap_failed` panic blocks in IR: the RA becomes the original's, but block
  placement changes (2,112 B). A full block-order scan (1,980 moves) on that IR never improves, so IR block order
  does not drive placement there.
* Why heuristics cannot work (confirms w4): with overflow-checks on, only MIR Asserts carry `!prof`; no Assert
  survives in this function, and the BPI cold/noreturn estimates top out below the needed frequency ratio.
  The match came from IR structure (one shared Err arm), not from weights.

Ledger ids: 19c995b1 (verify #2272), 4b003fcf, 20dce9c0 (helper variants), 02151963 (IR scans).
