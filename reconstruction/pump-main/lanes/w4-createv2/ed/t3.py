import os
BLOCK=''' let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;
 let virtual_quote_reserves=if quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};
 let bonding_curve:&mut trade_types::BondingCurve=&mut ctx.accounts.bonding_curve;
 bonding_curve.creator=creator;
 bonding_curve.initial_virtual_quote_reserves=virtual_quote_reserves;
 bonding_curve.virtual_token_reserves=global.initial_virtual_token_reserves;
 bonding_curve.virtual_quote_reserves=virtual_quote_reserves;
 bonding_curve.real_token_reserves=global.initial_real_token_reserves;
 bonding_curve.real_quote_reserves=0;
 bonding_curve.token_total_supply=global.token_total_supply;
 bonding_curve.is_mayhem_mode=is_mayhem_mode;
 bonding_curve.is_cashback_coin=false;
 bonding_curve.quote_mint=quote_mint;
 bonding_curve.creator_fee_bps=fee;
 bonding_curve.can_edit_creator_fee=false;
 bonding_curve.is_holder_reward=is_holder_reward.0;
 bonding_curve.depth=depth;
 bonding_curve.post_complete_base_out=0;
 bonding_curve.post_complete_quote_in=0;
'''
CR=os.environ.get('CR','val')
call=' init_curve(&mut ctx.accounts.bonding_curve,global,%s,quote_mint,reserves,depth,fee,is_mayhem_mode,is_holder_reward.0);\n'%('creator' if CR=='val' else '&creator')
EDITS=[(BLOCK, call+'\n'*(BLOCK.count('\n')-1))]
body=BLOCK.replace(' let bonding_curve:&mut trade_types::BondingCurve=&mut ctx.accounts.bonding_curve;\n','').replace('is_holder_reward.0','is_holder_reward')
if CR!='val': body=body.replace('bonding_curve.creator=creator;','bonding_curve.creator=*creator;')
APPEND='fn init_curve(bonding_curve:&mut trade_types::BondingCurve,global:&Global,creator:%s,quote_mint:Pubkey,reserves:Option<u64>,depth:u8,fee:u64,is_mayhem_mode:bool,is_holder_reward:bool){\n'%('Pubkey' if CR=='val' else '&Pubkey')+body+'}\n'
