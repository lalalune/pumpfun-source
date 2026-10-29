# Per-site hot/cold map

hot = call site at >= 2 % of entry block frequency (LLVM inlines the cost-60 clone / cost-130 to_string there); cold = below (threshold 45, stays a call).
Ours from `-C remark=inline -C debuginfo=line-tables-only` (experiment only). Original from CENSUS error-message form by following Source line.

## 0x14f4e0 buy_exact_sol_in

- original error sites (by following Source line): buy.rs:53 hot, buy.rs:53 cold, buy.rs:57 cold, buy.rs:92 cold, buy.rs:110 cold, buy.rs:143 cold, buy.rs:151 cold, buy.rs:133 cold, buy.rs:232 cold, buy.rs:232 cold
- ours: lib.rs:180:9 clone cold, buy.rs:232:141 to_string cold, buy.rs:151:2 to_string cold, buy.rs:133:3 to_string cold, buy.rs:143:3 to_string cold, buy.rs:110:2 to_string cold, buy.rs:92:2 to_string cold, buy.rs:59:2 to_string cold, buy.rs:57:2 to_string cold

## 0x80df8 trade::v3_buy_costs

- original error sites (by following Source line): trade_v3.rs:371 hot, trade_v3.rs:371 hot
- ours: -

## 0x6cd78 legacy_sell::process_cashback_inner

- original error sites (by following Source line): sell.rs:33 hot, sell.rs:33 hot, sell.rs:81 hot, sell.rs:85 cold, sell.rs:102 cold, sell.rs:107 cold, sell.rs:102 cold, sell.rs:114 cold
- ours: sell.rs:33:59 to_string hot, sell.rs:81:9 to_string hot, sell.rs:85:97 to_string cold, sell.rs:51:15 clone hot, sell.rs:43:21 clone hot, sell.rs:44:67 clone hot, sell.rs:44:85 clone hot, sell.rs:56:15 clone hot, sell.rs:102:113 to_string cold, sell.rs:107:5 to_string cold, sell.rs:114:5 to_string cold

## 0x83c00 trade::v3_execute_buy

- original error sites (by following Source line): trade_v3.rs:691 hot
- ours: lib.rs:180:9 clone cold

## 0x13f630 buy_v2::buy_exact_quote_in_handler

- original error sites (by following Source line): buy_v2.rs:769 hot, buy_v2.rs:767 hot, buy_v2.rs:767 hot, buy_v2.rs:780 cold, buy_v2.rs:873 cold, buy_v2.rs:907 cold, buy_v2.rs:921 cold, buy_v2.rs:967 cold, buy_v2.rs:986 cold, buy_v2.rs:979 cold, buy_v2.rs:979 cold
- ours: buy_v2.rs:767:2 to_string hot, buy_v2.rs:769:2 to_string hot, buy_v2.rs:771:2 to_string hot, lib.rs:180:9 clone hot, lib.rs:180:9 clone cold, buy_v2.rs:780:8 to_string cold, buy_v2.rs:873:2 to_string cold, buy_v2.rs:907:3 to_string cold, buy_v2.rs:921:4 to_string cold, buy_v2.rs:979:4 to_string cold, buy_v2.rs:986:3 to_string cold, buy_v2.rs:967:3 to_string cold, buy_v2.rs:997:2 to_string cold

## 0x13b9b8 buy_v2::buy_handler

- original error sites (by following Source line): buy_v2.rs:345 hot, buy_v2.rs:345 hot, buy_v2.rs:345 hot, buy_v2.rs:369 cold, buy_v2.rs:494 cold
- ours: buy_v2.rs:345:2 to_string hot, buy_v2.rs:354:2 to_string hot, buy_v2.rs:356:2 to_string hot, lib.rs:180:9 clone cold, buy_v2.rs:369:8 to_string cold, buy_v2.rs:494:2 to_string cold

## 0x144508 sell_v2::execute

- original error sites (by following Source line): sell_v2.rs:243 hot, sell_v2.rs:245 hot, sell_v2.rs:245 hot, sell_v2.rs:260 cold, sell_v2.rs:379 cold
- ours: sell_v2.rs:243:2 to_string hot, sell_v2.rs:245:2 to_string hot, sell_v2.rs:247:2 to_string hot, lib.rs:180:9 clone cold, sell_v2.rs:260:8 to_string cold, sell_v2.rs:379:2 to_string cold

## 0x4c158 migrate_v2::create_token_account_v2

- original error sites (by following Source line): -
- ours: migrate_v2.rs:416:20 clone hot, lib.rs:180:9 clone hot, migrate_v2.rs:427:57 clone hot, migrate_v2.rs:427:73 clone hot, migrate_v2.rs:420:477 clone hot, migrate_v2.rs:420:493 clone hot

## 0x147ba0 trade::buy

- original error sites (by following Source line): trade_v3.rs:801 hot, trade_v3.rs:801 hot, trade_v3.rs:842 cold
- ours: trade_v3.rs:801:5 to_string hot, trade_v3.rs:802:5 to_string hot, trade_v3.rs:842:5 to_string cold

## 0x14a8a8 trade::sell

- original error sites (by following Source line): trade_v3.rs:1126 hot, trade_v3.rs:1126 hot, trade_v3.rs:1148 cold
- ours: trade_v3.rs:1126:5 to_string hot, trade_v3.rs:1127:5 to_string hot, trade_v3.rs:1148:5 to_string cold, lib.rs:180:9 clone cold

## 0x1489f8 trade::buy_exact_quote

- original error sites (by following Source line): trade_v3.rs:881 hot, trade_v3.rs:881 hot, trade_v3.rs:891 cold, trade_v3.rs:926 cold, trade_v3.rs:1001 cold, trade_v3.rs:993 cold, trade_v3.rs:935 cold, trade_v3.rs:971 cold
- ours: trade_v3.rs:881:5 to_string hot, trade_v3.rs:882:5 to_string hot, trade_v3.rs:891:5 to_string cold, trade_v3.rs:993:13 to_string cold, trade_v3.rs:1001:9 to_string cold, trade_v3.rs:926:9 to_string cold, trade_v3.rs:935:9 to_string cold, trade_v3.rs:971:13 to_string cold

## 0x72810 sweep::execute

- original error sites (by following Source line): sweep_fees.rs:123 hot, sweep_fees.rs:123 hot
- ours: sweep_fees.rs:123:2 to_string hot, sweep_fees.rs:145:122 to_string hot, lib.rs:180:9 clone hot, lib.rs:180:9 clone cold

## 0x1e7c0 create_v2::execute

- original error sites (by following Source line): create_v2.rs:716 hot, create_v2.rs:774 cold, create_v2.rs:732 hot, create_v2.rs:738 hot, create_v2.rs:738 hot, create_v2.rs:719 hot, create_v2.rs:258 cold, create_v2.rs:778 cold, create_v2.rs:205 hot, create_v2.rs:541 hot, create_v2.rs:541 hot, create_v2.rs:758 cold, create_v2.rs:210 hot, create_v2.rs:709 hot, create_v2.rs:709 hot, create_v2.rs:220 cold, create_v2.rs:243 cold
- ours: create_v2.rs:709:3 to_string hot, create_v2.rs:716:2 to_string hot, create_v2.rs:719:3 to_string hot, create_v2.rs:732:2 to_string hot, create_v2.rs:738:2 to_string hot, create_v2.rs:758:3 to_string cold, create_v2.rs:774:3 to_string cold, create_v2.rs:778:3 to_string cold, lib.rs:180:9 clone cold, create_v2.rs:258:2 to_string cold, create_v2.rs:260:172 clone cold, create_v2.rs:260:124 clone cold, create_v2.rs:260:78 clone cold, create_v2.rs:243:2 to_string cold, create_v2.rs:220:2 to_string cold

## 0x77940 token_incentives::claim_token_incentives::cashback::claim_v2

- original error sites (by following Source line): None hot, claim_token_incentives.rs:310 hot, claim_token_incentives.rs:342 cold, claim_token_incentives.rs:333 cold
- ours: token_incentives/claim_token_incentives.rs:305:25 to_string hot, lib.rs:180:9 clone hot, token_incentives/claim_token_incentives.rs:310:4 to_string hot, token_incentives/claim_token_incentives.rs:333:4 to_string hot, token_incentives/claim_token_incentives.rs:342:103 to_string cold, lib.rs:180:9 clone cold

## 0x5b3b0 multi_hop_curve::swap_hop

- original error sites (by following Source line): multi_hop_curve_swap.rs:484 hot, multi_hop_curve_swap.rs:546 cold, multi_hop_curve_swap.rs:686 cold, multi_hop_curve_swap.rs:599 cold, multi_hop_curve_swap.rs:590 cold
- ours: multi_hop_curve_swap.rs:484:9 to_string hot, lib.rs:180:9 clone hot, lib.rs:180:9 clone cold, multi_hop_curve_swap.rs:546:9 to_string cold, multi_hop_curve_swap.rs:686:13 to_string cold, multi_hop_curve_swap.rs:590:13 to_string cold, multi_hop_curve_swap.rs:599:17 to_string cold

## 0x22a10 admin_cto::execute

- original error sites (by following Source line): admin_cto.rs:289 hot, admin_cto.rs:289 hot, admin_cto.rs:298 hot, admin_cto.rs:306 hot, admin_cto.rs:296 hot, admin_cto.rs:326 cold, admin_cto.rs:312 cold, admin_cto.rs:330 cold, admin_cto.rs:330 cold, admin_cto.rs:338 cold, admin_cto.rs:410 hot, admin_cto.rs:719 cold, admin_cto.rs:648 hot, admin_cto.rs:660 cold, admin_cto.rs:284 hot, admin_cto.rs:284 hot
- ours: creator/admin_cto.rs:284:47 to_string hot, creator/admin_cto.rs:289:69 to_string hot, creator/admin_cto.rs:296:106 to_string cold, creator/admin_cto.rs:298:40 to_string hot, creator/admin_cto.rs:306:41 to_string hot, creator/admin_cto.rs:307:97 to_string hot, creator/admin_cto.rs:312:80 to_string cold, creator/admin_cto.rs:326:226 to_string cold, creator/admin_cto.rs:330:40 to_string cold, creator/admin_cto.rs:334:66 to_string cold, creator/admin_cto.rs:338:85 to_string cold, creator/admin_cto.rs:410:2 to_string cold, creator/admin_cto.rs:556:179 to_string cold, creator/admin_cto.rs:648:144 to_string cold, creator/admin_cto.rs:660:24 to_string cold, lib.rs:180:9 clone cold, creator/admin_cto.rs:719:4 to_string cold

