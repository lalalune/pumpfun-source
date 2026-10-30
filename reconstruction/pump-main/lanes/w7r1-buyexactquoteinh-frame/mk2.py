import sys
import os
OUT=os.path.expanduser(os.environ.get('OUT','~/.cache/pumpfun-reconstruction/lanes/w7r1-buyexactquoteinh-frame'))
COMPLETE="let a=&mut *ctx.accounts;if a.bonding_curve.real_token_reserves==0{a.bonding_curve.complete=true;let event=crate::trade_types::CompleteEvent{mint:a.base_mint.key(),user:a.user.key(),bonding_curve:a.bonding_curve.key(),quote_mint:a.bonding_curve.quote_mint,timestamp};emit!(event);emit_cpi!(event);}"
PREP="let a=&mut *ctx.accounts;crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;Ok(())"
S="ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,ev:TradeEvent,timestamp:i64"
SR="ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,ev:&TradeEvent,timestamp:i64"
def mk(name,caller,body,sig=S,attr="#[inline(always)]"):
    body=body.replace('COMPLETE',COMPLETE).replace('PREP',PREP)
    helper="\n"+attr+"\nfn cap_eq<'info>("+sig+")->Result<()>{\n"+body+"\n}\n"
    reps=[("  emit!(ev);emit_cpi!(ev);\n  complete_and_prepare(ctx,timestamp)?;\n",caller,'eq'),("\nOk(())\n}\nuse crate::legacy_sell","\n\n}\nuse crate::legacy_sell",'all'),("",helper,'eof')]
    open(f'{OUT}/spec/{name}.py','w').write('REPS='+repr(reps)+'\n')
