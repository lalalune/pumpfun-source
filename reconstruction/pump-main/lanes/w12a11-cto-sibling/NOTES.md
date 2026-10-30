# Lane w12a11-cto-sibling (wave 12, pool a)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: sibling-idiom transplant from byte-matched handlers (pump-amm `admin_cto_pool`, pump-fees
`admin_cto_sharing_config`, Pump Main `collect_creator_fee`, `distribute_creator_fee_v2`, `sweep_fees`, `migrate`).
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w12a11-cto-sibling/` (not in git).
Ledger approach `sibling-idiom`, keys `0x22a10-w12-20a1ae9-sib-*-v1`.

## Mechanism: AMM per-arm `is_cashback_coin` (orig structural difference S9)

pump-amm `admin_cto_pool` (whole-ELF identical, same author and feature) computes

```rust
let is_cashback_coin = if is_holder_reward { false } else { pool.is_cashback_coin };
if let Some(creator_fee_bps) = creator_fee_bps {
    require!(!is_native_or_usdc(&pool.quote_mint), CreatorFeeNotConfigurableForQuote);
    require!(!is_cashback_coin, CreatorFeeNotAllowedForCashbackCoin);
    ...
```

Transplanted into `validate` (line 314, a layout-pad line, so no `line!()` moves) with the 330 check testing it:

```rust
 let cashback=if holder{false}else{st.cashback};      // line 314
 ...
  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}   // line 330
```

`cashback` is a constant `false` on the holder arm, so MIR JumpThreading threads the 330 switch back through
the fee-tag test and the 326 test: the holder arm gets its own fee-tag and 326 tests and skips 330, the
non-holder arm keeps 326 then 330, and both share one 326 error block. That is exactly the original's
validate shape (w12a09-cto-cleanroom outline S9: orig B24-B27 holder arm, B48-B52 non-holder arm), which main
lacked (one shared fee block, 330 testing `holder` dynamically).

| build | admin_cto bytes | ratio | normalized / raw losses |
| --- | ---: | ---: | --- |
| main 84bf9b1 (#2749, L1) | 27,400 | 0.45147 | |
| main + `amm_cb_local` (t18) | 27,384 (-16) | **0.48367** | 0 / 0 normalized; size moves later windows |

Needs +16 B of compensation to land; search in progress (see SUMMARY.json when done).

## Other sibling idioms measured (on main 84bf9b1 = L1 unless noted)

| trial | idiom (sibling) | bytes | ratio |
| --- | --- | ---: | ---: |
| t13 | named `let rent=Rent::get()?` in the sweep native arm (collect_creator_fee / distribute_v2) | 27,368 | 0.44964 |
| t14 | event `new_creator: target` (AMM `new_coin_creator: coin_creator`) | 27,440 | 0.27481 |
| t15 | event `is_holder_reward: holder, is_cashback_coin: cashback` (AMM) | 27,408 | 0.4487 |
| t16 | t14 + t15 | 27,528 | 0.23132 |
| t17 | old fee read after creator/holder/cashback stores (AMM store order) | 27,408 | 0.4514 |
| t01 | rent local on main 20a1ae9 (h1) | 27,416 | 0.43816 |
| t04 | rent local + frozen_first on main 20a1ae9 | 27,400 | 0.43229 |

Keeping `target` live until the event (t14/t16) collapses the frame (ratio -0.18 to -0.22).

## Frame note (IR oracle on main 20a1ae9 IR from w12a01-cto-frame)

`frameoracle.py --drop-lifetime _188 --drop-lifetime _194` (the final `emit_cpi!` temporaries
`[AccountInfo;1]` 48 B and `[&[u8];2]` 32 B) has exactly the size of the +80 B break between fi54
(`val.sroa.6.i`) and fi109 (`_184`): with them unmerged, fi109..fi122 sit at the same -16 delta as fi43..fi54
(the extra 16 B `_117.i74` wallet signer slice). Only the sizes are confirmed: the accesses of `_188` itself vote
for the original top slot (T 0x38), so which original objects fill those 80 B is still open. Alone the masked
ratio drops (0.43919 -> 0.42451) because holder_key/mint/ISel temps move to -48.
