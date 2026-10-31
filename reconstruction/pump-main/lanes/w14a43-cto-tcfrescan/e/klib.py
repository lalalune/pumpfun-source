K={
'nB':[("a.current_creator.is_writable==false","!a.current_creator.is_writable")],
'nC':[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let nf=a.bonding_curve.creator_fee_bps;let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"),("new_creator_fee_bps:a.bonding_curve.creator_fee_bps,","new_creator_fee_bps:nf,")],
'nA':[("lamports:x.lamports.clone(),data:a.pump_amm.data.clone(),","lamports:x.lamports.clone(),data:x.data.clone(),")],
'sh':[(" match sharing_update{Some(val)=>{\n"," if let Some(val)=sharing_update{{\n"),("signer_seeds),val)?;\n\n }None=>{}}\n","signer_seeds),val)?;\n\n }}\n")],
'tp':[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool_updated=a.pool.data_len()!=0 && a.pool.owner==&AMM;")],
'ev':[("is_holder_reward:holder,is_cashback_coin","is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin")],
}
K['x12d']=[("AccountInfo{key:x.key,lamports:x.lamports.clone(),owner:x.owner,data:x.data.clone(),rent_epoch","AccountInfo{key:x.key,lamports:x.lamports.clone(),owner:x.owner,data:a.creator_vault_quote_token_account.data.clone(),rent_epoch")]
K['vad']=[("coin_creator:a.current_creator.to_account_info(),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),","coin_creator:a.current_creator.to_account_info(),coin_creator_vault_authority:{let x:&AccountInfo=a.coin_creator_vault_authority.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:a.coin_creator_vault_authority.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},")]
K['spx']=[("system_program:a.system_program.to_account_info(),associated_token_program:a.associated_token_program.to_account_info(),coin_creator:","system_program:{let x:&AccountInfo=a.system_program.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:a.system_program.executable}},associated_token_program:a.associated_token_program.to_account_info(),coin_creator:")]
import os,json
K.update({k:[tuple(e) for e in v] for k,v in json.load(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a43-cto-tcfrescan/e/knobs_ok.json')).items()})
EDITS=[]
for n in os.environ['KN'].split('+'): EDITS+=K[n]
