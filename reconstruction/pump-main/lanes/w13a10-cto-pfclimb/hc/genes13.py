# Lane w13a10-cto-pfclimb gene library over main 3912c47ac admin_cto.rs (base_3912c47.rs).
# Each gene: list of exact (old, new) substitutions with equal newline counts (error-site lines fixed).
import runpy
_SV = runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w12a07-cto-sweepthread/tools/variants.py')['V']
GENES = {}
# w12a07-cto-sweepthread genes (skip flag in the sharing tree, vsigner hoist, and its size companions)
for k in ['vsig','vsigs','vsiglit','destscope','gate_if','gate_mut','rentlocal','frozenfirst','skiptree','skiptree_p3',
          'skiptree_if','amtne','amt0first','tokamtne','ammif','destrev','minvar','tokzero','vs_inline','bumpold','dborrow','oborrow','shborrow']:
    GENES['s7_' + k] = _SV[k]
# w12a14-cto-hillclimb gene library (genes that still apply to main 3912c47 keep their names)
import importlib.util as _iu
_spec = _iu.spec_from_file_location('g12', '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a10-cto-pfclimb/hc/genes12.py')
_m = _iu.module_from_spec(_spec); _spec.loader.exec_module(_m)
for _k, _v in _m.GENES.items():
    GENES.setdefault(_k, _v)
# --- w13a10 new genes (apply on top of s7_skiptree,s7_vsig) ---
_GS = "swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"
GENES['n_gate_ifskip'] = [(_GS, "swept=if skip{0}else{sweep(&ctx,&holder_key)?};")]
GENES['n_gate_matchskip'] = [(_GS, "swept=match skip{true=>0,false=>sweep(&ctx,&holder_key)?};")]
GENES['n_gate_mapor'] = [(_GS, "swept=if !skip{sweep(&ctx,&holder_key)}else{Ok(0)}?;")]
_VS = "let vsigner:&[&[&[u8]];1]=&[vaultseeds];"
GENES['n_vsig_infer'] = [(_VS, "let vsigner=&[vaultseeds];")]
GENES['n_vsig_arr'] = [(_VS, "let vsigner:[&[&[u8]];1]=[vaultseeds];"), ("amount,vsigner).map(|()|amount)", "amount,&vsigner).map(|()|amount)"), ("amount,vsigner)?;}", "amount,&vsigner)?;}")]
GENES['n_swept_let'] = [(" let swept;\n", "\n"), (_GS, "let " + _GS)]
GENES['n_sweep_hk_val'] = [("fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{", "fn sweep(ctx:&Context<AdminCto>,holder_key:Pubkey)->Result<u64>{"), ("sweep(&ctx,&holder_key)", "sweep(&ctx,holder_key)")]
GENES['n_skip_shared_or'] = [("(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)", "(None,!st.holder_reward&&st.creator!=Pubkey::default(),!shared)")]
GENES['n_gate_mapor_rev'] = [(_GS, "swept=if skip{Ok(0)}else{sweep(&ctx,&holder_key)}?;")]
GENES['n_gate_mapor_match'] = [(_GS, "swept=match skip{false=>sweep(&ctx,&holder_key),true=>Ok(0)}?;")]
GENES['n_gate_mapor_matchrev'] = [(_GS, "swept=match skip{true=>Ok(0),false=>sweep(&ctx,&holder_key)}?;")]
GENES['n_gate_mapor_let'] = [(_GS, "let r=if !skip{sweep(&ctx,&holder_key)}else{Ok(0)};swept=r?;")]
# --- relative to main 085e5df (w13a11 #2885: skip + vsigner + bump-first + reset early) ---
GENES['r_reset_revert'] = [(" let reset=sharing_update.is_some();let signer_seeds", " let signer_seeds"), ("sharing_config_reset:reset,", "sharing_config_reset:sharing_update.is_some(),")]
# --- relative to main 4394685 (skip + vsigner + Result gate + rent ref + curve cashback in event) ---
_R = "if native{let rent=&Rent::get()?;let min=rent.minimum_balance(0);"
GENES['m_rent_val'] = [(_R, "if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);")]
GENES['m_rent_inline'] = [(_R, "if native{let min=Rent::get()?.minimum_balance(0);")]
GENES['m_rent_min_ref'] = [(_R, "if native{let rent=&Rent::get()?;let min=&rent.minimum_balance(0);"), ("saturating_sub(min);", "saturating_sub(*min);")]
_EV = "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:holder,is_cashback_coin:a.bonding_curve.is_cashback_coin,"
GENES['m_ev_cb_local'] = [(_EV, "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:holder,is_cashback_coin:cashback,")]
GENES['m_ev_hr_curve'] = [(_EV, "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,")]
GENES['m_ev_nc_target'] = [(_EV, "old_creator,new_creator:target,is_holder_reward:holder,is_cashback_coin:a.bonding_curve.is_cashback_coin,")]
GENES['m_oldbump'] = [("let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();", "let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];")]
_T = "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
GENES['m_tree_p3'] = [(_T, "let (skip,collect_old,sharing_update)=if shared{if holder{(false,false,Some(None))}else{target=st.creator;(true,false,Some(new))}}else{(true,!st.holder_reward&&st.creator!=Pubkey::default(),None)};")]
GENES['m_tree_skipfirst'] = [(_T, "let (skip,sharing_update,collect_old)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(true,Some(new),false)}}else{(true,None,!st.holder_reward&&st.creator!=Pubkey::default())};")]
GENES['m_tree_holder'] = [(_T, "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};let holder=holder;")]
GENES['m_tree_unshared_first'] = [(_T, "let (sharing_update,collect_old,skip)=if !shared{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)}else if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)};")]
GENES['m_tree_match'] = [(_T, "let (sharing_update,collect_old,skip)=match (shared,holder){(true,true)=>(Some(None),false,false),(true,false)=>{target=st.creator;(Some(new),false,true)}(false,_)=>(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};")]
GENES['m_tree_co_and'] = [(_T, _T.replace("!st.holder_reward&&st.creator!=Pubkey::default()", "!st.holder_reward&st.creator!=Pubkey::default()"))]
GENES['m_tree_co_rev'] = [(_T, _T.replace("!st.holder_reward&&st.creator!=Pubkey::default()", "st.creator!=Pubkey::default()&&!st.holder_reward"))]
GENES['m_ev_hrc_cbl'] = [(_EV, "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:cashback,")]
GENES['m_ev_hr_curve_cbfirst'] = [(_EV, "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,")]
# --- w13a03-cto-entrycopy structural genes (entry copy of `new`): 0.50569 at 27,432 B on 4394685 ---
_g = {}; exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a03-cto-entrycopy/e/g8.py').read(), _g); GENES['x_g8'] = _g['EDITS']
_g = {}; exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a03-cto-entrycopy/e/s1.py').read(), _g); GENES['x_s1'] = _g['EDITS']
import json as _json
GENES['x_to085'] = [tuple(p) for p in _json.load(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a10-cto-pfclimb/hc/x_to085.json'))]
for _k,_v in _json.load(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a10-cto-pfclimb/hc/x_lines085.json')).items():
    GENES['x85_'+_k] = [tuple(p) for p in _v]
GENES['P'] = GENES['x85_L339'] + GENES['x85_L647'] + GENES['x85_L663'] + GENES['x85_L745'] + GENES['x85_L767'] + GENES['x_g8']
# --- P-relative genes (P = 085e5df text + w13a03 g8 entry copy, 0.50569 at 27,432 B) ---
_PT = "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
GENES['p_co_rev'] = [(_PT, _PT.replace("!st.holder_reward&&st.creator!=Pubkey::default()", "st.creator!=Pubkey::default()&&!st.holder_reward"))]
GENES['p_co_and'] = [(_PT, _PT.replace("!st.holder_reward&&st.creator!=Pubkey::default()", "!st.holder_reward&st.creator!=Pubkey::default()"))]
GENES['p_tree_unshared_first'] = [(_PT, "let (sharing_update,collect_old,skip)=if !shared{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)}else if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)};")]
GENES['p_tree_skipfirst'] = [(_PT, "let (skip,sharing_update,collect_old)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(true,Some(args.0),false)}}else{(true,None,!st.holder_reward&&st.creator!=Pubkey::default())};")]
_PA = "let args=&(new,);"
GENES['p_args_val'] = [(_PA, "let args=(new,);")]
GENES['p_args_newref'] = [(_PA, "let args=&new;  "), ("(Some(args.0),false,true)", "(Some(*args),false,true)")]
GENES['p_args_arr'] = [(_PA, "let args=&[new];"), ("(Some(args.0),false,true)", "(Some(args[0]),false,true)")]
GENES['p_args_before_st'] = [("let st=CtoState{", "let args=&(new,);let st=CtoState{"), ("fee_configurable:a.global.creator_fee_configurable};let args=&(new,);", "fee_configurable:a.global.creator_fee_configurable};")]
_PE = "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:holder,is_cashback_coin:cashback,"
GENES['p_ev_hr_curve'] = [(_PE, "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:cashback,")]
GENES['p_ev_cb_curve'] = [(_PE, "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:holder,is_cashback_coin:a.bonding_curve.is_cashback_coin,")]
GENES['p_ev_both_curve'] = [(_PE, "old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,")]
GENES['p_reset_inline'] = [(" let reset=sharing_update.is_some();let signer_seeds", " let signer_seeds"), ("sharing_config_reset:reset,", "sharing_config_reset:sharing_update.is_some(),")]
GENES['p_cb_rev'] = [("let cashback=!holder&&st.cashback;let mut target=validate", "let cashback=st.cashback&&!holder;let mut target=validate")]
GENES['p_cb_bitand'] = [("let cashback=!holder&&st.cashback;let mut target=validate", "let cashback=!holder&st.cashback;let mut target=validate")]
GENES['q_curve_order'] = [("  curve.is_cashback_coin=cashback;let old_fee=curve.creator_fee_bps;\n  curve.is_holder_reward=holder;\n", "  let old_fee=curve.creator_fee_bps;curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n")]
# --- W-relative (W = P,hk_after_shared,p_ev_both_curve = main ea78c08f1) ---
_WT = "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)}"
GENES['w_h4'] = [(_WT, "let (sharing_update,collect_old,skip,holder)=if shared{if holder{(Some(None),false,false,true)}else{target=st.creator;(Some(args.0),false,true,false)}}else if holder{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true,true)}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true,false)};(holder,cashback,target,sharing_update,collect_old,skip)}")]
GENES['w_h3'] = [(_WT, "let (sharing_update,collect_old,skip,holder)=if shared{if holder{(Some(None),false,false,true)}else{target=st.creator;(Some(args.0),false,true,false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true,holder)};(holder,cashback,target,sharing_update,collect_old,skip)}")]
GENES['w_h4b'] = [(_WT, "let (holder,sharing_update,collect_old,skip)=if shared{if holder{(true,Some(None),false,false)}else{target=st.creator;(false,Some(args.0),false,true)}}else if holder{(true,None,!st.holder_reward&&st.creator!=Pubkey::default(),true)}else{(false,None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)}")]
GENES['w_h4c'] = [(_WT, "let (sharing_update,collect_old,skip,holder)=if shared{if holder{(Some(None),false,false,true)}else{target=st.creator;(Some(args.0),false,true,false)}}else{if holder{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true,true)}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true,false)}};(holder,cashback,target,sharing_update,collect_old,skip)}")]
GENES['w_h4_co'] = [(_WT, "let (sharing_update,collect_old,skip,holder)=if shared{if holder{(Some(None),false,false,true)}else{target=st.creator;(Some(args.0),false,true,false)}}else{let co=!st.holder_reward&&st.creator!=Pubkey::default();if holder{(None,co,true,true)}else{(None,co,true,false)}};(holder,cashback,target,sharing_update,collect_old,skip)}")]
_WE = "is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,"
GENES['w_ev_hr_only'] = [(_WE, "is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:cashback,")]
GENES['w_ev_cb_only'] = [(_WE, "is_holder_reward:holder,is_cashback_coin:a.bonding_curve.is_cashback_coin,")]
GENES['w_ev_locals'] = [(_WE, "is_holder_reward:holder,is_cashback_coin:cashback,")]
# --- w13a08-cto-sweepphi v6 genes (hrb = pool CPI holder from the curve, perms of the sharing tree tuple) ---
_V6 = runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a08-cto-sweepphi/tools/v6.py')['V']
for _k in ['ob','hrb','reslate','rlref','gif','hkfirst','fu','hr2','ofirst','hrbc','p3','novsig','evcf','ofirst2'] + [k for k in _V6 if k.startswith('perm_')]:
    GENES['v6_' + _k] = _V6[_k]
GENES['q_pool_tgt_curve'] = [("signer_seeds),target,holder,fee)?;", "signer_seeds),a.bonding_curve.creator,holder,fee)?;")]
GENES['q_pool_both_curve'] = [("signer_seeds),target,holder,fee)?;", "signer_seeds),a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee)?;")]
GENES['q_pool_hr_curve_tgtcopy'] = [("signer_seeds),target,holder,fee)?;", "signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;")]
# --- relative to main 1043a51 (shared as if-expr) ---
_SH = "let shared=if a.bonding_curve.creator==a.sharing_config.key(){a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};"
GENES['z_sh_if_owner_first'] = [(_SH, "let shared=if a.sharing_config.owner==&FEES{a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty()}else{false};")]
GENES['z_sh_flat_owner_first'] = [(_SH, "let shared=a.sharing_config.owner==&FEES&&a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty();")]
GENES['z_sh_flat'] = [(_SH, "let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();")]
GENES['z_sh_if_borrow'] = [(_SH, "let shared=if a.bonding_curve.creator==*a.sharing_config.key{a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};")]
GENES['z_sh_if_nested'] = [(_SH, "let shared=if a.bonding_curve.creator==a.sharing_config.key(){if a.sharing_config.owner==&FEES{!a.sharing_config.data_is_empty()}else{false}}else{false};")]
GENES['z_sh_if_empty_first'] = [(_SH, "let shared=if a.bonding_curve.creator==a.sharing_config.key(){!a.sharing_config.data_is_empty()&&a.sharing_config.owner==&FEES}else{false};")]
GENES['z_sh_if_lhs'] = [(_SH, "let shared=if a.sharing_config.key()==a.bonding_curve.creator{a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};")]
GENES['z_sh_match'] = [(_SH, "let shared=match a.bonding_curve.creator==a.sharing_config.key(){true=>a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty(),false=>false};")]
GENES['z_sh_if_owner_deref'] = [(_SH, "let shared=if a.bonding_curve.creator==a.sharing_config.key(){*a.sharing_config.owner==FEES&&!a.sharing_config.data_is_empty()}else{false};")]
GENES['z_sfo_deref'] = [(_SH, "let shared=*a.sharing_config.owner==FEES&&a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty();")]
GENES['z_sfo_lhs'] = [(_SH, "let shared=a.sharing_config.owner==&FEES&&a.sharing_config.key()==a.bonding_curve.creator&&!a.sharing_config.data_is_empty();")]
GENES['z_sfo_ifkey'] = [(_SH, "let shared=a.sharing_config.owner==&FEES&&if a.bonding_curve.creator==a.sharing_config.key(){!a.sharing_config.data_is_empty()}else{false};")]
GENES['z_sfo_if'] = [(_SH, "let shared=if a.sharing_config.owner==&FEES&&a.bonding_curve.creator==a.sharing_config.key(){!a.sharing_config.data_is_empty()}else{false};")]
GENES['z_sfo_borrow'] = [(_SH, "let shared=a.sharing_config.owner==&FEES&&a.bonding_curve.creator==*a.sharing_config.key&&!a.sharing_config.data_is_empty();")]
