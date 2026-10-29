# Lane v3execute-semantic

Target: `0x83c00` `trade::v3_execute_buy` (programs/pump/src/trade_v3.rs), original 3,440 B.

## Results

| Trial | Change | cand bytes | ratio | official | ledger id |
| --- | --- | ---: | ---: | --- | --- |
| main d2cb88d | baseline | 3,408 | 0.7333 | 1019 / 188 | - |
| t01-init-helper | `init_volume_user(&mut UserVolumeAccumulator,&Signer)` helper replaces the inline pubkey-default check | 3,408 | 0.7595 | 1019 / 188, no gains/losses | 0a19d256c3464fbaa9edc443a30e0616 |
| t02-mint-wrapper | + `#[inline(always)] transfer_curve_mint_tokens` taking `&InterfaceAccount<Mint>`; decimals read inside | 3,408 | 0.7595 | 1019 / 188 | 1f1de20d8668446d8b056e30d9693de3 |
| ve | + `let (user_quote,curve_quote)=if is_sol{(None,None)}else{(Some(..),Some(..))};` before `transfer_from_user` | 3,432 | 0.7687 | 1019 / 188, no gains/losses | 7364d0c6316c43b28b232650a711ec0d |

t01 is a port of the prior `execute-init-helper` partial (research/goal-pump-recovery-20261028) onto main.

## Block map (original 0x83c00)

- 0x83c00-0x83c80: arg spill, `apply_buy` (call 0x39ef)
- 0x83c88-0x83ce0: `amount + post.base_out` checked add
- 0x83ce8-0x83ee8: `transfer_curve_tokens` (call 0x16dd), seeds key copy at -0x40..-0x28
- 0x83f00-0x84010: `a.user.key()==whitelist_pda` (call 0x25edd), then init_volume_user
- 0x84078-0x84150: two `accrue_fees` (call 0x3b66) with post branch
- 0x84158-0x84218: checked add total, `is_sol` select, `add(pool_quote,total_buyback)` (call -0x533)
- 0x84608-0x846d8: `transfer_from_user` (call 0x264a)
- 0x846f0-0x84818: native/quote-token buyback transfer
- 0x84830-0x84968: two `post_fee_amount` (call 0x2110), checked sub, Ok tuple
- 0x84468-0x84588: whitelist reload/sync branch (outlined late)

## Residuals after t01

Register allocation / scheduling only (call multiset equal). Original spills all five
stack args (quote_fee, total_buyback, pool_quote, creator_fee, protocol_fee) up front,
computes `&a.base_token_program` (a+0x18) before them, and loads `base_mint.decimals` after
the seed key copy; candidate keeps quote_fee in r7, keeps `associated_base_user` in r8,
loads decimals first. 4 slots short.

## Evidence: decimals load order (t02)

At all three original `transfer_curve_tokens` call sites (0x83ed8 here, 0x13d5c8 and 0x142178 in the
buy_v2 handlers) the original reads `base_mint.decimals` (`ldxb [mint+0x30]`) after the seed key copy, and
computes `&base_token_program` first. The candidate read decimals first at all three sites. Reading decimals
inside an inline(always) wrapper that takes `&InterfaceAccount<Mint>` reproduces the late decimals load (ratio
unchanged on its own; ve without the wrapper scores the same 0.7687). The buy_v2 lanes may want this.

## Rejected so far

- wrapper taking `&SellV3` (0.7262), all-three tuple let `(amount,user_ata,curve_ata)` (0.7524; system_program
  load moves after the merge as in the original, but the amount phi lands in pool_quote's spill slot),
  amount let then options let (0.7461).
