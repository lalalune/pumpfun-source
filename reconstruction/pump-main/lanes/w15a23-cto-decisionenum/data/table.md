| variant | ratio | bytes | norm losses | LCS --- | LCS -fj | LCS rfj | form |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| main 9120883 | 0.67376 | 27,400 | 0 | 2255 | 2599 | 3007 | - |
| d1a | 0.32491 | 27,520 | 0 |  |  |  |  |
| d1b | 0.35049 | 28,104 | 0 |  |  |  |  |
| d1b_cm | 0.35049 | 28,104 | 0 |  |  |  |  |
| d1b_rm | 0.35049 | 28,104 | 0 |  |  |  |  |
| d1b_sif | 0.35049 | 28,104 | 0 |  |  |  |  |
| d1c | 0.40831 | 27,520 | 0 |  |  |  |  |
| d1d | 0.35049 | 28,104 | 0 |  |  |  |  |
| d4 | 0.23987 | 28,104 | 0 |  |  |  |  |
| d4_hr | 0.22653 | 28,112 | 0 |  |  |  |  |
| d5 | 0.55744 | 27,408 | 0 | 1961 | 2387 | 2795 |  |
| d5m | 0.55744 | 27,408 | 0 |  |  |  |  |
| d6a | 0.31295 | 27,368 | 0 |  |  |  |  |
| d6b | 0.36759 | 27,400 | 0 | 1408 | 1819 | 2220 |  |
| d6b_rs | 0.30915 | 27,352 | 0 |  |  |  |  |
| d7 | 0.18807 | 29,248 | 1 | 848 | 1938 | 2459 | payload-less Tail{Sweep,Neither,Collect}; ONE match dispatch at the sweep site: swept=match tail{Collect=>{wallet()?;0}Sweep=>sweep()?,Neither=>0} |
| d7b | 0.18807 | 29,248 | 1 | 848 | 1938 | 2459 | d7 with Sweep arm first |
| d7c | 0.18807 | 29,248 | 1 | 848 | 1938 | 2459 | d7 with Neither arm first |
| d8 | 0.44586 | 29,312 | 1 | 1617 | 2132 | 2870 | 2-variant Next{Shared(Option<Pubkey>),Unshared{collect}} whose tag values {0,1,2} equal the original 0x8f8 sharing tag; sweep=matches!(Shared(None)), collect fr |
| d9 | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | isomorphic enum Sharing{Reset(Option<Pubkey>),Keep} replacing Option<Option<Pubkey>> (match Reset(val)=>CPI, Keep=>{}; reset=matches!(Reset(_))) |
| h1 | 0.3711 | 27,368 | 0 | 1460 | 2532 | 2990 | validate returns Result<Creator>, enum Creator{Holder,New(Pubkey)} (validate-exit tag); execute: holder=matches!(c,Holder), cashback=!holder&&st.cashback after  |
| h1b | 0.36745 | 27,376 | 0 | 1527 | 2517 | 2969 | h1 with (holder,target)=match validate()?{Holder=>(true,holder_key),New(t)=>(false,t)} |
| h1n | 0.37601 | 27,352 | 0 | 1478 | 2548 | 2992 | h1 with variant order Creator{New(Pubkey),Holder} |
| h2 | 0.3169 | 27,208 | 0 | 1322 | 2224 | 2926 | h1 with curve.is_holder_reward=holder.unwrap_or(false) kept |
| h3 | 0.3705 | 27,368 | 0 | 1459 | 2531 | 2991 | h1 with Result<Option<Pubkey>> (None=holder), target=c.unwrap_or(holder_key) |
| h4 | 0.36715 | 27,376 | 0 | 1454 | 2517 | 2969 | h1 with (holder,cashback,target)=match c{Holder=>(true,false,holder_key),New(t)=>(false,st.cashback,t)} |
| h4b | 0.30458 | 27,416 | 0 | 1284 | 2204 | 2909 | h4 with curve holder store from the argument |
| h5 | 0.33933 | 27,368 | 0 | 1395 | 2470 | 2983 | enum Creator{Holder(Pubkey),New(Pubkey)} (both carry the key) from validate; holder=matches!(Holder(_)); target=match c{Holder(k)/New(k)=>k} |
| h5b | 0.35699 | 27,416 | 0 | 1464 | 2446 | 2966 | h5 with (holder,target)=match validate()?{Holder(k)=>(true,k),New(k)=>(false,k)} |
| h5c | 0.36492 | 27,352 | 0 | 1392 | 2257 | 2971 | h5b with curve holder store from the argument |
| h6 | 0.34263 | 27,320 | 0 | 1405 | 2503 | 2993 | (reference) validate returns Result<(Pubkey,bool)> (w13a38-like) on current main |
| k1 | 0.56722 | 27,248 | 0 | 1924 | 2316 | 2983 | enum Kind{Holder,Wallet{cashback:bool}} replaces the cashback bool at its head position (before validate); curve holder/cashback stores from matches!(Kind) |
| k1b | 0.56298 | 27,280 | 0 | 1912 | 2299 | 2985 | k1 with the holder store kept from the argument |
| k1c | 0.56298 | 27,280 | 0 | 1912 | 2299 | 2985 | k1b with cashback store match Kind{Wallet{cashback}=>cashback,Holder=>false} |
| k1d | 0.56722 | 27,248 | 0 | 1924 | 2316 | 2983 | k1c + holder store matches!(Holder) |
| k2 | 0.53227 | 27,288 | 0 | 1943 | 2413 | 2986 | Kind built right after validate (validate-exit position) in the shared tree; both curve stores from Kind |
| k2b | 0.53529 | 27,376 | 0 | 1839 | 2274 | 2989 | k2 with holder store from the argument |
| k3 | 0.56298 | 27,280 | 0 | 1912 | 2299 | 2985 | Option<bool> sum type at the head (None=holder, Some(st.cashback)); cashback store cashback==Some(true) |
| k3b | 0.56722 | 27,248 | 0 | 1924 | 2316 | 2983 | k3 + holder store cashback.is_none(), cashback store unwrap_or(false) |
| mil | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | (reference) if let Some(val)=sharing_update{..} (w15a20 m_il) == d9 bytes |
| v1 | 0.37036 | 27,648 | 0 | 1410 | 1824 | 2229 | validate(..,shared)->Result<(Pubkey,Next)> with Next{Holder,Shared,Wallet{collect}} built at validate Ok; later uses from match/matches! |
| v2 | 0.22518 | 27,424 | 0 | 1005 | 1815 | 2210 | as v1 with next built by an if-tree before Ok((target,next)) (target=st.creator in Shared arm) |
| mk_L_fee_unwrap_again | 0.66926 | 27,400 | 0 | 2241 | 2587 | 3003 | mil + knob L_fee_unwrap_again |
| mk_cu_fee_oldunwrap | 0.66926 | 27,400 | 0 | 2241 | 2587 | 3003 | mil + knob cu_fee_oldunwrap |
| mk_cu_fee_replace | 0.66946 | 27,384 | 0 | 2240 | 2591 | 2997 | mil + knob cu_fee_replace |
| mk_cu_replace | 0.67206 | 27,392 | 0 | 2249 | 2598 | 3005 | mil + knob cu_replace |
| mk_cu_typed | 0.67036 | 27,360 | 0 | 2242 | 2590 | 2998 | mil + knob cu_typed |
| mk_ev_auth_deref | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob ev_auth_deref |
| mk_ev_cb_local | 0.66557 | 27,384 | 0 | 2231 | 2595 | 3006 | mil + knob ev_cb_local |
| mk_ev_mint_key | 0.66467 | 27,408 | 0 | 2225 | 2578 | 2992 | mil + knob ev_mint_key |
| mk_ev_nc_target | 0.38779 | 27,464 | 0 | 1534 | 2559 | 2976 | mil + knob ev_nc_target |
| mk_ev_reset_shared | 0.5915 | 27,280 | 0 | 2045 | 2463 | 2988 | mil + knob ev_reset_shared |
| mk_ev_ts_clockvar | 0.66936 | 27,392 | 0 | 2240 | 2601 | 3007 | mil + knob ev_ts_clockvar |
| mk_ev_ts_map | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob ev_ts_map |
| mk_g_canedit_first | 0.67176 | 27,392 | 0 | 2248 | 2597 | 3004 | mil + knob g_canedit_first |
| mk_g_fee_unwrap | 0.66926 | 27,400 | 0 | 2241 | 2587 | 3003 | mil + knob g_fee_unwrap |
| mk_g_old_fee_first | 0.67206 | 27,392 | 0 | 2249 | 2598 | 3005 | mil + knob g_old_fee_first |
| mk_g_s7_destrev | 0.67176 | 27,392 | 0 | 2248 | 2600 | 3007 | mil + knob g_s7_destrev |
| mk_g_s7_destscope | 0.53234 | 27,432 | 0 | 1832 | 2217 | 2616 | mil + knob g_s7_destscope |
| mk_g_s7_tokamtne | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob g_s7_tokamtne |
| mk_g_s7_tokzero | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob g_s7_tokzero |
| mk_g_w_clock_local | 0.67126 | 27,408 | 0 | 2247 | 2599 | 3006 | mil + knob g_w_clock_local |
| mk_pool_prog_let | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob pool_prog_let |
| mk_prep_match | 0.66667 | 27,392 | 0 | 2231 | 2581 | 2989 | mil + knob prep_match |
| mk_pu_match | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob pu_match |
| mk_rent_checked | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob rent_checked |
| mk_sh_accs_let | 0.63609 | 27,368 | 0 | 2140 | 2461 | 2982 | mil + knob sh_accs_let |
| mk_sh_fees_key | 0.67196 | 27,392 | 0 | 2249 | 2599 | 3006 | mil + knob sh_fees_key |
| mk_sh_prog_let | 0.67066 | 27,360 | 0 | 2243 | 2592 | 2999 | mil + knob sh_prog_let |
| mk_sig_arr | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob sig_arr |
| mk_sig_mint_acct | 0.50786 | 27,456 | 0 | 1733 | 2018 | 2485 | mil + knob sig_mint_acct |
| mk_w_ev_creator_first | 0.66736 | 27,456 | 0 | 2236 | 2588 | 3001 | mil + knob w_ev_creator_first |
| mk_wl_cr_deref | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob wl_cr_deref |
| mk_wl_ts_clockvar | 0.67126 | 27,408 | 0 | 2247 | 2599 | 3006 | mil + knob wl_ts_clockvar |
| mk_wl_ts_map | 0.67236 | 27,392 | 0 | 2250 | 2600 | 3007 | mil + knob wl_ts_map |
