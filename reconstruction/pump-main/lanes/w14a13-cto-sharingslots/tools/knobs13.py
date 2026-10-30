# tail knobs adapted to main cef0574 (semantics-preserving; newline count kept)
import json
K={}
PU="let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"
K['pu_amm_keyfn']=[(PU,"let pool_updated=!a.pool.data_is_empty() && *a.pool.owner==a.pump_amm.key();")]
K['pu_amm_key']=[(PU,"let pool_updated=!a.pool.data_is_empty() && a.pool.owner==a.pump_amm.key;")]
EVA="authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),"
K['ev_mint_key']=[(EVA,"authority:a.admin_set_creator_authority.key(),mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),")]
K['ev_auth_deref']=[(EVA,"authority:*a.admin_set_creator_authority.key,mint,bonding_curve:a.bonding_curve.key(),")]
K['ev_cb_local']=[("is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_cashback_coin:cashback,")]
K['ev_nc_target']=[("new_creator:a.bonding_curve.creator,","new_creator:target,")]
K['ev_hr_local']=[("is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback","is_holder_reward:holder,is_cashback")]
K['ev_nf_inline']=[("new_creator_fee_bps:nf,","new_creator_fee_bps:a.bonding_curve.creator_fee_bps,")]
K['ev_nf_unwrap']=[("new_creator_fee_bps:nf,","new_creator_fee_bps:fee.unwrap_or(old_fee),")]
EVT="let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,"
K['ev_ts_clockvar']=[(EVT,"let clock=Clock::get()?;let e=AdminCtoEvent{timestamp:clock.unix_timestamp,")]
K['ev_ts_map']=[(EVT,"let e=AdminCtoEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,")]
K['ev_ts_prepool']=[(EVT,"let e=AdminCtoEvent{timestamp:ts,"),(PU,"let ts=Clock::get()?.unix_timestamp;"+PU)]
K['pargs_hr_local']=[("let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(target,holder,fee);")]
K['pargs_tgt_curve']=[("let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee);")]
K['cu_fee_oldunwrap']=[("if let Some(f)=fee{curve.creator_fee_bps=f;}","curve.creator_fee_bps=fee.unwrap_or(old_fee);")]
K['cu_fee_unwrapcur']=[("if let Some(f)=fee{curve.creator_fee_bps=f;}","curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);")]
K['pu_msg_first']=[]  # placeholder
del K['pu_msg_first']
if __name__=='__main__': print(json.dumps(list(K)))
