| gene | form | ratio | bytes | M | fM | rfjM | true-LCS rfj | eq main |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `none` | main 90300f9 | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `c1` | cashback mut local=false, assigned per tree arm (shared non-holder: st.cashback; non-shared: !holder&&st.cashback) | 0.56525 | 27264 | 1882 | 2044 | 2852 | 2995 (-12) | no |
| `s2` | sharing_update as third field of the tree tuple (co,skip,su) | 0.67266 | 27416 | 2246 | 2343 | 2810 | 3008 (+1) | no |
| `c2` | cashback deferred init, assigned in each tree arm | 0.56525 | 27264 | 1882 | 2044 | 2852 | 2995 (-12) | no |
| `k1` | skip as mut local (true) cleared in holder arm; tree returns collect_old only | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3006 (-1) | no |
| `c3` | cashback as a third field of the tree tuple (computed inside each arm) | 0.47889 | 27416 | 1599 | 1719 | 2174 | 2474 (-533) | no |
| `k2` | collect_old as mut local (false), non-shared arm assigns; tree returns skip only | 0.51182 | 27448 | 1710 | 1698 | 2197 | 2483 (-524) | no |
| `c4` | c1 with the assignment last in each arm | 0.56525 | 27264 | 1882 | 2044 | 2852 | 2995 (-12) | no |
| `k3` | collect_old deferred init per arm; tree returns skip | 0.51182 | 27448 | 1710 | 1698 | 2197 | 2483 (-524) | no |
| `c5` | cashback mut local=st.cashback, holder arm clears, non-shared arm masks with !holder | 0.56525 | 27264 | 1882 | 2044 | 2852 | 2995 (-12) | no |
| `k4` | skip deferred init per arm; tree returns collect_old | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3006 (-1) | no |
| `c6` | c2 with the non-shared arm as if holder{false}else{st.cashback} | 0.56525 | 27264 | 1882 | 2044 | 2852 | 2995 (-12) | no |
| `h1` | outer hop binds (mut target,..) directly instead of let mut target=target | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `t1` | target deferred: let vt=validate(..)?; let target; assigned per tree arm | 0.36328 | 27328 | 1211 | 2245 | 2867 | 3002 (-5) | no |
| `p1` | pargs bound inside the pool_updated arm | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `t2` | target as a third field of the tree tuple (non-holder shared arm = curve.creator) | 0.37504 | 27320 | 1250 | 2286 | 2855 | 2994 (-13) | no |
| `p2` | pargs deferred, assigned inside the pool_updated arm | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `t3` | let vt=validate()?; let mut target=vt; holder arm re-assigns target=vt | 0.36328 | 27328 | 1211 | 2245 | 2867 | 3002 (-5) | no |
| `p3` | pargs fields bound as separate locals first | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `s1` | sharing_update deferred init (no default), non-shared arm assigns None | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `p4` | pargs mut with field 1 assigned after | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `f1` | collect_old value computed before validate (let co=..) and used by the non-shared arm | 0.59421 | 27280 | 1979 | 2012 | 2843 | 2977 (-30) | no |
| `m3` | tree as if shared&&holder{..}else if shared{..}else{..} | 0.57215 | 27488 | 1913 | 2231 | 2813 | 3006 (-1) | no |
| `f2` | collect_old value computed after validate, before the tree | 0.43221 | 27448 | 1444 | 1549 | 2183 | 2466 (-541) | no |
| `m4` | tree as if !shared{..}else if !holder{..}else{..} | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `f3` | skip computed after the tree as !(shared&&holder); tree returns collect_old only | 0.56869 | 27448 | 1900 | 1985 | 2791 | 2989 (-18) | no |
| `o1` | outer Ok hop carries (target,sharing_update) only (cashback from the block) | 0.67346 | 27400 | 2248 | 2347 | 2809 | 3006 (-1) | no |
| `f4` | skip computed before validate as !(shared&&holder); tree returns collect_old only | 0.46835 | 27320 | 1561 | 1609 | 2185 | 2483 (-524) | no |
| `o2` | outer Ok hop carries (sharing_update,cashback) only (target from the block) | 0.66437 | 27384 | 2217 | 2345 | 2811 | 3006 (-1) | no |
| `o3` | outer Ok hop also carries skip | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `f6` | curve creator bound before validate, used by the shared non-holder arm | 0.67125 | 27528 | 2246 | 2344 | 2817 | 3015 (+8) | no |
| `o4` | outer Ok hop also carries collect_old | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `f7` | curve creator bound after validate (before tree), used by the shared non-holder arm | 0.67265 | 27440 | 2247 | 2344 | 2810 | 3010 (+3) | no |
| `o5` | outer Ok hop field order (sharing_update,target,cashback) | 0.67196 | 27400 | 2243 | 2347 | 2810 | 3007 (+0) | no |
| `m1` | tree as match (shared,holder) | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `o6` | outer Ok hop field order (cashback,target,sharing_update) | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `m2` | tree as match shared{true=>if holder..,false=>..} | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `o7` | outer Ok hop field order (target,cashback,sharing_update) | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `o8` | outer Ok hop with an identity .map | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `vo1w3c` | vo1 (validate fills &mut Option<Option<Pubkey>> out-param per arm) + mut target outside the block: frame-permutation search for vo1's L1 gap | overlap / compile fail | | | | | | |
| `f5` | sharing_update payload Some(args.0) computed before validate | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `vo1o1` | vo1 (validate fills &mut Option<Option<Pubkey>> out-param per arm) + hop without cashback: frame-permutation search for vo1's L1 gap | 0.52086 | 27288 | 1735 | 2187 | 2802 | 2988 (-19) | no |
| `vo1m4` | vo1 (validate fills &mut Option<Option<Pubkey>> out-param per arm) + !shared-first tree: frame-permutation search for vo1's L1 gap | overlap / compile fail | | | | | | |
| `vo1` | vo1 re-priced on 90300f9 (validate fills &mut sharing_update out-param per arm) | 0.52086 | 27288 | 1735 | 2187 | 2803 | 2989 (-18) | no |
| `vo1co5` | vo1c (su declared before the 6-tuple block) + hop order (su,target,cb) | 0.55149 | 27288 | 1837 | 2187 | 2803 | 2989 (-18) | no |
| `vo1o5` | vo1 (validate fills &mut Option<Option<Pubkey>> out-param per arm) + (su,target,cb): frame-permutation search for vo1's L1 gap | 0.52086 | 27288 | 1735 | 2187 | 2803 | 2989 (-18) | no |
| `vo1co7` | vo1c + hop order (target,cb,su) | 0.55299 | 27288 | 1842 | 2187 | 2803 | 2989 (-18) | no |
| `vo1o6` | vo1 (validate fills &mut Option<Option<Pubkey>> out-param per arm) + (cb,target,su): frame-permutation search for vo1's L1 gap | 0.52086 | 27288 | 1735 | 2187 | 2803 | 2989 (-18) | no |
| `vo1do6` | vo1d (su local copied to sharing_update) + hop order (cb,target,su) | 0.53295 | 27280 | 1775 | 2209 | 2777 | 2992 (-15) | no |
| `vo1o7` | vo1 (validate fills &mut Option<Option<Pubkey>> out-param per arm) + (target,cb,su): frame-permutation search for vo1's L1 gap | 0.52086 | 27288 | 1735 | 2187 | 2803 | 2989 (-18) | no |
| `vo1k1` | vo1 (validate fills &mut Option<Option<Pubkey>> out-param per arm) + skip mut local: frame-permutation search for vo1's L1 gap | overlap / compile fail | | | | | | |
| `q5` | 6-tuple order: skip before collect_old | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `q1` | inner block tuple without the unused _holder field | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `q6` | 6-tuple order: sharing_update before target | 0.67316 | 27400 | 2247 | 2346 | 2810 | 3007 (+0) | no |
| `q2` | 6-tuple order (target,su,cb,_holder,co,skip) | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `q7` | 6-tuple order (_holder,co,skip,cb,target,su) | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `q3` | 6-tuple order (co,skip,_holder,cb,target,su) | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `q8` | 6-tuple fully reversed | 0.67316 | 27400 | 2247 | 2346 | 2810 | 3007 (+0) | no |
| `q4` | 6-tuple order (_holder,target,su,cb,co,skip) | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `k1o1` | k1 + o1 | 0.67346 | 27400 | 2248 | 2347 | 2809 | 3005 (-2) | no |
| `k4o1` | k4 + o1 | 0.67346 | 27400 | 2248 | 2347 | 2809 | 3005 (-2) | no |
| `k4f7` | k4 + f7 | overlap / compile fail | | | | | | |
| `k1q6` | k1 + q6 | 0.67316 | 27400 | 2247 | 2346 | 2810 | 3006 (-1) | no |
| `A5` | main target + cashback deferred per arm (c2 on main tree) | 0.56525 | 27264 | 1882 | 2044 | 2852 | 2995 (-12) | no |
| `A1` | all fields per arm: let vt=validate()?; target, cashback deferred and assigned in each tree arm (su mut None) | 0.37367 | 27344 | 1246 | 2071 | 2862 | 2997 (-10) | no |
| `A6` | A1 with the !shared-first tree (m4 order) | 0.37367 | 27344 | 1246 | 2071 | 2862 | 2997 (-10) | no |
| `A2` | A1 with sharing_update deferred too | 0.37367 | 27344 | 1246 | 2071 | 2862 | 2997 (-10) | no |
| `A7` | t1 + c2 (target and cashback deferred per arm) | 0.37367 | 27344 | 1246 | 2071 | 2862 | 2997 (-10) | no |
| `A3` | A2 with collect_old/skip deferred too (no tree tuple at all) | 0.37562 | 27408 | 1254 | 2079 | 2867 | 2998 (-9) | no |
| `A4` | A1, non-shared cashback as if holder{false}else{st.cashback} | 0.37367 | 27344 | 1246 | 2071 | 2862 | 2997 (-10) | no |
| `g1` | let creator=st.creator; bound before validate, used by the shared non-holder arm | 0.67255 | 27520 | 2250 | 2344 | 2820 | 3014 (+7) | no |
| `g6` | creator bound between sk and validate | 0.67125 | 27528 | 2246 | 2344 | 2817 | 3015 (+8) | no |
| `g2` | creator bound before let hopt | 0.66806 | 27496 | 2234 | 2343 | 2817 | 3015 (+8) | no |
| `g7` | creator bound before let cashback | 0.66806 | 27496 | 2234 | 2343 | 2817 | 3015 (+8) | no |
| `g3` | creator bound at the start of the state block (before let st) | 0.67235 | 27464 | 2247 | 2344 | 2810 | 3010 (+3) | no |
| `g9` | creator carried as args.1 (args=&(new,creator)) | 0.66806 | 27496 | 2234 | 2343 | 2817 | 3015 (+8) | no |
| `g4` | creator bound by reference before validate (&a.bonding_curve.creator) | 0.67346 | 27400 | 2248 | 2347 | 2810 | 3007 (+0) | yes |
| `g10` | g6 + dummy use in the non-shared arm (screen only, not landable) | 0.67125 | 27528 | 2246 | 2344 | 2817 | 3015 (+8) | no |
| `g5` | creator bound before st and moved into CtoState{creator,..} | 0.61649 | 27560 | 2064 | 2257 | 2808 | 3013 (+6) | no |
| `Ksa` | size knob sh_accs_let alone | 0.636 | 27376 | 2122 | 2202 | 2847 | 2982 (-25) | no |
| `Kdb` | size knob s_dest_borrow (-80 B) alone on main | 0.67027 | 27320 | 2234 | 2333 | 2800 | 2997 (-10) | no |
| `Ksp` | size knob sh_prog_let alone | 0.67056 | 27368 | 2237 | 2332 | 2790 | 2999 (-8) | no |
| `Kob` | size knob s_old_borrow alone | 0.66067 | 27320 | 2202 | 2328 | 2800 | 2997 (-10) | no |
| `Kers` | size knob ev_reset_shared alone | 0.59081 | 27288 | 1968 | 2164 | 2804 | 2988 (-19) | no |
| `Kct` | size knob cu_typed alone | 0.67026 | 27368 | 2236 | 2333 | 2801 | 2998 (-9) | no |
| `Kfr` | size knob cu_fee_replace alone | 0.66906 | 27392 | 2233 | 2330 | 2798 | 2997 (-10) | no |
| `X2` | g3 + cu_typed + sh_prog_let (pinned 27400) | 0.66717 | 27400 | 2227 | 2317 | 2781 | 2993 (-14) | no |
| `X1` | g1 + s_dest_borrow + cu_typed + cu_fee_replace (size repay) | 0.66637 | 27416 | 2225 | 2317 | 2796 | 2993 (-14) | no |
| `X4` | g1 + s_dest_borrow + sh_prog_let + cu_fee_replace (pinned 27400) | 0.66477 | 27400 | 2219 | 2308 | 2778 | 2986 (-21) | no |
| `X3` | f7 + cu_typed + cu_fee_replace | 0.66876 | 27416 | 2233 | 2327 | 2796 | 2999 (-8) | no |
| `c1g1` | c1 (per-arm cashback) + g1 (creator early) | 0.56338 | 27384 | 1880 | 2040 | 2860 | 3005 (-2) | no |
| `c1g3` | c1 + g3 | 0.5627 | 27392 | 1878 | 2040 | 2855 | 3003 (-4) | no |
| `c1f6` | c1 + f6 | 0.56479 | 27392 | 1885 | 2046 | 2863 | 3006 (-1) | no |
| `c1f7` | c1 + f7 | 0.56504 | 27312 | 1883 | 2043 | 2856 | 2999 (-8) | no |
