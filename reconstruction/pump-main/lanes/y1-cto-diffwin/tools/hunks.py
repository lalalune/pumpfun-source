#!/usr/bin/env python3
"""Apply named hunks to admin_cto.rs: hunks.py <base file> <out file> NAME..."""
import sys
H = {
 'A_valref': [
  ("holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{", "holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"),
  ("return Err(error!(PumpError::CtoNewCreatorNotAllowed));}holder_key}else{", "return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"),
  ("if t==holder_key||t==sharing{", "if t==*holder_key||t==*sharing{"),
  ("validate(&st,holder,fee,new,holder_key,a.sharing_config.key())", "validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())"),
 ],
 'B_tcf_order': [
  ("TransferCreatorFeesToPumpV2{payer:a.admin_set_creator_authority.to_account_info(),quote_mint:a.quote_mint.to_account_info(),token_program:a.quote_token_program.to_account_info(),system_program:a.system_program.to_account_info(),",
   "TransferCreatorFeesToPumpV2{system_program:a.system_program.to_account_info(),quote_mint:a.quote_mint.to_account_info(),token_program:a.quote_token_program.to_account_info(),payer:a.admin_set_creator_authority.to_account_info(),"),
 ],
 'C_ws_sharing': [
  ("admin_cto_sharing_config(CpiContext::new_with_signer(", "admin_cto_sharing_config(CpiContext::new("),
  ("program:a.pump_fees.to_account_info()},signer_seeds),val)?;", "program:a.pump_fees.to_account_info()}).with_signer(signer_seeds),val)?;"),
 ],
 'D_ws_pool': [
  ("admin_cto_pool(CpiContext::new_with_signer(", "admin_cto_pool(CpiContext::new("),
  ("program:a.pump_amm.to_account_info()},signer_seeds),target,holder,fee)?;", "program:a.pump_amm.to_account_info()}).with_signer(signer_seeds),target,holder,fee)?;"),
 ],
 'E_ql_first': [
  ("let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);",
   "let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();"),
 ],
 'F_su_tree': [
  ("let sharing_update=if shared{Some(if holder{None}else{new})}else{None};let collect_old=sharing_update.is_none()&&!st.holder_reward&&st.creator!=Pubkey::default();if shared&&!holder{target=st.creator;}",
   "let (sharing_update,collect_old)=if shared{if holder{(Some(None),false)}else{target=st.creator;(Some(new),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};"),
 ],
 'G_old_bump': [
  ("let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds", "let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];let vaultseeds"),
 ],
 'H_wallet_flags': [
  ("""  let coin_present=!a.coin_creator_vault_ata.data_is_empty();let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();
  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;
  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;""",
   """  let coin_present=!a.coin_creator_vault_ata.data_is_empty();
  let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);
  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;"""),
  ("  if collection_native||(source_present&&!source_frozen){", "  if do_collect{"),
  ("  if coin_present&&!coin_frozen{", "  if do_coin{"),
 ],
}
def main():
    src, out, *names = sys.argv[1:]
    s = open(src).read()
    for n in names:
        if n.startswith('g:'):
            sys.path.insert(0, __import__('os').path.dirname(__file__)); import genes1
            pairs = genes1.GENES[n[2:]]
        elif n not in H:
            extra = __import__('json').load(open(n))  # json file of [[old,new],...]
            pairs = extra
        else:
            pairs = H[n]
        for o, nw in pairs:
            c = s.count(o)
            if c != 1: sys.exit(f'{n}: count {c} for {o[:80]!r}')
            s = s.replace(o, nw)
    open(out, 'w').write(s)
main()
