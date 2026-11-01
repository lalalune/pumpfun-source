# w16a16 lholdpair genes (experiment only): head levers for the L-basin holder-piece pair, applied on top of 'Lv'
# (L_vol = mv_5_1+t1n+m_crl2+vol334_back). Each gene: exact single-occurrence (old,new) replacements; line count kept.
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_pt as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)
_LIT='CtoState{fee_configurable:a.global.creator_fee_configurable,cashback:a.bonding_curve.is_cashback_coin,creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,quote_locked,holder_enabled:a.global.is_holder_reward_enabled}'
_ST=' let st='+_LIT+';'
_HC='let hopt=holder;let holder=hopt==Some(true);'
_CB='let cashback=!holder&&st.cashback;'
_AR='let args=&(new,);'
_SK='let sk=a.sharing_config.key();'
_TAIL=_ST+_HC+_CB+_AR+_SK
def _seq(*parts): return [(_TAIL,''.join(parts))]
G['hb']=_seq(' '+_HC,'let st='+_LIT+';',_CB,_AR,_SK)
G['sk2']=_seq(_ST,_HC,_CB,_SK,_AR)
G['hc2']=_seq(_ST,'let hopt=holder;',_AR,'let holder=hopt==Some(true);',_CB,_SK)
G['ar1']=_seq(_ST,_AR,_HC,_CB,_SK)
G['cbl']=_seq(_ST,_HC,_AR,_SK,_CB)
G['sk1']=_seq(_ST,_SK,_HC,_CB,_AR)
G['arsk']=_seq(_ST,_AR,_SK,_HC,_CB)
# Global / bonding-curve bindings for the literal
_LG=_LIT.replace('a.global.','g.')
_LB=_LIT.replace('a.bonding_curve.','bc.')
_LGB=_LG.replace('a.bonding_curve.','bc.')
G['gb']=[(_ST,' let g=&a.global;let st='+_LG+';')]
G['bcb']=[(_ST,' let bc=&a.bonding_curve;let st='+_LB+';')]
G['gbcb']=[(_ST,' let g=&a.global;let bc=&a.bonding_curve;let st='+_LGB+';')]
# plain (non-#[inline]) constructor helper on the same line
G['sth']=[(_ST,' let st=cto_state(a,quote_locked);'),('struct CtoState{','fn cto_state(a:&AdminCto,quote_locked:bool)->CtoState{'+_LIT+'}struct CtoState{')]
G['sthg']=[(_ST,' let st=cto_state(&a.global,&a.bonding_curve,quote_locked);'),('struct CtoState{','fn cto_state(g:&Global,bc:&BondingCurve,quote_locked:bool)->CtoState{'+_LGB+'}struct CtoState{')]
# holder flag uses (entry-argument use count)
G['h1']=[('curve.is_holder_reward=holder.unwrap_or(false);','curve.is_holder_reward=_holder;')]
G['evh']=[('let e=AdminCtoEvent{is_holder_reward:a.bonding_curve.is_holder_reward,','let e=AdminCtoEvent{is_holder_reward:holder.unwrap_or(false),')]
G['xcba']=[(_CB,'let cashback=st.cashback&&!holder;')]
G['xhm']=[(_HC,'let hopt=holder;let holder=matches!(hopt,Some(true));')]
G['vhm']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=matches!(hopt,Some(true));')]
# ---- batch 2 ----
# shared non-holder arm reads the creator from st (bc data ptr no longer live across validate)
G['g0L']=[("else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}","else{sharing_update=Some(args.0);target=st.creator;(false,true)}}")]
# quote_locked evaluated inline in the literal, original head read order (cashback, holder_reward, mayhem before the quote test)
_QL='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
_QLE='quote_locked:{let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)}'
def _qlo(order):
    F={'fee_configurable':'fee_configurable:a.global.creator_fee_configurable','cashback':'cashback:a.bonding_curve.is_cashback_coin','creator':'creator:a.bonding_curve.creator','max_fee':'max_fee:a.global.max_configurable_creator_fee_bps','mayhem':'mayhem:a.bonding_curve.is_mayhem_mode','holder_reward':'holder_reward:a.bonding_curve.is_holder_reward','quote_locked':_QLE,'holder_enabled':'holder_enabled:a.global.is_holder_reward_enabled'}
    lit='CtoState{'+','.join(F[x] for x in order.split())+'}'
    return [(_QL,''),(_ST,' let st='+lit+';')]
G['qlo1']=_qlo('cashback holder_reward mayhem quote_locked max_fee holder_enabled fee_configurable creator')
G['qlo2']=_qlo('cashback holder_reward mayhem quote_locked creator max_fee holder_enabled fee_configurable')
G['qlo3']=_qlo('fee_configurable cashback creator max_fee mayhem holder_reward quote_locked holder_enabled')
G['qlo4']=_qlo('cashback holder_reward mayhem quote_locked fee_configurable creator max_fee holder_enabled')
# validate call-site spellings on the L_vol text
_CV='validate(&st,hopt,fee,new,&holder_key,&sk)?'
G['cvsk']=[(_SK+'let mut target='+_CV,'let mut target=validate(&st,hopt,fee,new,&holder_key,&a.sharing_config.key())?')]
G['cvhk']=[(_CV,'validate(&st,hopt,fee,new,&hk.0,&sk)?')]
G['cvar']=[(_CV,'validate(&st,hopt,fee,args.0,&holder_key,&sk)?')]
G['h1evh']=G['h1']+G['evh']
# ---- batch 3: late flag use counts (event reads the execute flags instead of re-reading the curve) ----
G['evcb']=[('is_cashback_coin:a.bonding_curve.is_cashback_coin,','is_cashback_coin:cashback,')]
G['evhb']=[('let e=AdminCtoEvent{is_holder_reward:a.bonding_curve.is_holder_reward,','let e=AdminCtoEvent{is_holder_reward:_holder,')]
G['evboth']=G['evcb']+G['evh']
G['hrv']=[(' if st.holder_reward&&!(hopt==Some(true)){',' if st.holder_reward&&!holder{')]
G['cbif2']=[(_CB,'let cashback=if !holder{st.cashback}else{false};')]
G['sutg']=[("else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}","else{sharing_update=Some(Some(target));target=a.bonding_curve.creator;(false,true)}}")]
