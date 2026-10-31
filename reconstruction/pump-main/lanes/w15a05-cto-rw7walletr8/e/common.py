RW7=('if coin_present&do_coin{','if do_coin{')
DC='let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;'
DCOL='let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);'
ATA='if !collection_native||coin_present{'
COINCPI_HEAD='  if coin_present&do_coin{\n  crate::pump_amm::cpi::collect_coin_creator_fee('
COINCPI_TAIL='program:a.pump_amm.to_account_info()}))?;}\n }}Ok(())}'
TAIL=('program:a.pump_amm.to_account_info()}))?;}\n }}Ok(())}',)
COLH='  if do_collect{\n    let event_signers'
def S1(r7):
    g='do_coin' if r7 else 'coin_present&do_coin'
    return [(COINCPI_HEAD,'  if '+g+'{coin_cpi(a)?;}fn coin_cpi(a:&AdminCto)->Result<()>{\n  crate::pump_amm::cpi::collect_coin_creator_fee('),(TAIL[0],'program:a.pump_amm.to_account_info()}))?;Ok(())}\n }}Ok(())}')]
def S2(r7):
    e=[(COLH,'  pay(ctx,do_collect,coin_present,do_coin)?;fn pay(ctx:&Context<AdminCto>,do_collect:bool,coin_present:bool,do_coin:bool)->Result<()>{let a=&ctx.accounts;if do_collect{\n    let event_signers'),(TAIL[0],'program:a.pump_amm.to_account_info()}))?;}Ok(())}\n }}Ok(())}')]
    if r7: e.append(RW7)
    return e
def S2b(r7):
    # only do_coin passed, coin_present folded in
    e=[(COLH,'  pay(ctx,do_collect,coin_present&do_coin)?;fn pay(ctx:&Context<AdminCto>,do_collect:bool,do_coin:bool)->Result<()>{let a=&ctx.accounts;if do_collect{\n    let event_signers'),(TAIL[0],'program:a.pump_amm.to_account_info()}))?;}Ok(())}\n }}Ok(())}'),RW7]
    return e
def S4(r7):
    e=[(DC,'let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;let flags=(do_collect,do_coin);'),('  if do_collect{\n','  if flags.0{\n'),(COINCPI_HEAD,'  if '+('flags.1' if r7 else 'coin_present&flags.1')+'{\n  crate::pump_amm::cpi::collect_coin_creator_fee(')]
    return e
def S6(r7):
    e=[('let coin_present=!a.coin_creator_vault_ata.data_is_empty();','let coin_present=!a.coin_creator_vault_ata.data_is_empty();let need_ata=!collection_native||coin_present;'),(ATA,'if need_ata{')]
    if r7: e.append(RW7)
    return e
def S7(r7):
    e=[(DC,'let do_coin=if coin_present{Some(!token_frozen(a.coin_creator_vault_ata.as_ref())?)}else{None};'),(ATA,'if !collection_native||do_coin.is_some(){'),(COINCPI_HEAD,'  if do_coin==Some(true){\n  crate::pump_amm::cpi::collect_coin_creator_fee(')]
    return e
