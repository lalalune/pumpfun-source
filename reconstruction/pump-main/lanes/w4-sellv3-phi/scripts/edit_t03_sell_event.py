import sys
p=sys.argv[1]+'/src/trade_v3.rs'; s=open(p).read()
a='let event=crate::multi_hop_curve::trade_event(&a.bonding_curve,&a.global,&a.user_volume_accumulator,&a.user.key(),&a.base_mint.key(),false,amount,quote,&fees,'
assert s.count(a)==1
s=s.replace(a,'let event=sell_event(&a.bonding_curve,&a.global,&a.user_volume_accumulator,&a.user.key(),&a.base_mint.key(),amount,quote,fees,')
i=s.index(a[:0]+'let event=sell_event('); j=s.index('\n',i); line=s[i:j]
assert line.endswith('Clock::get()?.unix_timestamp);'), line
s=s.replace(line, line.replace(',"sell",Clock::get()?.unix_timestamp);',',Clock::get()?.unix_timestamp);'))
b='fn quote_is_native(curve:&BondingCurve)->bool{curve.quote_mint==Pubkey::default()}'
assert s.count(b)==1
s=s.replace(b,b+'  fn sell_event(curve:&BondingCurve,global:&Global,volume:&crate::UserVolumeAccumulator,user:&Pubkey,mint:&Pubkey,amount:u64,quote:u64,fees:TradeFees,buyback_fee:u64,quote_transfer_fee:u64,timestamp:i64)->TradeEvent{crate::multi_hop_curve::trade_event(curve,global,volume,user,mint,false,amount,quote,&fees,buyback_fee,quote_transfer_fee,"sell",timestamp)}')
open(p,'w').write(s)
