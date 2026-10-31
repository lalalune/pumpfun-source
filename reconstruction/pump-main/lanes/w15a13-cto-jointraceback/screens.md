| trial | base | bytes | M | ratio | note |
| --- | --- | ---: | ---: | ---: | --- |
| a1 | ed47ac7 | 27448 | 1710 | 0.51182 | join tuple order (skip,collect_old) |
| a2 | ed47ac7 | 27448 | 1900 | 0.56869 | skip as expression !(shared&&holder) after the tree; tree yields collect_old only |
| a3 | ed47ac7 | 27400 | 2248 | 0.67346 | skip as mut local init true, cleared in holder-shared arm |
| a4 | ed47ac7 | 27448 | 1710 | 0.51182 | collect_old as mut local set in non-shared arm; tree yields skip |
| a5 | ed47ac7 | 27448 | 1710 | 0.51182 | all three join outputs as mut locals (statement tree) |
| a6 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; !shared arm first (if-else nesting kept) |
| a7 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; inner !holder arm first |
| a8 | ed47ac7 | 27416 | 2247 | 0.67296 | target override before sharing payload in the shared non-holder arm |
| a9 | ed47ac7 | 27432 | 1915 | 0.57335 | collect_old operand order: creator test first |
| a10 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; collect_old as if holder_reward{false}else{creator!=default} |
| b1 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; Ok hop carries skip |
| b2 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; Ok hop carries collect_old |
| b3 | ed47ac7 | 27400 | 2243 | 0.67196 | Ok hop field order (sharing_update,target,cashback) |
| b4 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; Ok hop field order (target,cashback,sharing_update) |
| b5 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; Ok hop field order (cashback,target,sharing_update) |
| b6 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; block tuple field order skip before collect_old |
| b7 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; block tuple: flags first |
| b8 | ed47ac7 | 27400 | 2247 | 0.67316 | block tuple: sharing_update before target |
| c1 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; wallet gate without ; (expression) |
| c2 | ed47ac7 | 27392 | 2243 | 0.67206 | wallet gate as then().transpose()? |
| c3 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; wallet gate let ()=..? |
| c4 | ed47ac7 | 27400 | 2248 | 0.67346 | = main bytes; wallet gate inverted if |
| c5 | ed47ac7 | 26768 | 2117 | 0.64181 | sweep gate unwrap_or(Ok(0))? |
| c6 | ed47ac7 | 26816 | 1569 | 0.47524 | sweep gate skip.then_some(Ok(0)).unwrap_or_else(sweep)? |
| c7 | ed47ac7 | 27440 | 1776 | 0.53166 | sweep gate if let false=skip |
| c8 | ed47ac7 | 27440 | 1776 | 0.53166 | sweep gate match skip false first |
| c9 | ed47ac7 | 27440 | 1776 | 0.53166 | sweep gate match skip true first |
| a8c2 | 86e2a6b | 27408 | 2245 | 0.67246 | a8+c2 |
| m0 | 86e2a6b | 27400 | 2249 | 0.67376 | = main bytes; unedited capture (eq_main) |
| a8_s_dest_borrow | 86e2a6b | 27336 | 2236 | 0.67067 | size repay: a8 + knob s_dest_borrow |
| a8_prep_match | 86e2a6b | 27416 | 2229 | 0.66757 | size repay: a8 + knob prep_match |
| a8_L_fee_unwrap_again | 86e2a6b | 27424 | 2231 | 0.66806 | size repay: a8 + knob L_fee_unwrap_again |
| a8_s_old_borrow | 86e2a6b | 27336 | 2204 | 0.66107 | size repay: a8 + knob s_old_borrow |
| a8_g_old_fee_first | 86e2a6b | 27416 | 2247 | 0.67296 | size repay: a8 + knob g_old_fee_first |
| a8_st_ql_first | 86e2a6b | - | - | compile error | size repay: a8 + knob st_ql_first |
| a8_L_share_none_first | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob L_share_none_first |
| a8_w_ev_creator_first | 86e2a6b | 27480 | 2231 | 0.66736 | size repay: a8 + knob w_ev_creator_first |
| a8_p_ev_ts_last | 86e2a6b | 27672 | 1678 | 0.50015 | size repay: a8 + knob p_ev_ts_last |
| a8_cu_fee_oldunwrap | 86e2a6b | 27424 | 2231 | 0.66806 | size repay: a8 + knob cu_fee_oldunwrap |
| a8_w_create_rev | 86e2a6b | 27688 | 1715 | 0.51103 | size repay: a8 + knob w_create_rev |
| a8_cu_typed | 86e2a6b | 27384 | 2238 | 0.67066 | size repay: a8 + knob cu_typed |
| a8_cu_replace | 86e2a6b | 27416 | 2247 | 0.67296 | size repay: a8 + knob cu_replace |
| a8_ev_nc_target | 86e2a6b | 27472 | 1295 | 0.38743 | size repay: a8 + knob ev_nc_target |
| a8_ev_auth_deref | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob ev_auth_deref |
| a8_ev_cb_local | 86e2a6b | 27408 | 2226 | 0.66677 | size repay: a8 + knob ev_cb_local |
| a8_ev_reset_shared | 86e2a6b | 27288 | 2003 | 0.60132 | size repay: a8 + knob ev_reset_shared |
| a8_ev_mint_key | 86e2a6b | 27432 | 2218 | 0.66407 | size repay: a8 + knob ev_mint_key |
| a8_ev_ts_clockvar | 86e2a6b | 27416 | 2238 | 0.67026 | size repay: a8 + knob ev_ts_clockvar |
| a8_ev_ts_map | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob ev_ts_map |
| a8_pool_prog_let | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob pool_prog_let |
| a8_ev_ts_presig | 86e2a6b | 26824 | 1967 | 0.59570 | size repay: a8 + knob ev_ts_presig |
| a8_sh_prog_let | 86e2a6b | 27384 | 2239 | 0.67096 | size repay: a8 + knob sh_prog_let |
| a8_sh_accs_let | 86e2a6b | 27392 | 2123 | 0.63610 | size repay: a8 + knob sh_accs_let |
| a8_sig_mint_acct | 86e2a6b | 27480 | 1696 | 0.50733 | size repay: a8 + knob sig_mint_acct |
| a8_sh_fees_key | 86e2a6b | 27416 | 2247 | 0.67286 | size repay: a8 + knob sh_fees_key |
| a8_wl_ts_clockvar | 86e2a6b | 27432 | 2245 | 0.67216 | size repay: a8 + knob wl_ts_clockvar |
| a8_wl_ts_map | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob wl_ts_map |
| a8_sig_arr | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob sig_arr |
| a8_pu_match | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob pu_match |
| a8_rent_checked | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob rent_checked |
| a8_cu_fee_replace | 86e2a6b | 27408 | 2235 | 0.66946 | size repay: a8 + knob cu_fee_replace |
| a8_g_s7_destscope | 86e2a6b | 27456 | 1778 | 0.53210 | size repay: a8 + knob g_s7_destscope |
| a8_wl_cr_deref | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob wl_cr_deref |
| a8_g_s7_destrev | 86e2a6b | 27416 | 2246 | 0.67266 | size repay: a8 + knob g_s7_destrev |
| a8_g_s7_tokamtne | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob g_s7_tokamtne |
| a8_g_s7_tokzero | 86e2a6b | 27416 | 2248 | 0.67326 | size repay: a8 + knob g_s7_tokzero |
| a8_g_fee_unwrap | 86e2a6b | 27424 | 2231 | 0.66806 | size repay: a8 + knob g_fee_unwrap |
| a8_g_canedit_first | 86e2a6b | 27416 | 2246 | 0.67266 | size repay: a8 + knob g_canedit_first |
| a8_g_s7_dborrow | 86e2a6b | 27336 | 2236 | 0.67067 | size repay: a8 + knob g_s7_dborrow |
| c2_prep_match | 86e2a6b | 27392 | 2225 | 0.66667 | size repay: c2 + knob prep_match |
| a8_g_w_clock_local | 86e2a6b | 27432 | 2245 | 0.67216 | size repay: a8 + knob g_w_clock_local |
| c2_s_old_borrow | 86e2a6b | 27312 | 2202 | 0.66077 | size repay: c2 + knob s_old_borrow |
| c2_s_dest_borrow | 86e2a6b | 27312 | 2234 | 0.67037 | size repay: c2 + knob s_dest_borrow |
| c2_L_share_none_first | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob L_share_none_first |
| c2_L_fee_unwrap_again | 86e2a6b | 27400 | 2232 | 0.66866 | size repay: c2 + knob L_fee_unwrap_again |
| c2_p_ev_ts_last | 86e2a6b | 27648 | 1677 | 0.50007 | size repay: c2 + knob p_ev_ts_last |
| c2_g_old_fee_first | 86e2a6b | 27392 | 2243 | 0.67206 | size repay: c2 + knob g_old_fee_first |
| c2_st_ql_first | 86e2a6b | - | - | compile error | size repay: c2 + knob st_ql_first |
| c2_w_create_rev | 86e2a6b | 27664 | 1714 | 0.51096 | size repay: c2 + knob w_create_rev |
| c2_w_ev_creator_first | 86e2a6b | 27456 | 2230 | 0.66736 | size repay: c2 + knob w_ev_creator_first |
| c2_cu_replace | 86e2a6b | 27392 | 2243 | 0.67206 | size repay: c2 + knob cu_replace |
| c2_cu_fee_oldunwrap | 86e2a6b | 27400 | 2232 | 0.66866 | size repay: c2 + knob cu_fee_oldunwrap |
| c2_ev_auth_deref | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob ev_auth_deref |
| c2_cu_typed | 86e2a6b | 27360 | 2235 | 0.67006 | size repay: c2 + knob cu_typed |
| c2_ev_cb_local | 86e2a6b | 27384 | 2221 | 0.66557 | size repay: c2 + knob ev_cb_local |
| c2_ev_nc_target | 86e2a6b | 27464 | 1296 | 0.38779 | size repay: c2 + knob ev_nc_target |
| c2_ev_mint_key | 86e2a6b | 27408 | 2217 | 0.66407 | size repay: c2 + knob ev_mint_key |
| c2_ev_reset_shared | 86e2a6b | 27280 | 1966 | 0.59030 | size repay: c2 + knob ev_reset_shared |
| c2_ev_ts_map | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob ev_ts_map |
| c2_ev_ts_clockvar | 86e2a6b | 27392 | 2234 | 0.66936 | size repay: c2 + knob ev_ts_clockvar |
| c2_ev_ts_presig | 86e2a6b | 26800 | 1969 | 0.59658 | size repay: c2 + knob ev_ts_presig |
| c2_pool_prog_let | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob pool_prog_let |
| c2_sh_accs_let | 86e2a6b | 27368 | 2121 | 0.63579 | size repay: c2 + knob sh_accs_let |
| c2_sh_prog_let | 86e2a6b | 27360 | 2236 | 0.67036 | size repay: c2 + knob sh_prog_let |
| c2_sh_fees_key | 86e2a6b | 27392 | 2243 | 0.67196 | size repay: c2 + knob sh_fees_key |
| c2_sig_mint_acct | 86e2a6b | 27456 | 1695 | 0.50726 | size repay: c2 + knob sig_mint_acct |
| c2_wl_ts_map | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob wl_ts_map |
| c2_wl_ts_clockvar | 86e2a6b | 27408 | 2241 | 0.67126 | size repay: c2 + knob wl_ts_clockvar |
| c2_pu_match | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob pu_match |
| c2_sig_arr | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob sig_arr |
| c2_cu_fee_replace | 86e2a6b | 27384 | 2233 | 0.66916 | size repay: c2 + knob cu_fee_replace |
| c2_rent_checked | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob rent_checked |
| c2_wl_cr_deref | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob wl_cr_deref |
| c2_g_s7_destscope | 86e2a6b | 27432 | 1778 | 0.53234 | size repay: c2 + knob g_s7_destscope |
| c2_g_s7_tokamtne | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob g_s7_tokamtne |
| c2_g_s7_destrev | 86e2a6b | 27392 | 2242 | 0.67176 | size repay: c2 + knob g_s7_destrev |
| c2_g_fee_unwrap | 86e2a6b | 27400 | 2232 | 0.66866 | size repay: c2 + knob g_fee_unwrap |
| c2_g_s7_tokzero | 86e2a6b | 27392 | 2244 | 0.67236 | size repay: c2 + knob g_s7_tokzero |
| c2_g_s7_dborrow | 86e2a6b | 27312 | 2234 | 0.67037 | size repay: c2 + knob g_s7_dborrow |
| c2_g_canedit_first | 86e2a6b | 27392 | 2242 | 0.67176 | size repay: c2 + knob g_canedit_first |
| c2_g_w_clock_local | 86e2a6b | 27408 | 2241 | 0.67126 | size repay: c2 + knob g_w_clock_local |
| a8c2_prep_match | 86e2a6b | 27408 | 2226 | 0.66677 | size repay: a8c2 + knob prep_match |
| a8c2_s_dest_borrow | 86e2a6b | 27328 | 2234 | 0.67017 | size repay: a8c2 + knob s_dest_borrow |
| a8c2_L_fee_unwrap_again | 86e2a6b | 27416 | 2231 | 0.66816 | size repay: a8c2 + knob L_fee_unwrap_again |
| a8c2_s_old_borrow | 86e2a6b | 27328 | 2202 | 0.66057 | size repay: a8c2 + knob s_old_borrow |
| a8c2_g_old_fee_first | 86e2a6b | 27408 | 2244 | 0.67216 | size repay: a8c2 + knob g_old_fee_first |
| a8c2_st_ql_first | 86e2a6b | - | - | compile error | size repay: a8c2 + knob st_ql_first |
| a8c2_L_share_none_first | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob L_share_none_first |
| a8c2_w_ev_creator_first | 86e2a6b | 27472 | 2231 | 0.66746 | size repay: a8c2 + knob w_ev_creator_first |
| a8c2_p_ev_ts_last | 86e2a6b | 27664 | 1677 | 0.49993 | size repay: a8c2 + knob p_ev_ts_last |
| a8c2_cu_fee_oldunwrap | 86e2a6b | 27416 | 2231 | 0.66816 | size repay: a8c2 + knob cu_fee_oldunwrap |
| a8c2_w_create_rev | 86e2a6b | 27680 | 1715 | 0.51110 | size repay: a8c2 + knob w_create_rev |
| a8c2_cu_typed | 86e2a6b | 27376 | 2235 | 0.66986 | size repay: a8c2 + knob cu_typed |
| a8c2_cu_replace | 86e2a6b | 27408 | 2244 | 0.67216 | size repay: a8c2 + knob cu_replace |
| a8c2_ev_nc_target | 86e2a6b | 27464 | 1295 | 0.38749 | size repay: a8c2 + knob ev_nc_target |
| a8c2_ev_auth_deref | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob ev_auth_deref |
| a8c2_ev_reset_shared | 86e2a6b | 27280 | 2001 | 0.60081 | size repay: a8c2 + knob ev_reset_shared |
| a8c2_ev_cb_local | 86e2a6b | 27400 | 2221 | 0.66537 | size repay: a8c2 + knob ev_cb_local |
| a8c2_ev_ts_clockvar | 86e2a6b | 27408 | 2235 | 0.66946 | size repay: a8c2 + knob ev_ts_clockvar |
| a8c2_ev_mint_key | 86e2a6b | 27424 | 2217 | 0.66387 | size repay: a8c2 + knob ev_mint_key |
| a8c2_pool_prog_let | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob pool_prog_let |
| a8c2_ev_ts_map | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob ev_ts_map |
| a8c2_sh_prog_let | 86e2a6b | 27376 | 2236 | 0.67016 | size repay: a8c2 + knob sh_prog_let |
| a8c2_ev_ts_presig | 86e2a6b | 26816 | 1969 | 0.59640 | size repay: a8c2 + knob ev_ts_presig |
| a8c2_sig_mint_acct | 86e2a6b | 27472 | 1695 | 0.50711 | size repay: a8c2 + knob sig_mint_acct |
| a8c2_sh_accs_let | 86e2a6b | 27384 | 2124 | 0.63650 | size repay: a8c2 + knob sh_accs_let |
| a8c2_wl_ts_clockvar | 86e2a6b | 27424 | 2242 | 0.67136 | size repay: a8c2 + knob wl_ts_clockvar |
| a8c2_sh_fees_key | 86e2a6b | 27408 | 2244 | 0.67206 | size repay: a8c2 + knob sh_fees_key |
| a8c2_sig_arr | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob sig_arr |
| a8c2_wl_ts_map | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob wl_ts_map |
| a8c2_rent_checked | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob rent_checked |
| a8c2_pu_match | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob pu_match |
| a8c2_g_s7_destscope | 86e2a6b | 27448 | 1778 | 0.53218 | size repay: a8c2 + knob g_s7_destscope |
| a8c2_cu_fee_replace | 86e2a6b | 27400 | 2233 | 0.66896 | size repay: a8c2 + knob cu_fee_replace |
| a8c2_g_s7_destrev | 86e2a6b | 27408 | 2243 | 0.67186 | size repay: a8c2 + knob g_s7_destrev |
| a8c2_wl_cr_deref | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob wl_cr_deref |
| a8c2_g_s7_tokzero | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob g_s7_tokzero |
| a8c2_g_s7_tokamtne | 86e2a6b | 27408 | 2245 | 0.67246 | size repay: a8c2 + knob g_s7_tokamtne |
| a8c2_g_canedit_first | 86e2a6b | 27408 | 2243 | 0.67186 | size repay: a8c2 + knob g_canedit_first |
| a8c2_g_fee_unwrap | 86e2a6b | 27416 | 2231 | 0.66816 | size repay: a8c2 + knob g_fee_unwrap |
| a8c2_g_s7_dborrow | 86e2a6b | 27328 | 2234 | 0.67017 | size repay: a8c2 + knob g_s7_dborrow |
| a8c2_g_w_clock_local | 86e2a6b | 27424 | 2242 | 0.67136 | size repay: a8c2 + knob g_w_clock_local |
| pa4 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa4 |
| pa1 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa1 |
| pg3 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pg3 |
| pg9 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pg9 |
| pc9 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pc9 |
| pa4_stok | 86e2a6b | - | - | compile error | skip-polarity form pa4 x sweep/tail form stok |
| pa4_snt | 86e2a6b | 27424 | 1335 | 0.39976 | skip-polarity form pa4 x sweep/tail form snt |
| pa4_stok2 | 86e2a6b | - | - | compile error | skip-polarity form pa4 x sweep/tail form stok2 |
| pa4_sn3 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa4 x sweep/tail form sn3 |
| pa4_samm | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa4 x sweep/tail form samm |
| pa4_sdest | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa4 x sweep/tail form sdest |
| pa4_snvd | 86e2a6b | 27384 | 1655 | 0.49595 | skip-polarity form pa4 x sweep/tail form snvd |
| pa4_swg | 86e2a6b | 27448 | 1699 | 0.50853 | skip-polarity form pa4 x sweep/tail form swg |
| pa4_swo | 86e2a6b | 27456 | 1680 | 0.50277 | skip-polarity form pa4 x sweep/tail form swo |
| pa4_ssw1 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa4 x sweep/tail form ssw1 |
| pa4_scoin | 86e2a6b | 27440 | 1712 | 0.51250 | skip-polarity form pa4 x sweep/tail form scoin |
| pa1_stok | 86e2a6b | - | - | compile error | skip-polarity form pa1 x sweep/tail form stok |
| pa1_snt | 86e2a6b | 27424 | 1335 | 0.39976 | skip-polarity form pa1 x sweep/tail form snt |
| pa1_stok2 | 86e2a6b | - | - | compile error | skip-polarity form pa1 x sweep/tail form stok2 |
| pa1_sn3 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa1 x sweep/tail form sn3 |
| pa1_samm | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa1 x sweep/tail form samm |
| pa1_sdest | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa1 x sweep/tail form sdest |
| pa1_snvd | 86e2a6b | 27384 | 1655 | 0.49595 | skip-polarity form pa1 x sweep/tail form snvd |
| pa1_swg | 86e2a6b | 27448 | 1699 | 0.50853 | skip-polarity form pa1 x sweep/tail form swg |
| pa1_swo | 86e2a6b | 27456 | 1680 | 0.50277 | skip-polarity form pa1 x sweep/tail form swo |
| pa1_ssw1 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pa1 x sweep/tail form ssw1 |
| pa1_scoin | 86e2a6b | 27440 | 1712 | 0.51250 | skip-polarity form pa1 x sweep/tail form scoin |
| pg3_snt | 86e2a6b | 27424 | 1609 | 0.48181 | skip-polarity form pg3 x sweep/tail form snt |
| pg3_stok | 86e2a6b | - | - | compile error | skip-polarity form pg3 x sweep/tail form stok |
| pg3_stok2 | 86e2a6b | - | - | compile error | skip-polarity form pg3 x sweep/tail form stok2 |
| pg3_sn3 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pg3 x sweep/tail form sn3 |
| pg3_samm | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pg3 x sweep/tail form samm |
| pg3_sdest | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pg3 x sweep/tail form sdest |
| pg3_snvd | 86e2a6b | 27376 | 1965 | 0.58894 | skip-polarity form pg3 x sweep/tail form snvd |
| pg3_swg | 86e2a6b | 27440 | 1765 | 0.52836 | skip-polarity form pg3 x sweep/tail form swg |
| pg3_swo | 86e2a6b | 27448 | 1746 | 0.52260 | skip-polarity form pg3 x sweep/tail form swo |
| pg3_ssw1 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pg3 x sweep/tail form ssw1 |
| pg3_scoin | 86e2a6b | 27432 | 1778 | 0.53234 | skip-polarity form pg3 x sweep/tail form scoin |
| pg9_stok | 86e2a6b | - | - | compile error | skip-polarity form pg9 x sweep/tail form stok |
| pg9_snt | 86e2a6b | 27424 | 1335 | 0.39976 | skip-polarity form pg9 x sweep/tail form snt |
| pg9_stok2 | 86e2a6b | - | - | compile error | skip-polarity form pg9 x sweep/tail form stok2 |
| pg9_sn3 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pg9 x sweep/tail form sn3 |
| pg9_samm | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pg9 x sweep/tail form samm |
| pg9_sdest | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pg9 x sweep/tail form sdest |
| pg9_snvd | 86e2a6b | 27384 | 1652 | 0.49506 | skip-polarity form pg9 x sweep/tail form snvd |
| pg9_swg | 86e2a6b | 27448 | 1699 | 0.50853 | skip-polarity form pg9 x sweep/tail form swg |
| pg9_swo | 86e2a6b | 27456 | 1680 | 0.50277 | skip-polarity form pg9 x sweep/tail form swo |
| pg9_ssw1 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity form pg9 x sweep/tail form ssw1 |
| pg9_scoin | 86e2a6b | 27440 | 1712 | 0.51250 | skip-polarity form pg9 x sweep/tail form scoin |
| pc9_stok | 86e2a6b | - | - | compile error | skip-polarity form pc9 x sweep/tail form stok |
| pc9_snt | 86e2a6b | 27424 | 1609 | 0.48181 | skip-polarity form pc9 x sweep/tail form snt |
| pc9_stok2 | 86e2a6b | - | - | compile error | skip-polarity form pc9 x sweep/tail form stok2 |
| pc9_sn3 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pc9 x sweep/tail form sn3 |
| pc9_samm | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pc9 x sweep/tail form samm |
| pc9_sdest | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pc9 x sweep/tail form sdest |
| pc9_snvd | 86e2a6b | 27376 | 1965 | 0.58894 | skip-polarity form pc9 x sweep/tail form snvd |
| pc9_swg | 86e2a6b | 27440 | 1765 | 0.52836 | skip-polarity form pc9 x sweep/tail form swg |
| pc9_swo | 86e2a6b | 27448 | 1746 | 0.52260 | skip-polarity form pc9 x sweep/tail form swo |
| pc9_ssw1 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity form pc9 x sweep/tail form ssw1 |
| pc9_scoin | 86e2a6b | 27432 | 1778 | 0.53234 | skip-polarity form pc9 x sweep/tail form scoin |
| d2 | 86e2a6b | 27400 | 2249 | 0.67376 | = main bytes; Ok hop rebinding without mut |
| d1 | 86e2a6b | 27400 | 2249 | 0.67376 | = main bytes; drop the let mut target=target rebinding after the Ok hop |
| d5 | 86e2a6b | 27544 | 1872 | 0.55931 | prepare_bonding_curve before the Ok hop |
| d3 | 86e2a6b | 27400 | 2249 | 0.67376 | = main bytes; drop the unused _holder field from the block tuple |
| d10 | 86e2a6b | 27152 | 1992 | 0.59955 | block holder as matches!(hopt,Some(true)) |
| d8 | 86e2a6b | 27208 | 2181 | 0.65574 | sk key binding before args |
| a8 | 86e2a6b | 27416 | 2248 | 0.67326 | target override before sharing payload in the shared non-holder arm |
| g1 | 86e2a6b | 27520 | 2251 | 0.67284 | w15a09 g1 re-check: let creator=st.creator before validate, target=creator in the shared arm |
| g1d8 | 86e2a6b | 27304 | 2183 | 0.65516 | g1 + d8 (sk before args) |
| g1d10 | 86e2a6b | 27256 | 1999 | 0.60048 | g1 + d10 (matches! holder) |
| g1c2 | 86e2a6b | 27512 | 2247 | 0.67175 | g1 + c2 (wallet gate then().transpose) |
| g13 | 86e2a6b | 27392 | 2246 | 0.67296 | creator bound at the head of the shared arm (before the holder test) |
| g14 | 86e2a6b | 27352 | 1536 | 0.46057 | g1 + the non-shared arm tests the creator local (st.creator no longer escapes to the memcmp there) |
| g14b | 86e2a6b | 27368 | 1536 | 0.46043 | creator local before validate used only by the non-shared memcmp |
| g11 | 86e2a6b | 27392 | 2246 | 0.67296 | creator by reference before validate, target=*creator |
| h4 | 86e2a6b | 27520 | 2251 | 0.67284 | g1 with Pubkey::new_from_array(st.creator.to_bytes()) |
| h2 | 86e2a6b | 27520 | 2251 | 0.67284 | g1 with st.creator.clone() |
| h8 | 86e2a6b | 27392 | 2246 | 0.67296 | arm target=Pubkey::new_from_array(st.creator.to_bytes()) |
| h7 | 86e2a6b | 27392 | 2246 | 0.67296 | g0 with clone(): target=st.creator.clone() in the shared arm |
| h11 | 86e2a6b | 27400 | 2249 | 0.67376 | = main bytes; arm target=a.bonding_curve.creator.clone() |
| h10 | 86e2a6b | 27392 | 2246 | 0.67296 | g13 with clone(): creator bound at the shared-arm head |
| q1 | 86e2a6b | 27440 | 1777 | 0.53196 | gate if !skip{sweep?}else{0} (sweep body is the then block) |
| q3 | 86e2a6b | 27448 | 1711 | 0.51212 | gate: let mut swept=0; if !skip{swept=sweep()?;} |
| q4 | 86e2a6b | 27440 | 1777 | 0.53196 | gate: deferred swept assigned in both arms, sweep arm first |
| q5 | 86e2a6b | 27400 | 2249 | 0.67376 | gate match !skip{true=>sweep?,false=>0} |
| q6 | 86e2a6b | 27440 | 1777 | 0.53196 | gate: deferred swept assigned in both arms, skip arm first |
| q1p | 86e2a6b | 27440 | 1777 | 0.53196 | gate if !skip{sweep?}else{0} (sweep body is the then block) + pa4 tree yields skip |
| q4p | 86e2a6b | 27440 | 1777 | 0.53196 | gate: deferred swept assigned in both arms, sweep arm first + pa4 tree yields skip |
| q3p | 86e2a6b | 27448 | 1711 | 0.51212 | gate: let mut swept=0; if !skip{swept=sweep()?;} + pa4 tree yields skip |
| r1 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=if skip{None}else{Some(sweep(&ctx,&holder_key))}.transpo |
| r2 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=match skip{true=>None,false=>Some(sweep(&ctx,&holder_key |
| r3 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=(if skip{Ok(None)}else{sweep(&ctx,&holder_key).map(Some) |
| r4 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=if skip{None}else{Some(sweep(&ctx,&holder_key)?)}.unwrap |
| r5 | 86e2a6b | 27440 | 1777 | 0.53196 | skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=match skip{false=>Some(sweep(&ctx,&holder_key)),true=>No |
| r6 | 86e2a6b | 27448 | 1711 | 0.51212 | skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=(if skip{Ok(0)}else{sweep(&ctx,&holder_key)}).map(\|v\|v |
| r7 | 86e2a6b | 26816 | 1570 | 0.47554 | skip-polarity sweep gate keeping the ? after the join (IR order: sweep.exit then join): swept=if skip{None}else{Some(sweep(&ctx,&holder_key))}.unwrap_ |
| s1 | 86e2a6b | 27440 | 1777 | 0.53196 | sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): let r=if skip{Ok(0)}else{sweep(&ctx,&holder_key)};if let  |
| s2 | 86e2a6b | 27440 | 1777 | 0.53196 | sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): let r=if !skip{sweep(&ctx,&holder_key)}else{Ok(0)};if let |
| s3 | 86e2a6b | 27440 | 1777 | 0.53196 | sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): swept=if skip{0}else{let r=sweep(&ctx,&holder_key);if let |
| s4 | 86e2a6b | 27440 | 1777 | 0.53196 | sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): swept=if skip{0}else{match sweep(&ctx,&holder_key){Err(e) |
| s5 | 86e2a6b | 27440 | 1777 | 0.53196 | sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): swept=if skip{0}else{let r=sweep(&ctx,&holder_key);if r.i |
| s6 | 86e2a6b | 27400 | 2249 | 0.67376 | = main bytes; sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): let r=(!skip).then(\|\|sweep(&ctx,&holder_key)).transpose |
| s7 | 86e2a6b | 26920 | 1543 | 0.46644 | sweep gate with an if-let Err early return (RPO puts the continuation before the Err block): let r=if skip{None}else{Some(sweep(&ctx,&holder_key))};if |
