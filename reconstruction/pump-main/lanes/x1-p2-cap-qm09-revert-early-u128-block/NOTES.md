# x1-p2-cap-qm09-revert-early-u128-block (target 0x5b3b0 swap_hop)

Base: origin/main e61baa928 plus the swap_hop source of 5e9a02804 (p2: #2403 post_fill
as the 5th element of the reserves-if tuple). Baseline score: x-baseline/1852a872e (1032/337).

Mechanism: revert qm-09 on the tuple base:

    let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };
    ->
    let cap = crate::buy_fee_market_cap(c,&h.base_mint)?;

| build | change | swap_hop B | ratio | score norm/raw | losses | unstripped sha256 |
| --- | --- | --- | --- | --- | --- | --- |
| v0 | p2 control | 18520 | 0.89006 | 1032/337 | none | d99e9d36... |
| v1 | qm-09 revert (`?`) | **18584 (= orig)** | 0.87713 | **1032/347** | none | 33d52ea1... |
| v2 | `.map_err(Error::from)?` | same as v1 | | | | byte-identical |
| v3 | `let cap: u128 = { ...? };` | same as v1 | | | | byte-identical |
| v4 | v1 + buyback checked_sub as explicit match | 18744 | 0.87127 | 1031/337 | 0x60878 | rejected |

v1 raw gains (size realigns everything after swap_hop): 0x29518 0x296f0 0x32530 0x3b598
0x3b738 0x3cd50 0x47d00 0x524f0 0x54c90 0x54db8. Calls [107,1] on both sides.

Error-epilogue census (stb [out+0x5a],2 blocks; own script, offsets from the function start):
with the revert, the error layout lines up with the original. The 13-predecessor shared late
block sits at +0x2730 (orig +0x2718), the 3-predecessor block at +0x2748 (orig +0x2730), and
every error block from +0x37f0 onward is at exactly the original offset. In p2 (v0), that
13-pred block was hoisted to +0x1ad8. The `?` revert restores the early-block/late-block
split, so no late-epilogue-host follow-up is needed. v4 shows that an explicit match
duplicates error!() (109 calls).

Remaining residual (v1, orig-only slots per 0x800 bucket): 0x0:12, 0x800:16, 0x1000:39,
0x1800:89, 0x2000:45, 0x2800:68, 0x3000:13, 0x3800:17, 0x4000:13, 0x4800:2. Most of it is
spill-slot pairs swapped ([-0xaa8]/[-0xab0], [-0xad0]/[-0xad8]) and the order of the buy-arm
get_fees / net_quote_for_budget call blocks around orig +0x19a8..+0x1b50 (the original
places the 0x6d0 call pair after the fee-config setup block).
